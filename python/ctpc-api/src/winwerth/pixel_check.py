"""
Pixel colour checker with screenshot caching (200 ms TTL).

On non-Windows / headless systems this falls back to mock mode returning
black pixels and empty regions.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger("ctpc-api.pixel_check")

# Try importing pyautogui — may fail on non-Windows / headless
try:
    import pyautogui
    import PIL.Image

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    _HAS_PYAUTOGUI = True
except Exception:
    _HAS_PYAUTOGUI = False
    logger.info("pyautogui not available — PixelChecker in mock mode")


class PixelChecker:
    """
    Screen pixel colour reader with a screenshot cache.

    The cache avoids taking a new screenshot for every single pixel read
    when multiple checks are done in rapid succession (e.g. error-box
    left + right).  TTL defaults to 200 ms.
    """

    def __init__(self, cache_ttl_ms: float = 200.0):
        self._cache_ttl = cache_ttl_ms / 1000.0  # store as seconds
        self._cached_screenshot: Optional[PIL.Image.Image] = None if _HAS_PYAUTOGUI else None
        self._cache_time: float = 0.0
        self.mock_mode = not _HAS_PYAUTOGUI

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_screenshot(self) -> Optional[object]:
        """Return a (possibly cached) full-screen screenshot."""
        if self.mock_mode:
            return None

        now = time.monotonic()
        if self._cached_screenshot is not None and (now - self._cache_time) < self._cache_ttl:
            return self._cached_screenshot

        try:
            self._cached_screenshot = pyautogui.screenshot()
            self._cache_time = time.monotonic()
            return self._cached_screenshot
        except Exception as exc:
            logger.error(f"Screenshot failed: {exc}")
            return None

    def invalidate_cache(self) -> None:
        """Force next read to take a fresh screenshot."""
        self._cached_screenshot = None
        self._cache_time = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Return (r, g, b) at screen coordinate (x, y)."""
        if self.mock_mode:
            return (0, 0, 0)

        screenshot = self._get_screenshot()
        if screenshot is None:
            return (0, 0, 0)
        try:
            return screenshot.getpixel((x, y))[:3]
        except Exception as exc:
            logger.error(f"getpixel({x},{y}) failed: {exc}")
            return (0, 0, 0)

    def check_pixel_color(
        self,
        x: int,
        y: int,
        expected_color: Union[Tuple[int, int, int], List[int]],
        tolerance: int = 5,
    ) -> bool:
        """True if pixel at (x, y) matches *expected_color* within *tolerance*."""
        actual = self.get_pixel_color(x, y)
        expected = tuple(expected_color) if isinstance(expected_color, list) else expected_color
        return all(abs(a - e) <= tolerance for a, e in zip(actual, expected))

    def check_multiple_pixels(
        self,
        coordinates_colors: List[Dict],
        tolerance: int = 5,
    ) -> Dict[str, Dict]:
        """Check several pixels in one shot (shares a single cached screenshot)."""
        self.invalidate_cache()  # force a fresh screenshot for the batch
        results: Dict[str, Dict] = {}
        for i, pd in enumerate(coordinates_colors):
            coords = pd["coords"]
            expected = pd["color"]
            name = pd.get("name", f"pixel_{i}")
            match = self.check_pixel_color(coords[0], coords[1], expected, tolerance)
            results[name] = {
                "coordinates": coords,
                "expected_color": expected,
                "actual_color": self.get_pixel_color(coords[0], coords[1]),
                "match": match,
            }
        return results

    def wait_for_pixel_color(
        self,
        x: int,
        y: int,
        expected_color: Union[Tuple[int, int, int], List[int]],
        timeout: float = 10.0,
        check_interval: float = 0.1,
        tolerance: int = 5,
    ) -> bool:
        """Poll until pixel matches or timeout expires."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.invalidate_cache()
            if self.check_pixel_color(x, y, expected_color, tolerance):
                return True
            time.sleep(check_interval)
        return False

    def get_region_colors(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Capture a rectangular region and return as numpy BGR array."""
        if self.mock_mode:
            return np.zeros((height, width, 3), dtype=np.uint8)
        try:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            return np.array(screenshot)
        except Exception as exc:
            logger.error(f"Region capture failed: {exc}")
            return np.array([])

    def find_color_in_region(
        self,
        region_coords: Tuple[int, int, int, int],
        target_color: Union[Tuple[int, int, int], List[int]],
        tolerance: int = 5,
    ) -> Optional[Tuple[int, int]]:
        """Find first occurrence of *target_color* in region. Returns absolute coords."""
        x, y, w, h = region_coords
        target = tuple(target_color) if isinstance(target_color, list) else target_color
        region = self.get_region_colors(x, y, w, h)
        if region.size == 0:
            return None
        for row in range(min(h, region.shape[0])):
            for col in range(min(w, region.shape[1])):
                px = tuple(region[row, col, :3])
                if all(abs(a - e) <= tolerance for a, e in zip(px, target)):
                    return (x + col, y + row)
        return None

    def save_screenshot(
        self,
        filename: str = "screenshot.png",
        region: Optional[Tuple[int, int, int, int]] = None,
    ) -> None:
        """Save a screenshot to disk."""
        if self.mock_mode:
            logger.info(f"Mock mode — skipping screenshot save to {filename}")
            return
        try:
            shot = pyautogui.screenshot(region=region) if region else pyautogui.screenshot()
            shot.save(filename)
            logger.info(f"Screenshot saved: {filename}")
        except Exception as exc:
            logger.error(f"Screenshot save failed: {exc}")
