# bg_whiten.py  (Ergänzung)
import numpy as np
import cv2
from typing import Tuple

def whiten_bg_array(
    gray: np.ndarray,
    *,
    feather_sigma: float = 1.5,
    morph_open: int = 3,
    offset: int = 0,
) -> Tuple[np.ndarray, int]:
    """
    Setzt den Hintergrund eines Graubilds in-memory auf Weiß (ohne Speichern).
    Returns: (out_gray_uint8, verwendeter_threshold)
    """
    if gray.ndim == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)

    t, obj_mask = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    if offset != 0:
        t2 = int(np.clip(t + offset, 0, 255))
        _, obj_mask = cv2.threshold(blur, t2, 255, cv2.THRESH_BINARY_INV)
        t = t2

    if morph_open and morph_open > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_open, morph_open))
        obj_mask = cv2.morphologyEx(obj_mask, cv2.MORPH_OPEN, k)

    soft = cv2.GaussianBlur(obj_mask, (0, 0), float(feather_sigma)) if feather_sigma > 0 else obj_mask
    alpha = (soft.astype(np.float32) / 255.0)

    white_bg = np.full_like(gray, 255, dtype=np.uint8)
    out = (alpha * gray.astype(np.float32) + (1.0 - alpha) * white_bg.astype(np.float32)).astype(np.uint8)
    return out, int(t)


