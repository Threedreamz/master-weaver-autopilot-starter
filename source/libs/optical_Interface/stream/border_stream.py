# detect_borders.py  (Ergänzung)
import numpy as np
import cv2
from typing import Tuple



def detect_outer_contour_array(
    img_bgr: np.ndarray,
    *,
    blur_sigma: float = 1.0,
    canny_low: int = 50,
    canny_high: int = 150,
    morph_close: int = 3,
    min_area: int = 500
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Wie detect_outer_contour(..), aber arbeitet direkt auf einem BGR-Array.
    Returns: (contour, overlay_bgr, mask_255)
    """
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Leeres Bild übergeben.")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    if blur_sigma and blur_sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), float(blur_sigma))

    edges = cv2.Canny(gray, threshold1=int(canny_low), threshold2=int(canny_high))
    if morph_close and morph_close > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_close, morph_close))
        edges
