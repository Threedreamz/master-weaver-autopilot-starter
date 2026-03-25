"""Scan folder management — creation, unique IDs, cleanup, disk checks."""

from __future__ import annotations

import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def generate_scan_id() -> str:
    """Return a unique scan identifier: ``YYYYMMDD-HHMMSS-<short-uuid>``."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    short = uuid.uuid4().hex[:8]
    return f"{ts}-{short}"


def make_scan_folder(base_path: str | Path, scan_id: str) -> Path:
    """Create ``<base_path>/scans/YYYY-MM-DD/<scan_id>/`` and return the path.

    Raises:
        OSError: If the directory cannot be created.
    """
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder = Path(base_path) / "scans" / date_str / scan_id
    folder.mkdir(parents=True, exist_ok=True)
    logger.info("Created scan folder: %s", folder)
    return folder


def disk_space_ok(path: str | Path, min_free_mb: float = 500) -> bool:
    """Return True if at least *min_free_mb* MB are free on the volume of *path*."""
    try:
        usage = shutil.disk_usage(str(path))
        free_mb = usage.free / (1024 * 1024)
        if free_mb < min_free_mb:
            logger.warning(
                "Low disk space at %s: %.1f MB free (minimum %.1f MB)",
                path,
                free_mb,
                min_free_mb,
            )
            return False
        return True
    except OSError:
        logger.exception("Cannot check disk space for %s", path)
        return False


def cleanup_old_scans(
    base_path: str | Path,
    max_age_days: int = 30,
    dry_run: bool = True,
) -> list[Path]:
    """Remove scan day-folders older than *max_age_days*.

    Returns the list of folders that were (or would be) deleted.
    """
    scans_dir = Path(base_path) / "scans"
    if not scans_dir.is_dir():
        return []

    cutoff = datetime.now(timezone.utc).date()
    removed: list[Path] = []

    for day_dir in sorted(scans_dir.iterdir()):
        if not day_dir.is_dir():
            continue
        try:
            dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
        except ValueError:
            continue
        age_days = (cutoff - dir_date).days
        if age_days > max_age_days:
            if dry_run:
                logger.info("[dry-run] Would remove %s (%d days old)", day_dir, age_days)
            else:
                shutil.rmtree(day_dir)
                logger.info("Removed %s (%d days old)", day_dir, age_days)
            removed.append(day_dir)

    return removed


def list_scan_folders(base_path: str | Path) -> list[dict]:
    """Return metadata dicts for all scan folders under *base_path*/scans/."""
    scans_dir = Path(base_path) / "scans"
    if not scans_dir.is_dir():
        return []

    results: list[dict] = []
    for day_dir in sorted(scans_dir.iterdir()):
        if not day_dir.is_dir():
            continue
        for scan_dir in sorted(day_dir.iterdir()):
            if not scan_dir.is_dir():
                continue
            stl_files = list(scan_dir.glob("*.stl"))
            results.append(
                {
                    "scan_id": scan_dir.name,
                    "date": day_dir.name,
                    "path": str(scan_dir),
                    "has_stl": len(stl_files) > 0,
                    "stl_files": [f.name for f in stl_files],
                    "size_mb": sum(f.stat().st_size for f in scan_dir.rglob("*") if f.is_file())
                    / (1024 * 1024),
                }
            )
    return results
