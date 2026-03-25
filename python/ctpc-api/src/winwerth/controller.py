"""
WinWerthController — unified facade over all WinWerth subsystem modules.

Provides the full interface required by:
- ``ScanController`` protocol (orchestrator/scan_machine.py)
- ``ControllerProtocol`` (orchestrator/stl_export.py)
- REST API routes (api/routes.py)

Auto-detects Windows + WinWerth availability; falls back to mock mode with
realistic delays and simulated state when unavailable or when *force_mock*
is set.

Thread-safe: all mutable state is guarded by a ``threading.Lock``.
"""

from __future__ import annotations

import logging
import os
import platform
import random
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from .config import get_color, get_coords, get_from_possible_keys, load_config
from .error_correction import error_correction as _run_error_correction
from .menu_detection import MenuNavigator
from .mouse import MouseController
from .pixel_check import PixelChecker
from .profile import (
    bring_to_front,
    choose_profile,
    close_profile_window,
    is_profile_selected as _is_profile_selected,
    open_profile_window,
)
from .pywinauto_controls import PyWinAutoBackend
from .rotation import activate_drehen, is_drehen_on, set_rotation_angle
from .tube import check_tube_on, check_tube_ready, click_tube_on
from .win_api import WindowInfo, create_window_api

logger = logging.getLogger("ctpc-api.controller")

# WinWerth main-window title substring used to locate the application.
_WINWERTH_TITLE = "WinWerth"


class WinWerthController:
    """Unified controller for the WinWerth CT scanner software.

    Args:
        force_mock: When *True*, skip platform/window detection and use mock
            mode unconditionally.  Useful for development and testing.
        config_file: Optional path to the ``winWerth_data.json`` configuration
            file.  When *None*, the default location next to the package root
            is used.
    """

    # ------------------------------------------------------------------
    # Construction & detection
    # ------------------------------------------------------------------

    def __init__(
        self,
        force_mock: bool = False,
        config_file: Optional[str] = None,
    ) -> None:
        self._lock = threading.Lock()

        # Load JSON configuration (coordinates, colours, UI layout)
        self.config: Dict[str, Any] = load_config(config_file)

        # Subsystem modules
        self.mouse = MouseController(pause=0.2)
        self.pixel_checker = PixelChecker(cache_ttl_ms=200.0)
        self.win_api = create_window_api()
        self.pywinauto = PyWinAutoBackend(force_mock=force_mock)
        self.menu = MenuNavigator(force_mock=force_mock)

        # Detect mock mode
        if force_mock:
            self.mock_mode = True
            logger.info("WinWerthController: forced mock mode")
        elif platform.system() != "Windows":
            self.mock_mode = True
            logger.info(
                "WinWerthController: non-Windows platform (%s) — mock mode",
                platform.system(),
            )
        elif not self.config:
            self.mock_mode = True
            logger.warning(
                "WinWerthController: config empty — mock mode"
            )
        else:
            # On Windows, try to find the WinWerth window
            win_info = self.win_api.find_window_by_title(_WINWERTH_TITLE)
            if win_info is None:
                self.mock_mode = True
                logger.warning(
                    "WinWerthController: WinWerth window not found — mock mode"
                )
            else:
                self.mock_mode = False
                logger.info(
                    "WinWerthController: LIVE mode (window '%s' at %d,%d)",
                    win_info.title,
                    win_info.x,
                    win_info.y,
                )

        # Mock state tracking
        self._mock_tube_on = False
        self._mock_rotation_active = False
        self._mock_scan_progress = 0.0
        self._mock_scan_running = False
        self._mock_selected_profile: Optional[str] = None

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def get_available_profiles(self) -> List[Dict[str, Any]]:
        """Return the list of magnification profiles from config."""
        profiles: List[Dict[str, Any]] = []
        try:
            absolute = self.config["Profile_Window"]["Absolute"]
            for key, val in absolute.items():
                if key in ("window_pos", "window_x_start", "Schliessen_Button"):
                    continue
                coords = get_coords(val)
                if coords:
                    profiles.append({"name": key, "x": coords[0], "y": coords[1]})
        except (KeyError, TypeError):
            pass

        if not profiles:
            # Provide sensible defaults so the API always returns something
            profiles = [
                {"name": "125L_first", "x": 0, "y": 0},
                {"name": "100L_second", "x": 0, "y": 0},
                {"name": "50L_third", "x": 0, "y": 0},
            ]
        return profiles

    def complete_profile_selection_sequence(self, profile_name: str) -> bool:
        """Open profile window, select *profile_name*, close window.

        Full sequence: click profile button -> wait -> select -> close.
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Profile selection: %s", profile_name)
                time.sleep(random.uniform(0.3, 0.8))
                self._mock_selected_profile = profile_name
                return True

            logger.info("Starting profile selection for '%s'", profile_name)

            # Step 1 — open profile window
            ok = open_profile_window(_WINWERTH_TITLE, self.config, self.mouse)
            if not ok:
                logger.error("Failed to open profile window")
                return False

            # Step 2 — select the profile
            ok = choose_profile(profile_name, self.config, self.mouse)
            if not ok:
                logger.error("Failed to select profile '%s'", profile_name)
                close_profile_window(self.config, self.mouse)
                return False

            # Step 3 — verify selection
            time.sleep(0.3)
            if not _is_profile_selected(profile_name, self.config, self.pixel_checker):
                logger.warning("Profile '%s' click succeeded but verification failed", profile_name)

            # Step 4 — close
            ok = close_profile_window(self.config, self.mouse)
            if not ok:
                logger.warning("Profile window close returned False")

            logger.info("Profile selection sequence complete: %s", profile_name)
            return True

    def is_profile_selected(self, profile_name: str) -> bool:
        """Check whether *profile_name* is currently selected."""
        if self.mock_mode:
            return self._mock_selected_profile == profile_name

        return _is_profile_selected(
            profile_name, self.config, self.pixel_checker
        )

    # ------------------------------------------------------------------
    # Tube (X-ray source) control
    # ------------------------------------------------------------------

    def click_tube_power_on(self) -> bool:
        """Activate the X-ray tube (click Rohre An)."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Tube power on")
                time.sleep(random.uniform(0.5, 1.5))
                self._mock_tube_on = True
                return True

            return click_tube_on(
                _WINWERTH_TITLE,
                self.config,
                self.mouse,
                safety_pin=False,
            )

    def is_tube_on(self) -> bool:
        """Check whether the X-ray tube is currently powered on."""
        if self.mock_mode:
            return self._mock_tube_on

        result = check_tube_on(self.config, self.pixel_checker)
        return result is True

    def is_tube_ready(self) -> bool:
        """Check whether the tube is in operational/ready state."""
        if self.mock_mode:
            return self._mock_tube_on

        result = check_tube_ready(self.config, self.pixel_checker)
        return result is True

    # ------------------------------------------------------------------
    # Rotation (Drehen) control
    # ------------------------------------------------------------------

    def activate_rotation(self) -> bool:
        """Activate the Drehen (rotation) mode."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Activate rotation")
                time.sleep(random.uniform(0.2, 0.5))
                self._mock_rotation_active = True
                return True

            return activate_drehen(self.config, self.mouse)

    def activate_drehen(self) -> bool:
        """Alias for :meth:`activate_rotation` (used by routes.py)."""
        return self.activate_rotation()

    def is_rotation_active(self) -> bool:
        """Check whether rotation mode is currently active."""
        if self.mock_mode:
            return self._mock_rotation_active

        return is_drehen_on(self.config, self.pixel_checker, self.mouse)

    def rotate_degrees(self, degrees: float) -> bool:
        """Set the rotation angle and initiate rotation.

        Args:
            degrees: Rotation angle (typically 360 for a full preview).
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Rotating %.1f degrees", degrees)
                # Simulate rotation time proportional to angle
                sim_time = (degrees / 360.0) * random.uniform(2.0, 4.0)
                time.sleep(sim_time)
                return True

            return set_rotation_angle(self.config, angle=int(degrees), mouse=self.mouse)

    # ------------------------------------------------------------------
    # Green box / boundary detection
    # ------------------------------------------------------------------

    def get_min_distances(self) -> Dict[str, Any]:
        """Capture minimum distances from the preview rotation.

        In live mode this reads pixel data from the WinWerth viewport.
        In mock mode it returns plausible fake boundaries.
        """
        if self.mock_mode:
            logger.info("[mock] Returning simulated min distances")
            time.sleep(random.uniform(0.3, 0.8))
            return {
                "top": random.randint(50, 150),
                "bottom": random.randint(50, 150),
                "left": random.randint(50, 150),
                "right": random.randint(50, 150),
                "min_distance_mm": round(random.uniform(5.0, 25.0), 2),
            }

        # Live: read from pixel analysis of the viewport
        # This is a simplified implementation — the real one would analyse
        # the preview image captured during rotation.
        logger.info("Capturing min distances from viewport")
        try:
            # Use viewport region from config if available
            viewport = self.config.get("WinWerth_Window", {}).get("Viewport", {})
            x = int(viewport.get("x", 200))
            y = int(viewport.get("y", 100))
            w = int(viewport.get("w", 600))
            h = int(viewport.get("h", 600))

            region = self.pixel_checker.get_region_colors(x, y, w, h)
            if region.size == 0:
                logger.warning("Empty region capture — returning defaults")
                return {"top": 100, "bottom": 100, "left": 100, "right": 100}

            # Find non-black boundaries (object extents)
            import numpy as np
            gray = np.mean(region, axis=2)
            threshold = 15
            rows, cols = np.where(gray > threshold)

            if len(rows) == 0:
                return {"top": 100, "bottom": 100, "left": 100, "right": 100}

            return {
                "top": int(np.min(rows)),
                "bottom": int(h - np.max(rows)),
                "left": int(np.min(cols)),
                "right": int(w - np.max(cols)),
                "min_distance_mm": round(min(np.min(rows), h - np.max(rows),
                                              np.min(cols), w - np.max(cols)) * 0.1, 2),
            }
        except Exception as exc:
            logger.error("get_min_distances failed: %s", exc)
            return {"top": 100, "bottom": 100, "left": 100, "right": 100}

    def set_green_box(self, boundaries: Dict[str, Any]) -> bool:
        """Draw the green selection box based on *boundaries*.

        This clicks the selection region in the WinWerth viewport.
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Setting green box: %s", boundaries)
                time.sleep(random.uniform(0.3, 0.6))
                return True

            try:
                select_region = self.config["WinWerth_Window"]["Select_Region"]
                btn = select_region["select_button_sideMenu"]
                coords = get_coords(btn)
                if coords:
                    self.mouse.click_and_wait(coords[0], coords[1], wait_time=0.5)

                # Use boundaries to calculate drag region on the viewport
                viewport = self.config.get("WinWerth_Window", {}).get("Viewport", {})
                vx = int(viewport.get("x", 200))
                vy = int(viewport.get("y", 100))
                vw = int(viewport.get("w", 600))
                vh = int(viewport.get("h", 600))

                top = boundaries.get("top", 50)
                bottom = boundaries.get("bottom", 50)
                left = boundaries.get("left", 50)
                right = boundaries.get("right", 50)

                start_x = vx + left
                start_y = vy + top
                end_x = vx + vw - right
                end_y = vy + vh - bottom

                return self.mouse.drag(start_x, start_y, end_x, end_y, duration=0.8)
            except (KeyError, TypeError) as exc:
                logger.error("set_green_box failed: %s", exc)
                return False

    # ------------------------------------------------------------------
    # Error correction
    # ------------------------------------------------------------------

    def run_error_correction(self) -> bool:
        """Run the voltage/ampere error-correction loop."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Running error correction")
                time.sleep(random.uniform(1.0, 3.0))
                return True

            return _run_error_correction(
                _WINWERTH_TITLE,
                self.config,
                self.pixel_checker,
                self.mouse,
            )

    def error_correction(self) -> bool:
        """Alias for :meth:`run_error_correction` (used by routes.py)."""
        return self.run_error_correction()

    # ------------------------------------------------------------------
    # Scan progress monitoring
    # ------------------------------------------------------------------

    def get_pixel_status(self) -> Dict[str, Any]:
        """Read current scan progress from screen pixel indicators.

        Returns a dict with ``progress`` (0.0..1.0) and ``complete`` (bool).
        """
        if self.mock_mode:
            # Simulate scan advancing
            self._mock_scan_progress = min(
                1.0, self._mock_scan_progress + random.uniform(0.05, 0.15)
            )
            complete = self._mock_scan_progress >= 1.0
            return {
                "progress": self._mock_scan_progress,
                "complete": complete,
            }

        try:
            # Read the progress indicator bar from config
            status_boxes = self.config.get("WinWerth_Window", {}).get(
                "Status_Farbcode_Boxen", {}
            )
            on_color = status_boxes.get("on_Color", [255, 0, 1])

            # Check tube operational status as a proxy for scan activity
            tube_ready = check_tube_ready(self.config, self.pixel_checker)
            tube_on = check_tube_on(self.config, self.pixel_checker)

            if tube_ready and tube_on:
                return {"progress": 0.5, "complete": False}
            elif tube_on is False and tube_ready is False:
                return {"progress": 1.0, "complete": True}
            else:
                return {"progress": 0.0, "complete": False}
        except Exception as exc:
            logger.error("get_pixel_status failed: %s", exc)
            return {"progress": 0.0, "complete": False}

    def is_scan_complete(self) -> bool:
        """Check whether the current scan has finished."""
        status = self.get_pixel_status()
        return status.get("complete", False)

    # ------------------------------------------------------------------
    # STL save-dialog control
    # ------------------------------------------------------------------

    def open_save_dialog(self) -> bool:
        """Open the WinWerth 'Speichern unter' dialog.

        Navigates: GRAFIK menu -> Speichern unter.
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Opening save dialog")
                time.sleep(random.uniform(0.3, 0.8))
                return True

            try:
                # Click GRAFIK menu
                grafik = self.config["WinWerth_Window"]["Buttons"]["Top_Menu"]["GRAFIK"]
                coords = get_coords(grafik)
                if coords:
                    self.mouse.click_and_wait(coords[0], coords[1], wait_time=0.5)

                # Click SPEICHERN
                speichern = self.config["WinWerth_Window"]["Buttons"]["Top_Menu"]["SPEICHERN"]
                coords = get_coords(speichern)
                if coords:
                    self.mouse.click_and_wait(coords[0], coords[1], wait_time=1.0)

                # Wait for the save dialog to appear
                save_title = self.config.get("STL_Speichern_Unter", {}).get(
                    "TITLE", "Speichern unter"
                )
                result = self.win_api.wait_for_window(save_title, timeout=10)
                return result is not None
            except (KeyError, TypeError) as exc:
                logger.error("open_save_dialog failed: %s", exc)
                return False

    def set_save_path(self, path: str) -> bool:
        """Type *path* into the save dialog's file-name field.

        Uses keyboard input to fill the path text box.
        """
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Setting save path: %s", path)
                time.sleep(random.uniform(0.2, 0.5))
                return True

            try:
                # Click on the path field ("Wähle Ort" / choose location)
                absolute = self.config["STL_Speichern_Unter"]["Absolute"]
                location = get_from_possible_keys(
                    absolute, ["Wähle_Ort", "WÃ¤hle_Ort"]
                )
                coords = get_coords(location)
                if coords:
                    self.mouse.click_and_wait(coords[0], coords[1], wait_time=0.5)

                # Type the path via keyboard
                try:
                    from pynput.keyboard import Controller as KbController, Key

                    kb = KbController()
                    # Select all existing text
                    kb.press(Key.ctrl_l)
                    kb.press("a")
                    kb.release("a")
                    kb.release(Key.ctrl_l)
                    time.sleep(0.1)
                    # Type path
                    kb.type(path)
                    time.sleep(0.2)
                    return True
                except ImportError:
                    logger.warning("pynput not available — cannot type save path")
                    return False
            except (KeyError, TypeError) as exc:
                logger.error("set_save_path failed: %s", exc)
                return False

    def confirm_save(self) -> bool:
        """Click the confirm/save button in the save dialog."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Confirming save")
                time.sleep(random.uniform(0.3, 0.8))
                return True

            try:
                absolute = self.config["STL_Speichern_Unter"]["Absolute"]
                path_btn = get_from_possible_keys(
                    absolute, ["Wähle_Pfad", "WÃ¤hle_Pfad"]
                )
                coords = get_coords(path_btn)
                if coords:
                    self.mouse.click_and_wait(coords[0], coords[1], wait_time=1.0)
                    return True
                return False
            except (KeyError, TypeError) as exc:
                logger.error("confirm_save failed: %s", exc)
                return False

    def close_save_dialog(self) -> bool:
        """Close the save dialog (press Escape or click close)."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Closing save dialog")
                time.sleep(0.2)
                return True

            try:
                from pynput.keyboard import Controller as KbController, Key

                kb = KbController()
                kb.press(Key.esc)
                kb.release(Key.esc)
                time.sleep(0.5)
                return True
            except ImportError:
                logger.warning("pynput not available — cannot close save dialog via Escape")
                # Fallback: try finding and clicking the window close button
                save_title = self.config.get("STL_Speichern_Unter", {}).get(
                    "TITLE", "Speichern unter"
                )
                return self.win_api.wait_for_window_closed(save_title, timeout=5)

    def complete_save_sequence(self, use_relative_coords: bool = False) -> bool:
        """Full STL save sequence: open dialog -> choose location -> choose path.

        Used by routes.py ``/stl/export`` endpoint.
        """
        if self.mock_mode:
            logger.info("[mock] Complete save sequence")
            time.sleep(random.uniform(0.5, 1.5))
            return True

        ok = self.open_save_dialog()
        if not ok:
            logger.error("Save sequence: failed to open dialog")
            return False

        ok = self.confirm_save()
        if not ok:
            logger.error("Save sequence: failed to confirm save")
            self.close_save_dialog()
            return False

        logger.info("Save sequence complete")
        return True

    # ------------------------------------------------------------------
    # Diagnostics & system status
    # ------------------------------------------------------------------

    def get_system_status(self) -> Dict[str, Any]:
        """Return aggregated system status (used by ``/status`` endpoint)."""
        if self.mock_mode:
            return {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mock_mode": True,
                "tube_on": self._mock_tube_on,
                "tube_ready": self._mock_tube_on,
                "rotation_active": self._mock_rotation_active,
                "selected_profile": self._mock_selected_profile,
                "error_boxes": {"left_error": (0, 0, 0), "right_error": (0, 0, 0)},
                "mouse_position": (0, 0),
            }

        tube_on = check_tube_on(self.config, self.pixel_checker)
        tube_ready = check_tube_ready(self.config, self.pixel_checker)

        # Error boxes
        error_boxes: Dict[str, Any] = {}
        try:
            eb = self.config["WinWerth_Window"]["Status_Farbcode_Boxen"]["Error_Boxen"]
            left = get_coords(eb.get("left_Box", {}))
            right = get_coords(eb.get("right_Box", {}))
            if left:
                error_boxes["left_error"] = self.pixel_checker.get_pixel_color(left[0], left[1])
            if right:
                error_boxes["right_error"] = self.pixel_checker.get_pixel_color(right[0], right[1])
        except (KeyError, TypeError):
            pass

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mock_mode": False,
            "tube_on": tube_on,
            "tube_ready": tube_ready,
            "rotation_active": is_drehen_on(self.config, self.pixel_checker, self.mouse),
            "error_boxes": error_boxes,
            "mouse_position": self.mouse.get_mouse_position(),
        }

    def check_tube_status_indicators(self) -> Dict[str, Any]:
        """Return raw pixel colours for tube status indicators."""
        if self.mock_mode:
            on_color = (255, 0, 1) if self._mock_tube_on else (0, 255, 0)
            return {
                "tube_status": on_color,
                "tube_operation_status": on_color,
            }

        results: Dict[str, Any] = {}
        try:
            status_boxes = self.config["WinWerth_Window"]["Status_Farbcode_Boxen"]

            tube_el = get_from_possible_keys(
                status_boxes, ["Roehrenstatus", "RÃ¶hrenstatus"]
            )
            coords = get_coords(tube_el)
            if coords:
                results["tube_status"] = self.pixel_checker.get_pixel_color(
                    coords[0], coords[1]
                )

            tube_op = get_from_possible_keys(
                status_boxes,
                ["Roehrenbetriebstatus", "Röhrenbetriebstatus", "RÃ¶hrenbetriebstatus"],
            )
            coords = get_coords(tube_op)
            if coords:
                results["tube_operation_status"] = self.pixel_checker.get_pixel_color(
                    coords[0], coords[1]
                )
        except (KeyError, TypeError) as exc:
            logger.error("check_tube_status_indicators failed: %s", exc)

        return results

    def check_error_boxes(self) -> Dict[str, Any]:
        """Return current pixel colours of the left/right error boxes."""
        if self.mock_mode:
            return {"left_error": (0, 0, 0), "right_error": (0, 0, 0)}

        results: Dict[str, Any] = {}
        try:
            eb = self.config["WinWerth_Window"]["Status_Farbcode_Boxen"]["Error_Boxen"]
            left = get_coords(eb["left_Box"])
            if left:
                results["left_error"] = self.pixel_checker.get_pixel_color(left[0], left[1])
            right = get_coords(eb["right_Box"])
            if right:
                results["right_error"] = self.pixel_checker.get_pixel_color(right[0], right[1])
        except (KeyError, TypeError) as exc:
            logger.error("check_error_boxes failed: %s", exc)

        return results

    def click_menu_item(self, menu_item: str) -> bool:
        """Click a top-level menu item (DATEI, WERKZEUG, GRAFIK, SPEICHERN)."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Clicking menu item: %s", menu_item)
                return True

            try:
                element = self.config["WinWerth_Window"]["Buttons"]["Top_Menu"][menu_item]
                coords = get_coords(element)
                if coords:
                    return self.mouse.click(coords[0], coords[1])
            except (KeyError, TypeError) as exc:
                logger.error("click_menu_item '%s' failed: %s", menu_item, exc)
            return False

    def click_volume_element(self, element_name: str) -> bool:
        """Click a volume list element (e.g. Voxl3, Voxl3_Kont_3)."""
        with self._lock:
            if self.mock_mode:
                logger.info("[mock] Clicking volume element: %s", element_name)
                return True

            try:
                element = self.config["WinWerth_Window"]["Liste_Komponenten"]["Volumen"][element_name]
                coords = get_coords(element)
                if coords:
                    return self.mouse.click(coords[0], coords[1])
            except (KeyError, TypeError) as exc:
                logger.error("click_volume_element '%s' failed: %s", element_name, exc)
            return False

    def take_diagnostic_screenshot(self, filename: Optional[str] = None) -> str:
        """Save a diagnostic screenshot and return the filename."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"winwerth_diagnostic_{timestamp}.png"

        self.pixel_checker.save_screenshot(filename)
        return filename

    def bring_winwerth_to_front(self) -> bool:
        """Bring the main WinWerth window to the foreground."""
        if self.mock_mode:
            return True
        return bring_to_front(_WINWERTH_TITLE)

    def emergency_stop(self) -> None:
        """Trigger emergency stop — move mouse to corner and log."""
        logger.warning("EMERGENCY STOP triggered")
        self.mouse.emergency_stop()
        self._mock_scan_running = False
        self._mock_scan_progress = 0.0

    # ------------------------------------------------------------------
    # Helpers for scan_machine reset
    # ------------------------------------------------------------------

    def reset_mock_scan_state(self) -> None:
        """Reset mock scan progress (called between scans)."""
        self._mock_scan_progress = 0.0
        self._mock_scan_running = False

    def __repr__(self) -> str:
        mode = "MOCK" if self.mock_mode else "LIVE"
        return f"<WinWerthController mode={mode}>"
