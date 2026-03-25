"""
Tube (Rohre) status checking and control.

Merged from original roehren_Click.py + roehren_Status.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .pixel_check import PixelChecker
from .win_api import create_window_api
from .mouse import MouseController

logger = logging.getLogger("ctpc-api.tube")


def check_tube_on(
    config: Dict[str, Any],
    pixel_checker: Optional[PixelChecker] = None,
) -> Optional[bool]:
    """
    Check if the X-ray tube is powered on.

    Returns:
        True  — tube is ON (matches on_Color)
        False — tube is OFF (matches off_Color)
        None  — indeterminate (neither colour matched)
    """
    pc = pixel_checker or PixelChecker()

    try:
        status_boxes = config["WinWerth_Window"]["Status_Farbcode_Boxen"]
        tube_status = status_boxes["Roehrenstatus"]
        off_color = status_boxes["off_Color"]
        on_color = status_boxes["on_Color"]
    except KeyError as exc:
        logger.error(f"Tube status config missing: {exc}")
        return None

    x, y = int(tube_status["x"]), int(tube_status["y"])

    # Check off first
    if pc.check_pixel_color(x, y, off_color, tolerance=20):
        return False
    if pc.check_pixel_color(x, y, on_color, tolerance=20):
        return True
    return None


def check_tube_ready(
    config: Dict[str, Any],
    pixel_checker: Optional[PixelChecker] = None,
) -> Optional[bool]:
    """
    Check if the tube is in ready/operational state.

    Returns:
        True  — tube is ready (matches ready_Color / on_Color)
        False — tube is not ready (matches off_Color)
        None  — indeterminate
    """
    pc = pixel_checker or PixelChecker()

    try:
        status_boxes = config["WinWerth_Window"]["Status_Farbcode_Boxen"]
        tube_op = status_boxes["Roehrenbetriebstatus"]
        off_color = status_boxes["off_Color"]
        # ready_Color may not exist; fall back to on_Color
        ready_color = status_boxes.get("ready_Color", status_boxes.get("on_Color", [255, 0, 1]))
    except KeyError as exc:
        logger.error(f"Tube ready config missing: {exc}")
        return None

    x, y = int(tube_op["x"]), int(tube_op["y"])

    if pc.check_pixel_color(x, y, off_color, tolerance=20):
        return False
    if pc.check_pixel_color(x, y, ready_color, tolerance=20):
        return True
    return None


def click_tube_on(
    title_window: str,
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
    safety_pin: bool = True,
) -> bool:
    """
    Click the 'Rohre An' button to power on the tube.

    If *safety_pin* is True (default), the click is blocked as a safety measure.
    Set ``safety_pin=False`` explicitly to allow tube activation.
    """
    if safety_pin:
        logger.warning("Safety pin active — tube power-on blocked")
        return False

    ms = mouse or MouseController()

    try:
        buttons = config["WinWerth_Window"]["Buttons"]
        # Handle possible UTF-8 encoding variants
        tube_btn = None
        for key in ["Rohre_An", "Röhre_An", "RÃ¶hre_An"]:
            if key in buttons:
                tube_btn = buttons[key]
                break

        if tube_btn is None:
            logger.error("Tube power button not found in config")
            return False

        x, y = int(tube_btn["x"]), int(tube_btn["y"])

        # Bring WinWerth window to front first
        win_api = create_window_api()
        win_info = win_api.find_window_by_title(title_window)
        if win_info:
            win_api.bring_window_to_front(win_info.hwnd)

        return ms.click_and_wait(x, y, wait_time=1.0)

    except (KeyError, TypeError) as exc:
        logger.error(f"click_tube_on failed: {exc}")
        return False
