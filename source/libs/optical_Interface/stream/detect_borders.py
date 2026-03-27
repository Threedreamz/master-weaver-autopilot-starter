# detect_borders.py (Ergänzung)
import cv2
import numpy as np
from typing import Tuple

def detect_outer_outline_no_holes_array(
    img_bgr: np.ndarray,
    *,
    blur_sigma: float = 1.0,
    morph_close: int = 3,
    min_area: int = 500
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Liefert NUR den äußeren Umriss eines Objekts (Löcher werden ignoriert).
    Pipeline: Graustufe -> (optional Blur) -> Otsu-Threshold -> Löcher füllen -> RETR_EXTERNAL
    Returns: (contour, overlay_bgr, mask_255)
    """
    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Leeres Bild übergeben.")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if blur_sigma and blur_sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), float(blur_sigma))

    # Otsu: dunkles Objekt auf hellem (weiß gemachten) Hintergrund
    # Je nach Kontrast ggf. THRESH_BINARY_INV tauschen:
    _, bin_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Kleine Lücken schließen
    if morph_close and morph_close > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_close, morph_close))
        bin_inv = cv2.morphologyEx(bin_inv, cv2.MORPH_CLOSE, k)

    # Löcher füllen (flood fill vom Rand):
    h, w = bin_inv.shape
    ff = bin_inv.copy()
    mask = np.zeros((h+2, w+2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 255)          # Außenbereich weiß füllen
    holes_filled = bin_inv | (~ff & 0xFF)         # Innenlöcher weg (Objekt bleibt kompakt)

    # ÄUSSERE Kontur
    cnts, _ = cv2.findContours(holes_filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise ValueError("Keine Konturen gefunden.")

    cnt = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area < max(1, int(min_area)):
        raise ValueError(f"Größte Kontur zu klein (Fläche={area:.0f} < {min_area}).")

    # Overlay und Maske
    overlay = img_bgr.copy()
    cv2.drawContours(overlay, [cnt], -1, (0, 255, 0), thickness=2, lineType=cv2.LINE_AA)

    mask255 = np.zeros_like(bin_inv, dtype=np.uint8)
    cv2.drawContours(mask255, [cnt], -1, color=255, thickness=cv2.FILLED)

    return cnt, overlay, mask255
