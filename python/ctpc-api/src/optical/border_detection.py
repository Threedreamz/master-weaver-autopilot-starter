"""OpenCV border detection for CT scan / printed part images.

Ported from AutoPilot Test_Outlining_And_Distances branch (detect_borders.py).
Extracts the outer contour of a dark object on a white(ned) background using
Otsu thresholding, flood-fill hole elimination, and morphological cleanup.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np

    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    np = None  # type: ignore[assignment]
    cv2 = None  # type: ignore[assignment]
    logger.warning("opencv-python not installed — border_detection running in mock mode")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BorderResult:
    """Result of border detection on a single image."""

    contour: "np.ndarray"  # shape (N, 1, 2) — OpenCV contour format
    overlay_image: "np.ndarray"  # BGR image with contour drawn in green
    binary_mask: "np.ndarray"  # uint8 mask (255 = object, 0 = background)
    bounding_box: Tuple[int, int, int, int]  # (x, y, w, h)
    area: float  # contour area in pixels


# ---------------------------------------------------------------------------
# Mock data for environments without OpenCV
# ---------------------------------------------------------------------------

def _mock_border_result() -> BorderResult:
    """Return synthetic test data when OpenCV is unavailable."""
    # Import numpy-stubs or create minimal arrays
    try:
        import numpy as _np
    except ImportError:
        raise RuntimeError(
            "Neither opencv-python nor numpy is available. "
            "Install at least numpy for mock mode."
        )

    # Synthetic square contour (100x100 at offset 50,50)
    contour = _np.array([
        [[50, 50]], [[150, 50]], [[150, 150]], [[50, 150]]
    ], dtype=_np.int32)

    overlay = _np.full((200, 200, 3), 255, dtype=_np.uint8)
    # Draw green rectangle on overlay
    overlay[50, 50:151] = [0, 255, 0]
    overlay[150, 50:151] = [0, 255, 0]
    overlay[50:151, 50] = [0, 255, 0]
    overlay[50:151, 150] = [0, 255, 0]

    mask = _np.zeros((200, 200), dtype=_np.uint8)
    mask[50:151, 50:151] = 255

    return BorderResult(
        contour=contour,
        overlay_image=overlay,
        binary_mask=mask,
        bounding_box=(50, 50, 100, 100),
        area=10000.0,
    )


# ---------------------------------------------------------------------------
# Core array-level function (ported directly from original)
# ---------------------------------------------------------------------------

def detect_outer_outline_no_holes_array(
    img_bgr: "np.ndarray",
    *,
    blur_sigma: float = 1.0,
    morph_close: int = 3,
    min_area: int = 500,
) -> Tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
    """Detect only the outer outline of an object, ignoring internal holes.

    Pipeline: grayscale -> optional Gaussian blur -> Otsu threshold ->
    flood-fill hole elimination -> morphological closing -> RETR_EXTERNAL
    contour extraction.

    Args:
        img_bgr: BGR input image.
        blur_sigma: Gaussian blur sigma (0 to skip).
        morph_close: Morphological closing kernel size (0 to skip).
        min_area: Minimum contour area in pixels; raises if largest
            contour is smaller.

    Returns:
        Tuple of (contour, overlay_bgr, mask_255).

    Raises:
        ValueError: If the image is empty or no contour meets the area
            threshold.
        RuntimeError: If OpenCV is not available.
    """
    if not _CV2_AVAILABLE:
        raise RuntimeError("opencv-python is required for detect_outer_outline_no_holes_array")

    if img_bgr is None or img_bgr.size == 0:
        raise ValueError("Empty image provided.")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    if blur_sigma and blur_sigma > 0:
        gray = cv2.GaussianBlur(gray, (0, 0), float(blur_sigma))

    # Otsu threshold — dark object on white background
    _, bin_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Morphological closing to bridge small gaps
    if morph_close and morph_close > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_close, morph_close))
        bin_inv = cv2.morphologyEx(bin_inv, cv2.MORPH_CLOSE, k)

    # Flood fill from corner to fill external area, then invert to fill holes
    h, w = bin_inv.shape
    ff = bin_inv.copy()
    mask = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 255)  # external region -> white
    holes_filled = bin_inv | (~ff & 0xFF)  # internal holes -> filled

    # Extract only external contours
    cnts, _ = cv2.findContours(holes_filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        raise ValueError("No contours found.")

    cnt = max(cnts, key=cv2.contourArea)
    area = cv2.contourArea(cnt)
    if area < max(1, int(min_area)):
        raise ValueError(f"Largest contour too small (area={area:.0f} < {min_area}).")

    # Draw overlay and create filled mask
    overlay = img_bgr.copy()
    cv2.drawContours(overlay, [cnt], -1, (0, 255, 0), thickness=2, lineType=cv2.LINE_AA)

    mask255 = np.zeros_like(bin_inv, dtype=np.uint8)
    cv2.drawContours(mask255, [cnt], -1, color=255, thickness=cv2.FILLED)

    return cnt, overlay, mask255


def detect_outer_contour_array(
    img_bgr: "np.ndarray",
    *,
    blur_sigma: float = 1.0,
    morph_close: int = 3,
    min_area: int = 500,
) -> Tuple["np.ndarray", "np.ndarray", "np.ndarray"]:
    """Alias for detect_outer_outline_no_holes_array.

    Provided for backward compatibility with imports expecting this name.
    """
    return detect_outer_outline_no_holes_array(
        img_bgr,
        blur_sigma=blur_sigma,
        morph_close=morph_close,
        min_area=min_area,
    )


# ---------------------------------------------------------------------------
# High-level file-based API
# ---------------------------------------------------------------------------

def detect_borders(
    image_path: str,
    *,
    blur_sigma: float = 5.0,
    morph_close: int = 5,
    min_area: int = 1000,
) -> BorderResult:
    """Detect the outer border of an object in an image file.

    This is the primary high-level API. It loads the image, runs the full
    detection pipeline (Otsu + flood fill + morphology + contour extraction),
    and returns a structured ``BorderResult``.

    When OpenCV is not installed, returns synthetic mock data for testing.

    Args:
        image_path: Path to the input image (BGR-decodable).
        blur_sigma: Gaussian blur sigma before thresholding. Higher values
            smooth out noise but may lose fine detail. Default 5.
        morph_close: Morphological closing kernel size. Bridges small gaps
            in the binary mask. Default 5.
        min_area: Minimum acceptable contour area in pixels. Default 1000.

    Returns:
        A ``BorderResult`` with contour, overlay, mask, bounding box, and area.

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If no contour meets the area threshold.
    """
    if not _CV2_AVAILABLE:
        logger.warning("OpenCV not available — returning mock BorderResult")
        return _mock_border_result()

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not decode image: {path}")

    logger.info("Detecting borders: %s (blur=%.1f, close=%d, min_area=%d)",
                path, blur_sigma, morph_close, min_area)

    cnt, overlay, mask = detect_outer_outline_no_holes_array(
        img,
        blur_sigma=blur_sigma,
        morph_close=morph_close,
        min_area=min_area,
    )

    x, y, w, h = cv2.boundingRect(cnt)
    area = float(cv2.contourArea(cnt))

    logger.info("Border detected — area=%.0f  bbox=(%d,%d,%d,%d)", area, x, y, w, h)

    return BorderResult(
        contour=cnt,
        overlay_image=overlay,
        binary_mask=mask,
        bounding_box=(x, y, w, h),
        area=area,
    )


def extract_outline(
    image_path: str,
    *,
    blur_sigma: float = 5.0,
    morph_close: int = 5,
    min_area: int = 1000,
) -> "np.ndarray":
    """Simplified API returning just the outer contour points.

    Convenience wrapper around ``detect_borders()`` for callers that only
    need the contour coordinates.

    Args:
        image_path: Path to the input image.
        blur_sigma: Gaussian blur sigma.
        morph_close: Morphological closing kernel size.
        min_area: Minimum contour area in pixels.

    Returns:
        Contour as an ndarray of shape (N, 1, 2).
    """
    result = detect_borders(
        image_path,
        blur_sigma=blur_sigma,
        morph_close=morph_close,
        min_area=min_area,
    )
    return result.contour
