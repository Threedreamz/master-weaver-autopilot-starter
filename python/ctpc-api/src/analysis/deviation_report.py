"""Deviation report generation — JSON + human-readable text."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class DeviationReport:
    """Structured deviation report matching the TypeScript interface."""

    reference_stl_path: str
    scan_stl_path: str
    min_deviation: float
    max_deviation: float
    avg_deviation: float
    std_deviation: float
    within_tolerance: bool
    tolerance_mm: float
    heatmap_data: Optional[list[float]] = None

    @classmethod
    def from_dict(cls, d: dict) -> DeviationReport:
        return cls(
            reference_stl_path=d["referenceStlPath"],
            scan_stl_path=d["scanStlPath"],
            min_deviation=d["minDeviation"],
            max_deviation=d["maxDeviation"],
            avg_deviation=d["avgDeviation"],
            std_deviation=d["stdDeviation"],
            within_tolerance=d["withinTolerance"],
            tolerance_mm=d["toleranceMm"],
            heatmap_data=d.get("heatmapData"),
        )

    def to_dict(self) -> dict:
        d = {
            "referenceStlPath": self.reference_stl_path,
            "scanStlPath": self.scan_stl_path,
            "minDeviation": self.min_deviation,
            "maxDeviation": self.max_deviation,
            "avgDeviation": self.avg_deviation,
            "stdDeviation": self.std_deviation,
            "withinTolerance": self.within_tolerance,
            "toleranceMm": self.tolerance_mm,
        }
        if self.heatmap_data is not None:
            d["heatmapData"] = self.heatmap_data
        return d


def write_report(report_data: dict, output_dir: str | Path) -> tuple[Path, Path]:
    """Write JSON and text reports to *output_dir*.

    Args:
        report_data: Dict as returned by ``compare_stl()``.
        output_dir: Directory to write reports into.

    Returns:
        Tuple of (json_path, txt_path).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()

    # -- JSON report (without heatmap for compact storage) -------------------
    json_report = {**report_data, "generatedAt": timestamp}
    # Store heatmap separately if large
    heatmap = json_report.pop("heatmapData", None)

    json_path = output_dir / "deviation-report.json"
    with open(json_path, "w") as f:
        json.dump(json_report, f, indent=2)
    logger.info("JSON report written: %s", json_path)

    # Write heatmap data separately if present
    if heatmap is not None:
        heatmap_path = output_dir / "heatmap-data.json"
        with open(heatmap_path, "w") as f:
            json.dump(heatmap, f)
        logger.info("Heatmap data written: %s", heatmap_path)

    # -- Text summary --------------------------------------------------------
    verdict = "PASS" if report_data.get("withinTolerance") else "FAIL"
    txt_path = output_dir / "deviation-report.txt"
    with open(txt_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("  Soll-Ist Deviation Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Generated:  {timestamp}\n")
        f.write(f"Reference:  {report_data.get('referenceStlPath', 'N/A')}\n")
        f.write(f"Scan:       {report_data.get('scanStlPath', 'N/A')}\n")
        f.write(f"Tolerance:  {report_data.get('toleranceMm', 0):.3f} mm\n\n")
        f.write("-" * 40 + "\n")
        f.write(f"  Min deviation:  {report_data.get('minDeviation', 0):.4f} mm\n")
        f.write(f"  Max deviation:  {report_data.get('maxDeviation', 0):.4f} mm\n")
        f.write(f"  Avg deviation:  {report_data.get('avgDeviation', 0):.4f} mm\n")
        f.write(f"  Std deviation:  {report_data.get('stdDeviation', 0):.4f} mm\n")
        f.write("-" * 40 + "\n\n")
        f.write(f"  VERDICT: {verdict}\n\n")
        f.write("=" * 60 + "\n")
    logger.info("Text report written: %s", txt_path)

    return json_path, txt_path
