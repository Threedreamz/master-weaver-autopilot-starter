"""
Mouse controller wrapper with configurable pause.

FIX from original: Removed ``mouseDownUp=False`` from drag() which caused the
drag to never release the button.  Pause is now configurable via constructor.
"""

from __future__ import annotations

import logging
import platform
import random
import time
from typing import List, Tuple

logger = logging.getLogger("ctpc-api.mouse")

_IS_GUI_AVAILABLE = False

try:
    import pyautogui

    pyautogui.FAILSAFE = True
    _IS_GUI_AVAILABLE = True
except Exception:
    logger.info("pyautogui not available — MouseController in mock mode")


class MouseController:
    """
    Wraps pyautogui mouse operations with validation and mock fallback.

    Args:
        pause: Global pause between pyautogui actions (seconds).
    """

    def __init__(self, pause: float = 0.1):
        self.mock_mode = not _IS_GUI_AVAILABLE
        self._pause = pause

        if not self.mock_mode:
            pyautogui.PAUSE = pause
            self.screen_width, self.screen_height = pyautogui.size()
        else:
            self.screen_width, self.screen_height = 1920, 1080

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _is_valid(self, x: int, y: int) -> bool:
        return 0 <= x < self.screen_width and 0 <= y < self.screen_height

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1,
              interval: float = 0.0, duration: float = 0.0) -> bool:
        if self.mock_mode:
            logger.debug(f"[mock] click({x}, {y})")
            return True
        if not self._is_valid(x, y):
            logger.warning(f"Invalid coordinates: ({x}, {y})")
            return False
        try:
            pyautogui.click(x, y, clicks=clicks, interval=interval,
                            button=button, duration=duration)
            return True
        except Exception as exc:
            logger.error(f"click({x},{y}) failed: {exc}")
            return False

    def double_click(self, x: int, y: int, button: str = "left") -> bool:
        return self.click(x, y, button=button, clicks=2, interval=0.1)

    def right_click(self, x: int, y: int) -> bool:
        return self.click(x, y, button="right")

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int,
             duration: float = 1.0, button: str = "left") -> bool:
        """
        Drag from (start_x, start_y) to (end_x, end_y).

        FIX: original code passed ``mouseDownUp=False`` which meant the mouse
        button was never released.  We now omit that parameter (defaults True).
        """
        if self.mock_mode:
            logger.debug(f"[mock] drag({start_x},{start_y} -> {end_x},{end_y})")
            return True
        if not (self._is_valid(start_x, start_y) and self._is_valid(end_x, end_y)):
            logger.warning(f"Invalid drag coords: ({start_x},{start_y})->({end_x},{end_y})")
            return False
        try:
            pyautogui.moveTo(start_x, start_y, duration=0.2)
            pyautogui.drag(end_x - start_x, end_y - start_y, duration, button=button)
            return True
        except Exception as exc:
            logger.error(f"drag failed: {exc}")
            return False

    def move_to(self, x: int, y: int, duration: float = 1.0) -> bool:
        if self.mock_mode:
            return True
        if not self._is_valid(x, y):
            return False
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as exc:
            logger.error(f"moveTo failed: {exc}")
            return False

    def scroll(self, x: int, y: int, clicks: int) -> bool:
        if self.mock_mode:
            return True
        if not self._is_valid(x, y):
            return False
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            pyautogui.scroll(clicks)
            return True
        except Exception as exc:
            logger.error(f"scroll failed: {exc}")
            return False

    def click_and_wait(self, x: int, y: int, wait_time: float = 1.0,
                       button: str = "left") -> bool:
        ok = self.click(x, y, button=button)
        if ok:
            time.sleep(wait_time)
        return ok

    def human_like_click(self, x: int, y: int, button: str = "left",
                         offset_range: int = 2) -> bool:
        ox = random.randint(-offset_range, offset_range)
        oy = random.randint(-offset_range, offset_range)
        time.sleep(random.uniform(0.05, 0.2))
        return self.click(x + ox, y + oy, button=button)

    def multi_click_sequence(self, sequence: List[dict],
                             delay_between: float = 0.5) -> bool:
        for i, item in enumerate(sequence):
            ok = self.click(item["x"], item["y"], button=item.get("button", "left"))
            if not ok:
                logger.error(f"Sequence failed at step {i+1}")
                return False
            if i < len(sequence) - 1:
                time.sleep(item.get("wait", delay_between))
        return True

    def get_mouse_position(self) -> Tuple[int, int]:
        if self.mock_mode:
            return (0, 0)
        return pyautogui.position()

    def set_pause(self, duration: float) -> None:
        self._pause = duration
        if not self.mock_mode:
            pyautogui.PAUSE = duration

    def emergency_stop(self) -> None:
        if not self.mock_mode:
            pyautogui.moveTo(0, 0)
        logger.warning("Emergency stop activated")
