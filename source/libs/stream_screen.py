# stream_screen.py  (Ergänzung)
from __future__ import annotations
from typing import Optional, Tuple, Iterator
import time
import numpy as np
import cv2

def iterate_screen(
    *,
    region: Optional[Tuple[int, int, int, int]] = None,
    monitor_index: int = 1,
    fps: float = 30.0,
) -> Iterator[np.ndarray]:
    """
    Liefert kontinuierlich BGR-Frames eines Bildschirmbereichs (ohne weitere Verarbeitung).
    """
    try:
        import mss
    except ImportError as e:
        raise RuntimeError("Bitte 'mss' installieren: pip install mss") from e

    if fps <= 0:
        fps = 30.0
    frame_delay = 1.0 / fps
    last = time.time()

    with mss.mss() as sct:
        monitors = sct.monitors
        if not (0 <= monitor_index < len(monitors)):
            monitor_index = 1
        mon = monitors[monitor_index]

        if region is None:
            bbox = {"left": mon["left"], "top": mon["top"], "width": mon["width"], "height": mon["height"]}
        else:
            x, y, w, h = region
            bbox = {"left": mon["left"] + int(x), "top": mon["top"] + int(y), "width": int(w), "height": int(h)}

        while True:
            sct_img = sct.grab(bbox)
            frame = np.array(sct_img)
            if frame.shape[2] == 4:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            yield frame

            # FPS drosseln
            now = time.time()
            dt = now - last
            sleep_left = frame_delay - dt
            if sleep_left > 0:
                time.sleep(sleep_left)
            last = time.time()
