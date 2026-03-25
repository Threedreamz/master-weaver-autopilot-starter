"""
Windows API wrapper for window enumeration, positioning, and focus management.

Falls back to mock mode on non-Windows platforms.
Includes a 60-second cache for window enumeration results.
"""

from __future__ import annotations

import logging
import platform
import re
import time
from typing import Dict, List, NamedTuple, Optional, Tuple

logger = logging.getLogger("ctpc-api.win_api")

_IS_WINDOWS = platform.system() == "Windows"


class WindowInfo(NamedTuple):
    hwnd: int
    title: str
    class_name: str
    x: int
    y: int
    width: int
    height: int
    is_visible: bool
    is_minimized: bool
    is_maximized: bool


# ---------------------------------------------------------------------------
# Mock implementation for non-Windows
# ---------------------------------------------------------------------------

class _MockWindowAPI:
    """Stub that returns empty results on non-Windows systems."""

    def get_all_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        return []

    def find_window_by_title(self, title: str, **kw) -> Optional[WindowInfo]:
        return None

    def find_windows_by_title(self, title: str, **kw) -> List[WindowInfo]:
        return []

    def get_window_coordinates(self, title: str, **kw) -> Optional[Tuple[int, int, int, int]]:
        return None

    def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
        return None

    def wait_for_window(self, title: str, timeout: float = 30.0, check_interval: float = 1.0) -> Optional[WindowInfo]:
        return None

    def wait_for_window_closed(self, title: str, timeout: float = 30.0, check_interval: float = 1.0) -> bool:
        return True

    def bring_window_to_front(self, hwnd: int) -> bool:
        return True

    def set_window_position(self, hwnd: int, x: int, y: int, width: int = None, height: int = None) -> bool:
        return True

    def is_foreground_title_contains(self, title_part: str, case_sensitive: bool = False) -> bool:
        return False

    def get_active_window(self) -> Optional[WindowInfo]:
        return None


# ---------------------------------------------------------------------------
# Real Windows implementation
# ---------------------------------------------------------------------------

if _IS_WINDOWS:
    import ctypes
    import ctypes.wintypes

    HWND = ctypes.wintypes.HWND
    RECT = ctypes.wintypes.RECT

    class _RealWindowAPI:
        """Wraps Win32 user32 calls with a 60 s window-enumeration cache."""

        _CACHE_TTL = 60.0  # seconds

        def __init__(self):
            self.user32 = ctypes.windll.user32
            self.user32.GetWindowTextLengthW.argtypes = [HWND]
            self.user32.GetWindowTextLengthW.restype = ctypes.c_int
            self.user32.GetWindowTextW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
            self.user32.GetClassNameW.argtypes = [HWND, ctypes.c_wchar_p, ctypes.c_int]
            self.user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(RECT)]
            self.user32.IsWindowVisible.argtypes = [HWND]
            self.user32.IsWindowVisible.restype = ctypes.c_bool
            self.user32.IsIconic.argtypes = [HWND]
            self.user32.IsIconic.restype = ctypes.c_bool
            self.user32.IsZoomed.argtypes = [HWND]
            self.user32.IsZoomed.restype = ctypes.c_bool
            self.user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
            self.user32.SetWindowPos.restype = ctypes.c_bool
            self.user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
            self.user32.ShowWindow.restype = ctypes.c_bool
            self.user32.SetForegroundWindow.argtypes = [HWND]
            self.user32.SetForegroundWindow.restype = ctypes.c_bool
            self.user32.GetForegroundWindow.argtypes = []
            self.user32.GetForegroundWindow.restype = HWND

            # Cache
            self._cached_windows: List[WindowInfo] = []
            self._cache_time: float = 0.0

        # --- low-level helpers ---

        def _get_window_text(self, hwnd: int) -> str:
            try:
                length = self.user32.GetWindowTextLengthW(hwnd)
                if length == 0:
                    return ""
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                return buf.value
            except Exception:
                return ""

        def _get_class_name(self, hwnd: int) -> str:
            try:
                buf = ctypes.create_unicode_buffer(256)
                self.user32.GetClassNameW(hwnd, buf, 256)
                return buf.value
            except Exception:
                return ""

        def get_window_rect(self, hwnd: int) -> Optional[Tuple[int, int, int, int]]:
            try:
                rect = RECT()
                if self.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
            except Exception:
                pass
            return None

        def _get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
            try:
                title = self._get_window_text(hwnd)
                cls = self._get_class_name(hwnd)
                rect = self.get_window_rect(hwnd)
                if rect is None:
                    return None
                x, y, w, h = rect
                return WindowInfo(
                    hwnd=hwnd, title=title, class_name=cls,
                    x=x, y=y, width=w, height=h,
                    is_visible=bool(self.user32.IsWindowVisible(hwnd)),
                    is_minimized=bool(self.user32.IsIconic(hwnd)),
                    is_maximized=bool(self.user32.IsZoomed(hwnd)),
                )
            except Exception:
                return None

        # --- enumeration with cache ---

        def get_all_windows(self, visible_only: bool = True) -> List[WindowInfo]:
            now = time.monotonic()
            if self._cached_windows and (now - self._cache_time) < self._CACHE_TTL:
                windows = self._cached_windows
            else:
                windows_list: List[WindowInfo] = []

                @ctypes.WINFUNCTYPE(ctypes.c_bool, HWND, ctypes.POINTER(ctypes.c_int))
                def _cb(hwnd, _lparam):
                    info = self._get_window_info(hwnd)
                    if info and info.title:
                        windows_list.append(info)
                    return True

                self.user32.EnumWindows(_cb, None)
                self._cached_windows = windows_list
                self._cache_time = time.monotonic()
                windows = windows_list

            if visible_only:
                return [w for w in windows if w.is_visible and not w.is_minimized]
            return list(windows)

        def invalidate_cache(self) -> None:
            self._cached_windows = []
            self._cache_time = 0.0

        # --- finders ---

        def find_window_by_title(self, title: str, exact_match: bool = False, case_sensitive: bool = False) -> Optional[WindowInfo]:
            search = title if case_sensitive else title.lower()
            for w in self.get_all_windows():
                wt = w.title if case_sensitive else w.title.lower()
                if (exact_match and wt == search) or (not exact_match and search in wt):
                    return w
            # Retry with fresh cache
            self.invalidate_cache()
            for w in self.get_all_windows():
                wt = w.title if case_sensitive else w.title.lower()
                if (exact_match and wt == search) or (not exact_match and search in wt):
                    return w
            return None

        def find_windows_by_title(self, title: str, exact_match: bool = False, case_sensitive: bool = False) -> List[WindowInfo]:
            search = title if case_sensitive else title.lower()
            return [
                w for w in self.get_all_windows()
                if ((w.title if case_sensitive else w.title.lower()) == search if exact_match
                    else search in (w.title if case_sensitive else w.title.lower()))
            ]

        def get_window_coordinates(self, title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
            w = self.find_window_by_title(title, exact_match)
            return (w.x, w.y, w.width, w.height) if w else None

        def wait_for_window(self, title: str, timeout: float = 30.0, check_interval: float = 1.0) -> Optional[WindowInfo]:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                self.invalidate_cache()
                w = self.find_window_by_title(title)
                if w:
                    return w
                time.sleep(check_interval)
            return None

        def wait_for_window_closed(self, title: str, timeout: float = 30.0, check_interval: float = 1.0) -> bool:
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                self.invalidate_cache()
                if not self.find_window_by_title(title):
                    return True
                time.sleep(check_interval)
            return False

        def bring_window_to_front(self, hwnd: int) -> bool:
            try:
                if self.user32.IsIconic(hwnd):
                    self.user32.ShowWindow(hwnd, 1)
                return bool(self.user32.SetForegroundWindow(hwnd))
            except Exception:
                return False

        def set_window_position(self, hwnd: int, x: int, y: int, width: int = None, height: int = None) -> bool:
            try:
                if width is None or height is None:
                    rect = self.get_window_rect(hwnd)
                    if rect is None:
                        return False
                    _, _, cw, ch = rect
                    width = width or cw
                    height = height or ch
                return bool(self.user32.SetWindowPos(hwnd, 0, x, y, width, height, 0x0004 | 0x0010))
            except Exception:
                return False

        def is_foreground_title_contains(self, title_part: str, case_sensitive: bool = False) -> bool:
            try:
                hwnd = self.user32.GetForegroundWindow()
                if not hwnd:
                    return False
                title = self._get_window_text(hwnd)
                if not title:
                    return False
                if case_sensitive:
                    return title_part in title
                return title_part.lower() in title.lower()
            except Exception:
                return False

        def get_active_window(self) -> Optional[WindowInfo]:
            try:
                hwnd = self.user32.GetForegroundWindow()
                return self._get_window_info(hwnd) if hwnd else None
            except Exception:
                return None


# ---------------------------------------------------------------------------
# Public factory
# ---------------------------------------------------------------------------

def create_window_api():
    """Return a WindowAPI appropriate for the current platform."""
    if _IS_WINDOWS:
        return _RealWindowAPI()
    logger.info("Non-Windows platform — using mock WindowAPI")
    return _MockWindowAPI()


# Convenience module-level functions
def get_window_coordinates(title: str, exact_match: bool = False) -> Optional[Tuple[int, int, int, int]]:
    return create_window_api().get_window_coordinates(title, exact_match)


def find_window(title: str, exact_match: bool = False) -> Optional[WindowInfo]:
    return create_window_api().find_window_by_title(title, exact_match)


def is_window_foreground(title_part: str, case_sensitive: bool = False) -> bool:
    return create_window_api().is_foreground_title_contains(title_part, case_sensitive)
