"""
Profile window management — selecting magnification profiles,
opening/closing the profile dialog.

Refactored from original profile_functions.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .pixel_check import PixelChecker
from .win_api import create_window_api
from .mouse import MouseController

logger = logging.getLogger("ctpc-api.profile")

# Known magnification profiles and their list indices (1-based)
PROFILE_MAP = {
    "s": 1,
    "xs": 2,
    "m": 3,
    "l": 4,
    # Absolute-coordinate names from config
    "125L_first": 1,
    "100L_second": 2,
    "50L_third": 3,
}


def window_is_open(title: str) -> bool:
    """Check if a window with *title* is currently open."""
    api = create_window_api()
    return api.get_window_coordinates(title) is not None


def get_hwnd(title: str) -> Optional[int]:
    """Get the HWND of a window by title."""
    api = create_window_api()
    info = api.find_window_by_title(title)
    return info.hwnd if info else None


def bring_to_front(title: str) -> bool:
    """Bring the named window to the foreground."""
    api = create_window_api()
    info = api.find_window_by_title(title)
    if info:
        return api.bring_window_to_front(info.hwnd)
    return False


def open_profile_window(
    main_title: str,
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """
    Open the profile selection window by clicking the profile button
    in the main WinWerth window.
    """
    ms = mouse or MouseController()
    api = create_window_api()

    win_info = api.find_window_by_title(main_title)
    if win_info is None:
        logger.error(f"Main window '{main_title}' not found")
        return False

    try:
        btn = config["WinWerth_Window"]["Profiles"]["button_profile_press"]
        x, y = int(btn["x"]), int(btn["y"])
    except KeyError as exc:
        logger.error(f"Profile button config missing: {exc}")
        return False

    ms.click_and_wait(x, y, wait_time=1.0)

    # Wait for profile window
    profile_title = "Rechner"
    api.invalidate_cache() if hasattr(api, "invalidate_cache") else None
    result = api.wait_for_window(profile_title, timeout=10)
    return result is not None


def choose_profile(
    profile_name: str,
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """
    Click a profile entry in the profile window by name.

    Supports both absolute coordinates (from config Profile_Window.Absolute)
    and relative coordinates (using offsets from Profile_Window.Relative).
    """
    ms = mouse or MouseController()
    api = create_window_api()

    # Try absolute coordinates first
    try:
        abs_profiles = config["Profile_Window"]["Absolute"]
        if profile_name in abs_profiles:
            entry = abs_profiles[profile_name]
            x, y = int(entry["x"]), int(entry["y"])
            return ms.click_and_wait(x, y, wait_time=0.5)
    except (KeyError, TypeError):
        pass

    # Fall back to relative offsets (for named profiles like "s", "xs", "m", "l")
    if profile_name not in PROFILE_MAP:
        logger.error(f"Unknown profile: '{profile_name}'")
        return False

    profile_idx = PROFILE_MAP[profile_name]

    try:
        rel = config["Profile_Window"]["Relative"]
        x_offset = int(rel["Window_X_offset"])
        y_first = int(rel["Window_Y_offset_first"])
        y_step = int(rel["Next_Button_offset"])
    except KeyError as exc:
        logger.error(f"Profile relative config missing: {exc}")
        return False

    # Get profile window position
    profile_win = api.find_window_by_title("Rechner")
    if profile_win is None:
        logger.error("Profile window 'Rechner' not found")
        return False

    win_rect = api.get_window_rect(profile_win.hwnd)
    if win_rect is None:
        return False
    win_x, win_y, _, _ = win_rect

    y = y_first
    if profile_idx > 1:
        y += y_step * (profile_idx - 1)

    abs_x = win_x + x_offset
    abs_y = win_y + y

    return ms.click_and_wait(abs_x, abs_y, wait_time=0.5)


def is_profile_selected(
    profile_name: str,
    config: Dict[str, Any],
    pixel_checker: Optional[PixelChecker] = None,
) -> bool:
    """Check whether a profile row is selected (black highlight)."""
    pc = pixel_checker or PixelChecker()

    if profile_name not in PROFILE_MAP:
        return False

    profile_idx = PROFILE_MAP[profile_name]
    api = create_window_api()

    try:
        rel = config["Profile_Window"]["Relative"]
        x_offset = int(rel["Window_X_offset"])
        y_first = int(rel["Window_Y_offset_first"])
        y_step = int(rel["Next_Button_offset"])
    except KeyError:
        return False

    profile_win = api.find_window_by_title("Rechner")
    if profile_win is None:
        return False

    win_rect = api.get_window_rect(profile_win.hwnd)
    if win_rect is None:
        return False
    win_x, win_y, _, _ = win_rect

    y = y_first
    if profile_idx > 1:
        y += y_step * (profile_idx - 1)

    abs_x = win_x + x_offset
    abs_y = win_y + y

    # Selected profile row is black text on highlight
    return pc.check_pixel_color(abs_x, abs_y, (0, 0, 0), tolerance=11)


def close_profile_window(
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """Close the profile selection window."""
    ms = mouse or MouseController()
    api = create_window_api()

    # Try absolute close button first
    try:
        btn = config["Profile_Window"]["Absolute"]["Schliessen_Button"]
        x, y = int(btn["x"]), int(btn["y"])
        ms.click_and_wait(x, y, wait_time=0.5)
    except KeyError:
        # Try relative
        try:
            rel_btn = config["Profile_Window"]["Relative"]["Schliessen_Button"]
            win_info = api.find_window_by_title("Rechner")
            if win_info is None:
                return False
            win_rect = api.get_window_rect(win_info.hwnd)
            if win_rect is None:
                return False
            x = win_rect[0] + int(rel_btn["x"])
            y = win_rect[1] + int(rel_btn["y"])
            ms.click_and_wait(x, y, wait_time=0.5)
        except KeyError as exc:
            logger.error(f"Close button config missing: {exc}")
            return False

    # Wait for window to close
    return api.wait_for_window_closed("Rechner", timeout=15)
