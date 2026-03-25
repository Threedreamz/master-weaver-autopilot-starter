"""
Error correction for voltage and ampere scroll bars.

CRITICAL FIXES from original code:
  1. Added ``count_L += 1`` and ``count_R += 1`` inside correction loops
     (original was missing increments -> infinite loop!)
  2. Ampere correction now uses ``count_R`` instead of ``count_L`` for offset.
  3. ``checkErrorLeft`` / ``checkErrorRight`` now receive required
     ``title_Window`` and ``jsonObject`` parameters.
  4. Added bounds checking for percentage values.
  5. Wrapped all operations in try/except for robustness.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .pixel_check import PixelChecker
from .win_api import create_window_api
from .mouse import MouseController

logger = logging.getLogger("ctpc-api.error_correction")


def _check_error_left(
    pixel_checker: PixelChecker,
    title_window: str,
    error_json: Dict[str, Any],
) -> bool:
    """Check whether the left error box shows the error colour."""
    try:
        left_box = error_json["left_Box"]
        error_color = error_json["error_Color"]
        return pixel_checker.check_pixel_color(
            int(left_box["x"]), int(left_box["y"]),
            error_color, tolerance=20,
        )
    except (KeyError, TypeError) as exc:
        logger.error(f"checkErrorLeft config error: {exc}")
        return False


def _check_error_right(
    pixel_checker: PixelChecker,
    title_window: str,
    error_json: Dict[str, Any],
) -> bool:
    """Check whether the right error box shows the error colour."""
    try:
        right_box = error_json["right_Box"]
        error_color = error_json["error_Color"]
        return pixel_checker.check_pixel_color(
            int(right_box["x"]), int(right_box["y"]),
            error_color, tolerance=20,
        )
    except (KeyError, TypeError) as exc:
        logger.error(f"checkErrorRight config error: {exc}")
        return False


def _set_bar_position(
    mouse: MouseController,
    percent: int,
    bar_json: Dict[str, Any],
) -> bool:
    """
    Click a scroll bar at the given percentage position.

    Args:
        percent: 2..99 inclusive.
        bar_json: Dict with keys ``x``, ``y``, ``w``.
    """
    # Bounds check
    percent = max(2, min(99, percent))

    try:
        base_x = int(bar_json["x"])
        y = int(bar_json["y"])
        width = int(bar_json.get("w", 83))
        x = base_x + round((percent / 100) * width)
        return mouse.click(x, y)
    except (KeyError, TypeError) as exc:
        logger.error(f"setBar failed: {exc}")
        return False


def change_voltage_percent(
    mouse: MouseController,
    percent: int,
    scrollbar_json: Dict[str, Any],
) -> bool:
    """Adjust the voltage scroll bar to *percent* and wait for stabilisation."""
    if percent < 2 or percent > 99:
        logger.warning(f"Voltage percent {percent} out of range [2, 99]")
        return False
    ok = _set_bar_position(mouse, percent, scrollbar_json["voltageBar"])
    if ok:
        time.sleep(5)
    return ok


def change_ampere_percent(
    mouse: MouseController,
    percent: int,
    scrollbar_json: Dict[str, Any],
) -> bool:
    """Adjust the ampere scroll bar to *percent* and wait for stabilisation."""
    if percent < 2 or percent > 99:
        logger.warning(f"Ampere percent {percent} out of range [2, 99]")
        return False
    ok = _set_bar_position(mouse, percent, scrollbar_json["ampereBar"])
    if ok:
        time.sleep(5)
    return ok


def error_correction(
    title_window: str,
    config: Dict[str, Any],
    pixel_checker: Optional[PixelChecker] = None,
    mouse: Optional[MouseController] = None,
    max_attempts: int = 10,
) -> bool:
    """
    Run the voltage/ampere error-correction loop.

    Reads error box colours and iteratively adjusts scroll bars until
    the error indicators clear or *max_attempts* is reached.

    Returns True on success, False if correction failed.
    """
    pc = pixel_checker or PixelChecker()
    ms = mouse or MouseController()

    try:
        error_json = config["WinWerth_Window"]["Status_Farbcode_Boxen"]["Error_Boxen"]
        # Merge error_Color into error_json for convenience
        status_boxes = config["WinWerth_Window"]["Status_Farbcode_Boxen"]
        error_json_with_color = {
            **error_json,
            "error_Color": status_boxes.get("error_Color", [0, 255, 0]),
        }
        scrollbar_json = config["WinWerth_Window"]["scrollBar"]
    except KeyError as exc:
        logger.error(f"Error correction config missing: {exc}")
        return False

    # --- FIX #1 & #3: Left error (voltage) correction with proper increment ---
    count_l = 0
    while _check_error_left(pc, title_window, error_json_with_color) and count_l < max_attempts:
        percent = 30 + count_l * 5
        logger.info(f"Left error correction attempt {count_l+1}: voltage -> {percent}%")
        change_voltage_percent(ms, percent, scrollbar_json)
        pc.invalidate_cache()
        count_l += 1  # FIX: was missing in original!

    if count_l >= max_attempts and _check_error_left(pc, title_window, error_json_with_color):
        logger.error("Could not correct left error (voltage) after max attempts")
        return False

    # --- FIX #2: Right error (ampere) correction uses count_R, not count_L ---
    count_r = 0
    while _check_error_right(pc, title_window, error_json_with_color) and count_r < max_attempts:
        percent = 30 + count_r * 5  # FIX: was count_L in original!
        logger.info(f"Right error correction attempt {count_r+1}: ampere -> {percent}%")
        change_ampere_percent(ms, percent, scrollbar_json)
        pc.invalidate_cache()
        count_r += 1  # FIX: was missing in original!

    if count_r >= max_attempts and _check_error_right(pc, title_window, error_json_with_color):
        logger.error("Could not correct right error (ampere) after max attempts")
        return False

    logger.info(f"Error correction complete (voltage: {count_l} tries, ampere: {count_r} tries)")
    return True
