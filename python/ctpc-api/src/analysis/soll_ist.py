"""Soll-Ist STL comparison — compute point-to-surface deviations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np
from scipy.spatial import KDTree
from stl import mesh as stl_mesh

logger = logging.getLogger(__name__)


def _extract_vertices(stl_path: str | Path) -> np.ndarray:
    """Load an STL file and return unique vertices as an (N, 3) array."""
    m = stl_mesh.Mesh.from_file(str(stl_path))
    # m.vectors has shape (num_triangles, 3, 3) — 3 vertices per triangle
    vertices = m.vectors.reshape(-1, 3)
    # Deduplicate to reduce KDTree size
    unique = np.unique(vertices, axis=0)
    logger.debug("Loaded %s: %d triangles, %d unique vertices", stl_path, len(m.vectors), len(unique))
    return unique


def compare_stl(
    reference_path: str | Path,
    scan_path: str | Path,
    tolerance_mm: float = 0.1,
) -> dict:
    """Compare a scanned STL against a reference STL.

    Uses a KDTree for efficient nearest-neighbour distance computation.
    For each vertex in the scan mesh, finds the closest point on the
    reference mesh and computes the Euclidean distance.

    Args:
        reference_path: Path to the reference (Soll) STL file.
        scan_path: Path to the scanned (Ist) STL file.
        tolerance_mm: Maximum acceptable average deviation in mm.

    Returns:
        Dict matching the TypeScript ``DeviationReport`` interface::

            {
                "referenceStlPath": str,
                "scanStlPath": str,
                "minDeviation": float,
                "maxDeviation": float,
                "avgDeviation": float,
                "stdDeviation": float,
                "withinTolerance": bool,
                "toleranceMm": float,
                "heatmapData": list[float],
            }
    """
    reference_path = Path(reference_path)
    scan_path = Path(scan_path)

    if not reference_path.exists():
        raise FileNotFoundError(f"Reference STL not found: {reference_path}")
    if not scan_path.exists():
        raise FileNotFoundError(f"Scan STL not found: {scan_path}")

    logger.info("Comparing STLs: reference=%s  scan=%s  tolerance=%.3fmm", reference_path, scan_path, tolerance_mm)

    ref_verts = _extract_vertices(reference_path)
    scan_verts = _extract_vertices(scan_path)

    # Build KDTree from reference vertices
    tree = KDTree(ref_verts)

    # Query distances from each scan vertex to its nearest reference vertex
    distances, _ = tree.query(scan_verts)

    min_dev = float(np.min(distances))
    max_dev = float(np.max(distances))
    avg_dev = float(np.mean(distances))
    std_dev = float(np.std(distances))
    within = avg_dev <= tolerance_mm

    logger.info(
        "Deviation: min=%.4f  max=%.4f  avg=%.4f  std=%.4f  pass=%s",
        min_dev, max_dev, avg_dev, std_dev, within,
    )

    return {
        "referenceStlPath": str(reference_path),
        "scanStlPath": str(scan_path),
        "minDeviation": min_dev,
        "maxDeviation": max_dev,
        "avgDeviation": avg_dev,
        "stdDeviation": std_dev,
        "withinTolerance": within,
        "toleranceMm": tolerance_mm,
        "heatmapData": distances.tolist(),
    }
