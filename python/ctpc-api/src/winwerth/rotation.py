"""
Rotation (Drehen) section control.

Merged from original drehen_functions.py + a_control.py.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from .pixel_check import PixelChecker
from .mouse import MouseController
from .config import get_coords

logger = logging.getLogger("ctpc-api.rotation")


def _click_werkzeuge(
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """Click the 'WERKZEUG' top-menu button."""
    ms = mouse or MouseController()
    try:
        btn = config["WinWerth_Window"]["Buttons"]["Top_Menu"]["WERKZEUG"]
        x, y = int(btn["x"]), int(btn["y"])
        return ms.click_and_wait(x, y, wait_time=0.5)
    except (KeyError, TypeError) as exc:
        logger.error(f"clickWerkzeuge failed: {exc}")
        return False


def _click_drehen(
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """Click the 'WERKZEUG_AUSWAHL' (Drehen sub-menu) button."""
    ms = mouse or MouseController()
    try:
        btn = config["WinWerth_Window"]["Buttons"]["Top_Menu"]["WERKZEUG_AUSWAHL"]
        x, y = int(btn["x"]), int(btn["y"])
        return ms.click_and_wait(x, y, wait_time=0.5)
    except (KeyError, TypeError) as exc:
        logger.error(f"clickDrehen failed: {exc}")
        return False


def is_drehen_on(
    config: Dict[str, Any],
    pixel_checker: Optional[PixelChecker] = None,
    mouse: Optional[MouseController] = None,
) -> bool:
    """
    Check if the Drehen (rotation) mode is active.

    Opens the Werkzeug menu, checks the pixel colour, then closes it.
    """
    pc = pixel_checker or PixelChecker()
    ms = mouse or MouseController()

    try:
        rot_config = config["WinWerth_Window"]["Rotierung"]
    except KeyError:
        logger.error("Rotierung config not found")
        return False

    # Open werkzeug menu to reveal drehen indicator
    _click_werkzeuge(config, ms)

    # Check drehen indicator colour
    try:
        # Rotierung.Menu_Button holds indicator coords
        menu_btn = rot_config.get("Menu_Button", [120, 812])
        x, y = int(menu_btn[0]), int(menu_btn[1])
        # Active drehen typically shows a specific colour; check for non-gray
        actual = pc.get_pixel_color(x, y)
        is_active = actual != (0, 0, 0)  # simplified check
    except Exception as exc:
        logger.error(f"is_drehen_on pixel check failed: {exc}")
        is_active = False

    # Close werkzeug menu
    _click_werkzeuge(config, ms)

    return is_active


def activate_drehen(
    config: Dict[str, Any],
    mouse: Optional[MouseController] = None,
) -> bool:
    """
    Activate the Drehen (rotation) mode via Werkzeug menu.

    Returns True if drehen is now active.
    """
    ms = mouse or MouseController()

    _click_werkzeuge(config, ms)
    _click_drehen(config, ms)
    _click_werkzeuge(config, ms)

    return is_drehen_on(config, mouse=ms)


def set_rotation_angle(
    config: Dict[str, Any],
    angle: int = 360,
    mouse: Optional[MouseController] = None,
) -> bool:
    """
    Type a rotation angle into the A-box text field.

    Note: requires pynput keyboard support.
    """
    ms = mouse or MouseController()

    try:
        rot_config = config["WinWerth_Window"]["Rotierung"]
        a_box = rot_config.get("A_Box", [30, 817])
        x, y = int(a_box[0]), int(a_box[1])
    except (KeyError, TypeError) as exc:
        logger.error(f"set_rotation_angle config error: {exc}")
        return False

    # Click on A_Box to focus it
    if not ms.click(x, y):
        return False

    # Type the angle via keyboard
    try:
        from pynput.keyboard import Controller as KbController, Key

        kb = KbController()
        # Select all existing text
        kb.press(Key.ctrl_l)
        kb.press("a")
        kb.release("a")
        kb.release(Key.ctrl_l)
        # Type the angle
        kb.type(str(angle))
        # Press enter
        kb.press(Key.enter)
        kb.release(Key.enter)
        return True
    except ImportError:
        logger.warning("pynput not available — cannot type rotation angle")
        return False
    except Exception as exc:
        logger.error(f"set_rotation_angle keyboard input failed: {exc}")
        return False
