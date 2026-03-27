import ctypes
from ctypes import wintypes
from pywinauto import Application

# structures for GetMonitorInfo
class RECT(ctypes.Structure):
    _fields_ = [('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long)]
    def width(self): return self.right - self.left
    def height(self): return self.bottom - self.top

class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('rcMonitor', RECT),
        ('rcWork', RECT),
        ('dwFlags', wintypes.DWORD),
        ('szDevice', ctypes.c_wchar * 32)
    ]

class monitor:
    """
    Utility to find which monitor a pywinauto window is on.
    Usage:
      m = Monitor()
      info = m.get_window_monitor(dlg)   # pass WindowWrapper (dlg) or None if stored in instance
    """
    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(RECT),
        wintypes.LPARAM
    )

    user32 = ctypes.windll.user32

    def __init__(self, dlg=None):
        self.dlg = dlg

    def _enum_monitors(self):
        monitors = []

        def _callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(MONITORINFOEXW)
            res = self.user32.GetMonitorInfoW(hMonitor, ctypes.byref(info))
            if res == 0:
                return True  # continue anyway
            r = info.rcMonitor
            w = info.rcWork
            monitors.append({
                'hmonitor': hMonitor,
                'monitor_rect': (r.left, r.top, r.right, r.bottom),
                'work_rect': (w.left, w.top, w.right, w.bottom),
                'name': info.szDevice
            })
            return True

        enum_proc = self.MONITORENUMPROC(_callback)
        if not self.user32.EnumDisplayMonitors(None, None, enum_proc, 0):
            raise ctypes.WinError()
        return monitors

    @staticmethod
    def _rect_overlap_area(a, b):
        # a and b are tuples (l,t,r,b)
        left = max(a[0], b[0])
        top = max(a[1], b[1])
        right = min(a[2], b[2])
        bottom = min(a[3], b[3])
        if right <= left or bottom <= top:
            return 0
        return (right - left) * (bottom - top)

    def get_window_monitor(self, dlg=None):
        """
        dlg: optional pywinauto WindowWrapper (if not provided, uses self.dlg).
        Returns dict or None:
          {
            'monitor_index': int,   # 1-based
            'monitor_name': str,
            'monitor_rect': (l,t,r,b),
            'work_rect': (l,t,r,b),
            'window_rect': (l,t,r,b),
            'overlap_area': int
          }
        """
        if dlg is None:
            dlg = self.dlg
        if dlg is None:
            raise ValueError("No dlg provided and no self.dlg set")

        try:
            rect = dlg.rectangle()
            win_rect = (rect.left, rect.top, rect.right, rect.bottom)
        except Exception:
            return None

        monitors = self._enum_monitors()
        if not monitors:
            return None

        best_idx = None
        best_area = -1
        for idx, m in enumerate(monitors, start=1):
            area = self._rect_overlap_area(win_rect, m['monitor_rect'])
            if area > best_area:
                best_area = area
                best_idx = idx

        # fallback if no overlap: use window center to decide
        if best_area == 0:
            cx = (win_rect[0] + win_rect[2]) // 2
            cy = (win_rect[1] + win_rect[3]) // 2
            found = None
            for idx, m in enumerate(monitors, start=1):
                l,t,r,b = m['monitor_rect']
                if l <= cx < r and t <= cy < b:
                    found = (idx, m)
                    break
            if found:
                best_idx = found[0]
                best_area = 0
            else:
                # nearest by center distance
                best_dist = None
                for idx, m in enumerate(monitors, start=1):
                    l,t,r,b = m['monitor_rect']
                    mcx = (l + r) / 2
                    mcy = (t + b) / 2
                    dist = (mcx - cx) ** 2 + (mcy - cy) ** 2
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_idx = idx
                best_area = 0

        chosen = monitors[best_idx - 1]
        return {
            'monitor_index': best_idx,
            'monitor_name': chosen.get('name'),
            'monitor_rect': chosen.get('monitor_rect'),
            'work_rect': chosen.get('work_rect'),
            'window_rect': win_rect,
            'overlap_area': best_area
        }

    def is_on_display(self, display_number, dlg=None):
        """
        Convenience helper: returns True if window is (mostly) on the given 1-based display_number.
        """
        info = self.get_window_monitor(dlg)
        if info is None:
            return False
        return info['monitor_index'] == display_number

