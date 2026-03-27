
"""
stream_controller.py

Provides three functions the rest of your code can call:
 - start_stream(cfg=None)   -> starts the capture/processing loop in a background thread
 - stop_stream()            -> requests the loop to stop and waits for it to finish
 - get_current_records()    -> returns a snapshot dict with the current record/min-distances

Design notes / behavior:
 - If cfg is None, the module will try to import `parse_args` from border_stream (your existing entrypoint)
   and use that. You can also pass the same AppConfig object your run_app() uses.
 - The running loop uses a threading.Thread and a threading.Event to stop cleanly.
 - The module will try to reuse your existing RecordState (import from app.state). If that fails,
   a small compatible fallback RecordState is used.
 - The processing pipeline uses your whiten_bg_array, detect_outer_outline_no_holes_array and
   draw_margin_overlays functions (imported from your files).
 - get_current_records() returns a plain dict snapshot (ints / tuples) safe to read from other threads.
"""

from __future__ import annotations
import threading
import time
from typing import Optional, Dict, Any

import cv2
import numpy as np

# Try to import user modules (these files you uploaded)
try:
    from libs.optical_Interface.bg_whiten import whiten_bg_array
except Exception as e:
    raise ImportError("Could not import whiten_bg_array from bg_whiten.py") from e

try:
    from libs.optical_Interface.stream.detect_borders import detect_outer_outline_no_holes_array
except Exception as e:
    raise ImportError("Could not import detect_outer_outline_no_holes_array from detect_borders.py") from e

try:
    from libs.optical_Interface.stream.overlays import draw_margin_overlays
except Exception as e:
    raise ImportError("Could not import draw_margin_overlays from overlays.py") from e

# The iterate_screen / parse_args / AppConfig live in border_stream.py in your project.
# start_stream(cfg=None) will use them when cfg is not provided.
try:
    import libs.optical_Interface.stream.border_stream as border_stream_module
    have_border_stream = True
except Exception:
    have_border_stream = False

# Try to reuse your RecordState; otherwise provide a small compatible fallback.
try:
    from app.state import RecordState as _UserRecordState
    RecordState = _UserRecordState
except Exception:
    # fallback minimal RecordState compatible with overlays.draw_margin_overlays usage
    class RecordState:
        def __init__(self):
            self.min_t = None
            self.min_b = None
            self.min_l = None
            self.min_r = None
            self.line_t = None
            self.line_b = None
            self.line_l = None
            self.line_r = None

        def reset(self):
            self.__init__()

# ---- module-global controller state ----
_stream_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None
_record_lock = threading.Lock()
_record_state: Optional[RecordState] = None

def _make_snapshot(record: RecordState) -> Dict[str, Any]:
    """Create a plain dict snapshot of the record state (safe to return across threads)."""
    return {
        'min_t': int(record.min_t) if record.min_t is not None else None,
        'min_b': int(record.min_b) if record.min_b is not None else None,
        'min_l': int(record.min_l) if record.min_l is not None else None,
        'min_r': int(record.min_r) if record.min_r is not None else None,
        'line_t': record.line_t,
        'line_b': record.line_b,
        'line_l': record.line_l,
        'line_r': record.line_r,
    }

def get_current_records() -> Optional[Dict[str, Any]]:
    """
    Return snapshot of the currently recorded minimum distances and record lines.
    Returns None if stream not running / no record state available.
    """
    global _record_state
    if _record_state is None:
        return None
    with _record_lock:
        return _make_snapshot(_record_state)

def _stream_loop(cfg, stop_event: threading.Event, record: RecordState) -> None:
    """
    Internal thread function: runs the capture -> processing -> overlay -> imshow loop.
    Exits when stop_event.is_set() or user presses 'q'/'ESC'.
    Updates the shared `record` object (protected by _record_lock in this module).
    """
    window_title = getattr(cfg, "window_title", "Stream")
    cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)

    fps = getattr(cfg, "fps", 15)
    # iterate_screen should be your generator that yields BGR frames.
    if not have_border_stream:
        raise RuntimeError("border_stream module unavailable: cannot iterate_screen")

    try:
        for frame_bgr in border_stream_module.iterate_screen(region=getattr(cfg, "region", None),
                                                             monitor_index=getattr(cfg, "monitor_index", 0),
                                                             fps=fps):
            if stop_event.is_set():
                break

            # preprocessing
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            white_bg_gray, _ = whiten_bg_array(
                gray,
                feather_sigma=1.5,
                morph_open=3,
                offset=0,
            )
            white_bg_bgr = cv2.cvtColor(white_bg_gray, cv2.COLOR_GRAY2BGR)

            # detection + overlays
            try:
                cnt, overlay, mask = detect_outer_outline_no_holes_array(
                    white_bg_bgr,
                    blur_sigma=1.0,
                    morph_close=3,
                    min_area=500
                )
                # update shared record in a threadsafe manner
                with _record_lock:
                    draw_margin_overlays(overlay, cnt, record)
                    # copy overlay to view for display
                    view = overlay.copy()
            except Exception as e:
                view = white_bg_bgr.copy()
                cv2.putText(view, str(e), (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

            hint = "REC (Session): rosa Linien MIN T/B/L/R. 'r' = reset. q/ESC = quit stream"
            cv2.putText(view, hint, (12, view.shape[0]-12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(view, hint, (12, view.shape[0]-12), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 1, cv2.LINE_AA)

            cv2.imshow(window_title, view)
            k = cv2.waitKey(1) & 0xFF
            if k in (27, ord('q')):
                # user requested quit via keyboard -> request stop
                stop_event.set()
                break
            elif k in (ord('r'), ord('R')):
                with _record_lock:
                    record.reset()

            # throttle if iterate_screen is very fast (smoothing)
            time.sleep(max(0, 1.0 / fps - 0.001))
    finally:
        try:
            cv2.destroyWindow(window_title)
        except Exception:
            pass

def start_stream(cfg=None) -> None:
    """
    Start the processing stream in a background thread.
    - cfg: optional config object (must provide region, monitor_index, fps, window_title). If None,
           start_stream will try to call border_stream.parse_args() to get a config.
    - If a stream is already running, this function does nothing (idempotent).
    """
    global _stream_thread, _stop_event, _record_state

    if _stream_thread is not None and _stream_thread.is_alive():
        # already running
        return

    # obtain cfg if not provided
    if cfg is None:
        if not have_border_stream:
            raise RuntimeError("No cfg provided and border_stream module not available.")
        cfg = getattr(border_stream_module, "parse_args")()

    _stop_event = threading.Event()
    _record_state = RecordState()

    _stream_thread = threading.Thread(
        target=_stream_loop,
        args=(cfg, _stop_event, _record_state),
        name="border_stream_thread",
        daemon=True
    )
    _stream_thread.start()

def stop_stream(wait: bool = True, timeout: Optional[float] = 5.0) -> None:
    """
    Request the stream to stop.
    - wait: if True, join the worker thread (up to timeout seconds).
    - timeout: seconds to wait for thread to finish (None = wait indefinitely).
    After stop_stream returns, the global stream state is cleared.
    """
    global _stream_thread, _stop_event, _record_state
    if _stop_event is None:
        return
    _stop_event.set()
    if wait and _stream_thread is not None:
        _stream_thread.join(timeout=timeout)

    # cleanup
    _stream_thread = None
    _stop_event = None
    _record_state = None

# -------------------------
# Example quick CLI usage:
# -------------------------
if __name__ == "__main__":
    # If you run this module directly, it will try to use border_stream.parse_args()
    if not have_border_stream:
        print("border_stream module not found. Provide a cfg when calling start_stream(cfg).")
    else:
        cfg = border_stream_module.parse_args()
        print("Starting stream (press q/ESC in window to stop)...")
        start_stream(cfg)
        try:
            # wait until thread stops (or user presses q)
            while _stream_thread is not None and _stream_thread.is_alive():
                time.sleep(0.2)
        except KeyboardInterrupt:
            stop_stream()
        print("Stream stopped.")
