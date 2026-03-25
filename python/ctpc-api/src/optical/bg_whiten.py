"""Background whitening for CT scan image preprocessing.

Ported from AutoPilot Test_Outlining_And_Distances branch (bg_whiten.py).
Sets the background of a grayscale image to white using Otsu thresholding
and soft alpha blending, preparing images for clean border detection.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
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
    logger.warning("opencv-python not installed — bg_whiten running in mock mode")


@dataclass
class WhitenResult:
    """Result of background whitening."""

    image: "np.ndarray"  # grayscale uint8, background set to white
    threshold: int  # Otsu threshold value used


# ---------------------------------------------------------------------------
# Core array-level function (ported directly from original)
# ---------------------------------------------------------------------------

def whiten_bg_array(
    gray: "np.ndarray",
    *,
    feather_sigma: float = 1.5,
    morph_open: int = 3,
    offset: int = 0,
) -> Tuple["np.ndarray", int]:
    """Set the background of a grayscale image to white (in-memory).

    Uses Otsu thresholding to separate foreground (dark object) from
    background, then alpha-blends the object onto a white canvas with
    optional feathered edges.

    Args:
        gray: Grayscale or BGR image (converted automatically if 3-channel).
        feather_sigma: Gaussian sigma for soft-edge alpha blending.
            Set to 0 for hard edges.
        morph_open: Kernel size for morphological opening to clean the mask.
            Set to 0 to skip.
        offset: Adjust the Otsu threshold by this many levels (positive =
            stricter, keeps less background).

    Returns:
        Tuple of (whitened_gray_uint8, threshold_value).

    Raises:
        RuntimeError: If OpenCV is not available.
    """
    if not _CV2_AVAILABLE:
        raise RuntimeError("opencv-python is required for whiten_bg_array")

    if gray.ndim == 3:
        gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (0, 0), 1.0)

    # Otsu threshold — dark object on light background
    t, obj_mask = cv2.threshold(
        blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # Optional threshold offset
    if offset != 0:
        t2 = int(np.clip(t + offset, 0, 255))
        _, obj_mask = cv2.threshold(blur, t2, 255, cv2.THRESH_BINARY_INV)
        t = t2

    # Morphological opening to remove noise specks
    if morph_open and morph_open > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (morph_open, morph_open))
        obj_mask = cv2.morphologyEx(obj_mask, cv2.MORPH_OPEN, k)

    # Soft-edge alpha mask
    if feather_sigma > 0:
        soft = cv2.GaussianBlur(obj_mask, (0, 0), float(feather_sigma))
    else:
        soft = obj_mask
    alpha = soft.astype(np.float32) / 255.0

    # Blend: object pixels where mask is 1, white where mask is 0
    white_bg = np.full_like(gray, 255, dtype=np.uint8)
    out = (
        alpha * gray.astype(np.float32)
        + (1.0 - alpha) * white_bg.astype(np.float32)
    ).astype(np.uint8)

    logger.debug("Background whitened — Otsu threshold=%d", int(t))
    return out, int(t)


# ---------------------------------------------------------------------------
# File-level convenience API
# ---------------------------------------------------------------------------

def whiten_background(
    image_path: str,
    *,
    feather_sigma: float = 1.5,
    morph_open: int = 3,
    offset: int = 0,
) -> "np.ndarray":
    """Whiten the background of an image loaded from disk.

    This is the primary high-level API. It loads the image, applies
    background whitening, and returns the processed grayscale image.

    Args:
        image_path: Path to the input image file.
        feather_sigma: Gaussian sigma for soft-edge blending (0 = hard).
        morph_open: Morphological opening kernel size (0 = skip).
        offset: Otsu threshold adjustment.

    Returns:
        Whitened grayscale image as uint8 ndarray.

    Raises:
        FileNotFoundError: If the image file does not exist.
        RuntimeError: If OpenCV is not available.
    """
    if not _CV2_AVAILABLE:
        raise RuntimeError("opencv-python is required for whiten_background")

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Could not decode image: {path}")

    logger.info("Whitening background: %s", path)
    result, threshold = whiten_bg_array(
        img,
        feather_sigma=feather_sigma,
        morph_open=morph_open,
        offset=offset,
    )
    logger.info("Whitening complete — threshold=%d", threshold)
    return result
