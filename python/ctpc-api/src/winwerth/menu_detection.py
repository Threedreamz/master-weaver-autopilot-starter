"""
Punkte-Menu detection and tab navigation for WinWerth.

Ported from the legacy ``interface_era`` branch (``punkte_Menu.py``,
``punkteMenu_h.py``, ``punkte_Menu_.py``).

Provides a high-level ``MenuNavigator`` class that:
- Detects which of the 4 Punkte-Menu tabs is currently active
  (Messfleck, CT, Hand, Rechnen)
- Switches between tabs with state validation
- Queries button availability by text or automation ID
- Falls back to mock mode on non-Windows platforms

Thread-safe: all mutable state is guarded by ``threading.Lock``.
"""

from __future__ import annotations

import logging
import platform
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ctpc-api.menu_detection")


# ---------------------------------------------------------------------------
# Tab definitions
# ---------------------------------------------------------------------------

class Tab(str, Enum):
    """The four Punkte-Menu tabs in WinWerth."""
    MESSFLECK = "Messfleck"
    CT = "CT"
    HAND = "Hand"
    RECHNEN = "Rechnen"


@dataclass(frozen=True)
class TabDetection:
    """How to detect whether a given tab is currently active."""
    automation_id: str
    text: str
    inverse: bool = False  # True → tab is active when the marker is ABSENT


@dataclass(frozen=True)
class TabButton:
    """Index of the navigation button to click for a target tab,
    given the *current* active tab.  Button indices shift depending on
    which tab is active (the legacy code encoded this explicitly)."""
    base_index: int
    rechnen_offset: int = 2  # Extra offset when coming from Rechnen tab


# Complete tab metadata derived from the original ``punkte_Menu_`` element
# definitions and ``punkte_Menu.btnIndexByTab``.
TAB_DETECTION: Dict[Tab, TabDetection] = {
    Tab.MESSFLECK: TabDetection(automation_id="", text="Messflecksensor"),
    Tab.CT:        TabDetection(automation_id="", text="CT-Sensor"),
    Tab.HAND:      TabDetection(automation_id="UpButton", text="Bildlauf nach links", inverse=True),
    Tab.RECHNEN:   TabDetection(automation_id="32807", text="1. Ergebnis"),
}

TAB_BUTTONS: Dict[Tab, TabButton] = {
    Tab.MESSFLECK: TabButton(base_index=76),
    Tab.CT:        TabButton(base_index=77),
    Tab.HAND:      TabButton(base_index=78),
    Tab.RECHNEN:   TabButton(base_index=79),
}


# ---------------------------------------------------------------------------
# Low-level button helpers (replaces button_h + punkteMenu_h)
# ---------------------------------------------------------------------------

def _get_all_buttons(dlg_descendants: Any) -> List[Dict[str, str]]:
    """Extract text and automation_id from a list of UIA button wrappers.

    Args:
        dlg_descendants: Result of ``dlg.descendants(control_type="Button")``.

    Returns:
        List of dicts with keys ``text`` and ``automation_id``.
    """
    buttons: List[Dict[str, str]] = []
    try:
        for btn in dlg_descendants:
            text = getattr(btn.element_info, "name", "")
            auto_id = getattr(btn.element_info, "automation_id", "")
            if text or auto_id:
                buttons.append({"text": text, "automation_id": auto_id})
    except Exception as exc:
        logger.error("_get_all_buttons failed: %s", exc)
    return buttons


def _is_button_available_by_text(text: str, buttons: List[Dict[str, str]]) -> bool:
    """Check whether any button matches *text* exactly."""
    return any(b["text"] == text for b in buttons)


def _is_button_available_by_id(automation_id: str, buttons: List[Dict[str, str]]) -> bool:
    """Check whether any button matches *automation_id* exactly."""
    return any(b["automation_id"] == automation_id for b in buttons)


# ---------------------------------------------------------------------------
# MenuNavigator
# ---------------------------------------------------------------------------

class MenuNavigator:
    """High-level navigator for the WinWerth Punkte-Menu.

    Args:
        win_api: A ``WindowApi`` instance (from ``win_api.create_window_api``).
            Used only in live mode to obtain the WinWerth dialog handle.
        window_title: Title substring for the main WinWerth window.
        force_mock: Force mock mode regardless of platform.
    """

    def __init__(
        self,
        win_api: Any = None,
        window_title: str = "WinWerth",
        force_mock: bool = False,
    ) -> None:
        self._lock = threading.Lock()
        self._win_api = win_api
        self._window_title = window_title

        # Determine mock mode
        if force_mock:
            self.mock_mode = True
            logger.info("MenuNavigator: forced mock mode")
        elif platform.system() != "Windows":
            self.mock_mode = True
            logger.info(
                "MenuNavigator: non-Windows platform (%s) — mock mode",
                platform.system(),
            )
        else:
            self.mock_mode = False
            logger.info("MenuNavigator: live mode")

        # Mock state
        self._mock_current_tab: Tab = Tab.MESSFLECK
        self._mock_buttons: List[str] = [
            "Messflecksensor", "CT-Sensor", "Bildlauf nach links",
            "1. Ergebnis", "Start", "Stop", "Messung",
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_dialog(self) -> Any:
        """Obtain the WinWerth dialog handle via pywinauto.

        Returns:
            The dialog wrapper, or None if not found.
        """
        if self.mock_mode:
            return None
        try:
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            windows = desktop.windows(title_re=f".*{self._window_title}.*")
            if windows:
                return windows[0]
            logger.warning("MenuNavigator: WinWerth window not found")
        except Exception as exc:
            logger.error("MenuNavigator._get_dialog failed: %s", exc)
        return None

    def _get_button_descriptors(self, dlg: Any) -> List[Dict[str, str]]:
        """Get all button descriptors from the dialog."""
        if dlg is None:
            return []
        try:
            descendants = dlg.descendants(control_type="Button")
            return _get_all_buttons(descendants)
        except Exception as exc:
            logger.error("_get_button_descriptors failed: %s", exc)
            return []

    def _detect_tab_live(self, dlg: Any) -> Optional[Tab]:
        """Detect current tab by inspecting dialog buttons."""
        buttons = self._get_button_descriptors(dlg)
        if not buttons:
            logger.warning("No buttons found in dialog — cannot detect tab")
            return None

        # Messfleck: button with text "Messflecksensor" exists
        det = TAB_DETECTION[Tab.MESSFLECK]
        if _is_button_available_by_text(det.text, buttons):
            return Tab.MESSFLECK

        # CT: button with text "CT-Sensor" exists
        det = TAB_DETECTION[Tab.CT]
        if _is_button_available_by_text(det.text, buttons):
            return Tab.CT

        # Hand: detected by ABSENCE of "UpButton" automation_id (inverse logic)
        det = TAB_DETECTION[Tab.HAND]
        if not _is_button_available_by_id(det.automation_id, buttons):
            return Tab.HAND

        # Rechnen: button with automation_id "32807" exists
        det = TAB_DETECTION[Tab.RECHNEN]
        if _is_button_available_by_id(det.automation_id, buttons):
            return Tab.RECHNEN

        return None

    def _click_by_index(self, index: int, dlg: Any) -> bool:
        """Click a button by its index in the dialog's button list."""
        try:
            descendants = dlg.descendants(control_type="Button")
            if 0 <= index < len(descendants):
                logger.info("Clicking button at index %d", index)
                descendants[index].click_input()
                return True
            else:
                logger.error(
                    "Button index %d out of range (total: %d)",
                    index, len(descendants),
                )
        except Exception as exc:
            logger.error("_click_by_index failed: %s", exc)
        return False

    def _compute_button_index(self, target: Tab, current: Optional[Tab]) -> int:
        """Compute the correct button index for *target* given *current* tab.

        The legacy code adds +2 to all indices when the current tab is Rechnen,
        because the Rechnen tab inserts extra buttons that shift the indices.
        """
        tab_btn = TAB_BUTTONS[target]
        index = tab_btn.base_index
        if current == Tab.RECHNEN:
            index += tab_btn.rechnen_offset
        return index

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_tab(self) -> Optional[str]:
        """Detect which Punkte-Menu tab is currently active.

        Returns:
            Tab name (``"Messfleck"``, ``"CT"``, ``"Hand"``, ``"Rechnen"``),
            or ``None`` if detection fails.
        """
        with self._lock:
            if self.mock_mode:
                logger.debug("[mock] Current tab: %s", self._mock_current_tab.value)
                return self._mock_current_tab.value

            dlg = self._get_dialog()
            if dlg is None:
                return None
            tab = self._detect_tab_live(dlg)
            return tab.value if tab else None

    def switch_to_tab(self, tab_name: str) -> bool:
        """Switch to the given tab by name.

        Detects the current tab first, skips if already there,
        then clicks the correct navigation button.

        Args:
            tab_name: One of ``"Messfleck"``, ``"CT"``, ``"Hand"``, ``"Rechnen"``.

        Returns:
            True if the tab switch succeeded (or was already active).
        """
        # Resolve tab_name to enum
        try:
            target = Tab(tab_name)
        except ValueError:
            logger.error("Unknown tab name: '%s'", tab_name)
            return False

        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Switching to tab: %s", target.value)
                time.sleep(random.uniform(0.1, 0.3))
                self._mock_current_tab = target
                return True

            dlg = self._get_dialog()
            if dlg is None:
                logger.error("Cannot switch tab — dialog not found")
                return False

            current = self._detect_tab_live(dlg)
            if current == target:
                logger.info("Already on tab '%s' — no switch needed", target.value)
                return True

            index = self._compute_button_index(target, current)
            logger.info(
                "Switching tab: %s -> %s (button index %d)",
                current.value if current else "unknown",
                target.value,
                index,
            )

            ok = self._click_by_index(index, dlg)
            if not ok:
                return False

            # Validate the switch
            time.sleep(0.3)
            new_tab = self._detect_tab_live(dlg)
            if new_tab != target:
                logger.warning(
                    "Tab switch validation failed — expected '%s', got '%s'",
                    target.value,
                    new_tab.value if new_tab else "None",
                )
                return False

            logger.info("Tab switch to '%s' confirmed", target.value)
            return True

    def is_button_available(self, button_name: str) -> bool:
        """Check whether a button with the given text is present.

        Args:
            button_name: The button text to search for.

        Returns:
            True if a button with matching text exists in the current dialog.
        """
        if self.mock_mode:
            return button_name in self._mock_buttons

        dlg = self._get_dialog()
        if dlg is None:
            return False
        buttons = self._get_button_descriptors(dlg)
        return _is_button_available_by_text(button_name, buttons)

    def is_button_available_by_id(self, automation_id: str) -> bool:
        """Check whether a button with the given automation ID is present.

        Args:
            automation_id: The UIA automation ID to search for.

        Returns:
            True if a button with matching automation_id exists.
        """
        if self.mock_mode:
            # In mock mode, only a few known IDs are "available"
            mock_ids = {"32807", "UpButton"}
            return automation_id in mock_ids

        dlg = self._get_dialog()
        if dlg is None:
            return False
        buttons = self._get_button_descriptors(dlg)
        return _is_button_available_by_id(automation_id, buttons)

    def click_button(self, button_name: str) -> bool:
        """Click a button by its text label.

        Searches all buttons in the dialog for a matching text and clicks it.

        Args:
            button_name: The visible text of the button to click.

        Returns:
            True if the button was found and clicked.
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Clicking button: %s", button_name)
                time.sleep(random.uniform(0.05, 0.15))
                return button_name in self._mock_buttons

            dlg = self._get_dialog()
            if dlg is None:
                logger.error("Cannot click button — dialog not found")
                return False

            try:
                descendants = dlg.descendants(control_type="Button")
                for btn in descendants:
                    text = getattr(btn.element_info, "name", "")
                    if text == button_name:
                        logger.info("Found button '%s', clicking", button_name)
                        btn.click_input()
                        return True
                logger.warning("Button '%s' not found in dialog", button_name)
            except Exception as exc:
                logger.error("click_button '%s' failed: %s", button_name, exc)
            return False

    def get_available_buttons(self) -> List[str]:
        """Return the text labels of all currently visible buttons.

        Returns:
            List of button text strings.
        """
        if self.mock_mode:
            return list(self._mock_buttons)

        dlg = self._get_dialog()
        if dlg is None:
            return []
        buttons = self._get_button_descriptors(dlg)
        return [b["text"] for b in buttons if b["text"]]

    def get_tab_names(self) -> List[str]:
        """Return the names of all four Punkte-Menu tabs."""
        return [tab.value for tab in Tab]

    def get_menu_state(self) -> Dict[str, Any]:
        """Return a summary of the current menu state.

        Useful for diagnostics and API responses.
        """
        current = self.get_current_tab()
        buttons = self.get_available_buttons()
        return {
            "current_tab": current,
            "available_tabs": self.get_tab_names(),
            "button_count": len(buttons),
            "mock_mode": self.mock_mode,
        }

    def __repr__(self) -> str:
        mode = "MOCK" if self.mock_mode else "LIVE"
        return f"<MenuNavigator mode={mode}>"
