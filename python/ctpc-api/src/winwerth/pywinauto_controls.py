"""
PyWinAuto-based UI control automation (buttons, checkboxes).

Ported from the original AutoPilot PyWinAuto_era branch.
Provides ``ButtonPresser``, ``CheckboxController``, and a unified
``PyWinAutoBackend`` facade that auto-detects pywinauto availability
and falls back to mock mode on non-Windows platforms.

Thread-safe: all mutable state is guarded by a ``threading.Lock``.
"""

from __future__ import annotations

import logging
import threading
from enum import IntEnum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("ctpc-api.pywinauto_controls")

# ---------------------------------------------------------------------------
# Detect pywinauto availability
# ---------------------------------------------------------------------------

_PYWINAUTO_AVAILABLE = False

try:
    from pywinauto.findwindows import ElementNotFoundError  # type: ignore[import-untyped]

    _PYWINAUTO_AVAILABLE = True
except ImportError:
    logger.info("pywinauto not available — PyWinAutoBackend will use mock mode")


class ToggleState(IntEnum):
    """UIA toggle states."""

    UNCHECKED = 0
    CHECKED = 1
    INDETERMINATE = 2


# ---------------------------------------------------------------------------
# ButtonPresser
# ---------------------------------------------------------------------------


class ButtonPresser:
    """Press buttons inside a pywinauto dialog by automation-id, index, or text.

    Ported from ``source/libs/pywinauto/button/button.py``.

    All methods accept a *dlg* argument — a pywinauto ``WindowSpecification``
    (or compatible wrapper) that has a ``.descendants()`` method.
    In mock mode *dlg* is ignored and the methods always return ``True``.
    """

    def __init__(self, *, mock_mode: bool = False) -> None:
        self._mock = mock_mode or not _PYWINAUTO_AVAILABLE
        self._lock = threading.Lock()
        if self._mock:
            logger.info("ButtonPresser: mock mode")

    # -- unified entry point ------------------------------------------------

    def press(
        self,
        dlg: Any,
        *,
        automation_id: Optional[str] = None,
        text: Optional[str] = None,
        index: Optional[int] = None,
    ) -> bool:
        """Press a button using whichever identifier is provided.

        Exactly one of *automation_id*, *text*, or *index* should be given.
        Returns ``True`` on success, ``False`` otherwise.
        """
        if automation_id is not None:
            return self.press_by_automation_id(dlg, automation_id)
        if index is not None:
            return self.press_by_index(dlg, index)
        if text is not None:
            return self.press_by_text(dlg, text)

        logger.error("ButtonPresser.press(): no identifier provided (automation_id, text, or index)")
        return False

    # -- by automation id ---------------------------------------------------

    def press_by_automation_id(self, dlg: Any, automation_id: str) -> bool:
        """Find and click a button matching *automation_id*."""
        with self._lock:
            if self._mock:
                logger.debug("[mock] press_by_automation_id('%s')", automation_id)
                return True

            logger.info("Searching for button with automation_id='%s'", automation_id)
            try:
                buttons = dlg.descendants(control_type="Button")
                for i, btn in enumerate(buttons):
                    btn_auto_id = getattr(btn.element_info, "automation_id", None)
                    if btn_auto_id == automation_id:
                        logger.info("Button #%d with automation_id='%s' found — clicking", i, automation_id)
                        btn.click_input()
                        return True

                logger.warning("No button with automation_id='%s' found", automation_id)
            except Exception:
                logger.exception("Error searching buttons by automation_id='%s'", automation_id)

            return False

    # -- by index -----------------------------------------------------------

    def press_by_index(self, dlg: Any, index: int) -> bool:
        """Click the button at position *index* in the dialog's button list."""
        with self._lock:
            if self._mock:
                logger.debug("[mock] press_by_index(%d)", index)
                return True

            logger.info("Pressing button at index %d", index)
            try:
                buttons = dlg.descendants(control_type="Button")
                if 0 <= index < len(buttons):
                    logger.info("Button #%d found — clicking", index)
                    buttons[index].click_input()
                    return True
                else:
                    logger.error(
                        "Index %d out of range (total buttons: %d)", index, len(buttons)
                    )
            except Exception:
                logger.exception("Error accessing button at index %d", index)

            return False

    # -- by visible text ----------------------------------------------------

    def press_by_text(self, dlg: Any, text: str) -> bool:
        """Find and click a button whose ``name`` matches *text*."""
        with self._lock:
            if self._mock:
                logger.debug("[mock] press_by_text('%s')", text)
                return True

            logger.info("Searching for button with text='%s'", text)
            try:
                buttons = dlg.descendants(control_type="Button")
                for i, btn in enumerate(buttons):
                    btn_name = getattr(btn.element_info, "name", None)
                    if btn_name == text:
                        logger.info("Button #%d with text='%s' found — clicking", i, text)
                        btn.click_input()
                        return True

                logger.warning("No button with text='%s' found", text)
            except Exception:
                logger.exception("Error searching buttons by text='%s'", text)

            return False

    # -- discovery helper ---------------------------------------------------

    def list_buttons(self, dlg: Any) -> List[Dict[str, Any]]:
        """Return metadata for every button in the dialog (useful for debugging).

        Each dict contains ``index``, ``automation_id``, and ``name``.
        """
        if self._mock:
            return []

        result: List[Dict[str, Any]] = []
        try:
            buttons = dlg.descendants(control_type="Button")
            for i, btn in enumerate(buttons):
                result.append({
                    "index": i,
                    "automation_id": getattr(btn.element_info, "automation_id", ""),
                    "name": getattr(btn.element_info, "name", ""),
                })
        except Exception:
            logger.exception("Error listing buttons")
        return result


# ---------------------------------------------------------------------------
# CheckboxController
# ---------------------------------------------------------------------------


class CheckboxController:
    """Read and set checkbox state via UIA automation-id.

    Ported from ``source/libs/pywinauto/checkbox/checkbox_h.py``.

    Well-known automation IDs (from the original ``checkbox_e.py``):

    * ``"2779"`` — *Schnelles Livebild* checkbox
    """

    # Well-known checkbox automation IDs from the original element definitions
    LIVEBILD_ID: str = "2779"

    def __init__(self, *, mock_mode: bool = False) -> None:
        self._mock = mock_mode or not _PYWINAUTO_AVAILABLE
        self._lock = threading.Lock()
        self._mock_states: Dict[str, bool] = {}  # automation_id -> checked
        if self._mock:
            logger.info("CheckboxController: mock mode")

    # -- state reading ------------------------------------------------------

    def get_state(self, dlg: Any, automation_id: str) -> Optional[bool]:
        """Return checkbox state: ``True`` (checked), ``False`` (unchecked),
        or ``None`` if the checkbox was not found.
        """
        with self._lock:
            if self._mock:
                return self._mock_states.get(automation_id, False)

            try:
                checkbox = dlg.child_window(auto_id=automation_id, control_type="CheckBox")
                state = checkbox.get_toggle_state()
                return state == ToggleState.CHECKED
            except Exception as exc:
                if _PYWINAUTO_AVAILABLE:
                    from pywinauto.findwindows import ElementNotFoundError as _ENF  # type: ignore[import-untyped]

                    if isinstance(exc, _ENF):
                        logger.warning("Checkbox with automation_id='%s' not found", automation_id)
                        return None
                logger.exception("Error reading checkbox state (automation_id='%s')", automation_id)
                return None

    def is_checked(self, dlg: Any, automation_id: str) -> bool:
        """Convenience: returns ``True`` only when checkbox is definitively checked."""
        return self.get_state(dlg, automation_id) is True

    # -- state mutation -----------------------------------------------------

    def set_state(self, dlg: Any, automation_id: str, *, checked: bool) -> bool:
        """Set checkbox to *checked* state.  Toggles only if current state differs.

        Returns ``True`` on success, ``False`` on failure.
        """
        with self._lock:
            if self._mock:
                logger.debug("[mock] set_state('%s', checked=%s)", automation_id, checked)
                self._mock_states[automation_id] = checked
                return True

            try:
                checkbox = dlg.child_window(auto_id=automation_id, control_type="CheckBox")
                current = checkbox.get_toggle_state() == ToggleState.CHECKED

                if current == checked:
                    logger.info("Checkbox '%s' already %s — no change needed",
                                automation_id, "checked" if checked else "unchecked")
                    return True

                checkbox.toggle()
                logger.info("Checkbox '%s' toggled to %s",
                            automation_id, "checked" if checked else "unchecked")
                return True
            except Exception as exc:
                if _PYWINAUTO_AVAILABLE:
                    from pywinauto.findwindows import ElementNotFoundError as _ENF  # type: ignore[import-untyped]

                    if isinstance(exc, _ENF):
                        logger.warning("Checkbox with automation_id='%s' not found", automation_id)
                        return False
                logger.exception("Error setting checkbox state (automation_id='%s')", automation_id)
                return False

    # -- Schnelles Livebild convenience methods (original checkbox.py) ------

    def is_livebild_checked(self, dlg: Any) -> Optional[bool]:
        """Check whether the *Schnelles Livebild* checkbox is active."""
        return self.get_state(dlg, self.LIVEBILD_ID)

    def ensure_livebild_checked(self, dlg: Any) -> bool:
        """Enable *Schnelles Livebild* if not already checked.

        Returns ``True`` on success (or already checked), ``False`` on failure.
        """
        current = self.is_livebild_checked(dlg)
        if current is None:
            logger.warning("LiveBild checkbox not found")
            return False
        if current:
            logger.info("Schnelles Livebild already checked")
            return True
        return self.set_state(dlg, self.LIVEBILD_ID, checked=True)

    # -- discovery helper ---------------------------------------------------

    def list_checkboxes(self, dlg: Any) -> List[Dict[str, Any]]:
        """Return metadata for every checkbox in the dialog."""
        if self._mock:
            return []

        result: List[Dict[str, Any]] = []
        try:
            checkboxes = dlg.descendants(control_type="CheckBox")
            for i, cb in enumerate(checkboxes):
                state = cb.get_toggle_state()
                result.append({
                    "index": i,
                    "automation_id": getattr(cb.element_info, "automation_id", ""),
                    "name": getattr(cb.element_info, "name", ""),
                    "checked": state == ToggleState.CHECKED,
                    "state": ToggleState(state).name if state in (0, 1, 2) else "UNKNOWN",
                })
        except Exception:
            logger.exception("Error listing checkboxes")
        return result


# ---------------------------------------------------------------------------
# PyWinAutoBackend — unified facade
# ---------------------------------------------------------------------------


class PyWinAutoBackend:
    """Unified backend wrapping both :class:`ButtonPresser` and
    :class:`CheckboxController`.

    Auto-detects pywinauto availability.  When unavailable (e.g. on macOS/Linux),
    all operations silently succeed in mock mode.

    Usage::

        backend = PyWinAutoBackend()
        print(backend.is_available)   # False on macOS
        print(backend.mock_mode)      # True on macOS

        # Button operations
        backend.buttons.press(dlg, automation_id="1234")
        backend.buttons.press(dlg, text="OK")
        backend.buttons.press(dlg, index=0)

        # Checkbox operations
        backend.checkboxes.set_state(dlg, "2779", checked=True)
        backend.checkboxes.ensure_livebild_checked(dlg)
    """

    def __init__(self, *, force_mock: bool = False) -> None:
        self._mock = force_mock or not _PYWINAUTO_AVAILABLE
        self.buttons = ButtonPresser(mock_mode=self._mock)
        self.checkboxes = CheckboxController(mock_mode=self._mock)

        if self._mock:
            logger.info(
                "PyWinAutoBackend: mock mode (pywinauto %s)",
                "not installed" if not _PYWINAUTO_AVAILABLE else "force-disabled",
            )
        else:
            logger.info("PyWinAutoBackend: LIVE mode (pywinauto available)")

    @property
    def is_available(self) -> bool:
        """Whether pywinauto is installed and the backend is in live mode."""
        return not self._mock

    @property
    def mock_mode(self) -> bool:
        """Whether the backend is operating in mock mode."""
        return self._mock

    def __repr__(self) -> str:
        mode = "MOCK" if self._mock else "LIVE"
        return f"<PyWinAutoBackend mode={mode}>"
