"""STL export — navigate WinWerth save dialog, write file, verify."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Protocol

from .folder_manager import generate_scan_id, make_scan_folder

logger = logging.getLogger(__name__)


class ControllerProtocol(Protocol):
    """Minimal interface the STL exporter needs from the WinWerth controller."""

    def open_save_dialog(self) -> bool: ...
    def set_save_path(self, path: str) -> bool: ...
    def confirm_save(self) -> bool: ...
    def close_save_dialog(self) -> bool: ...


async def export_stl(
    controller: ControllerProtocol,
    scan_id: str,
    output_dir: str | Path,
    *,
    poll_interval: float = 0.5,
    max_wait_s: float = 30.0,
) -> Path:
    """Drive the WinWerth save dialog to export an STL file.

    Args:
        controller: WinWerth controller with save-dialog methods.
        scan_id: Unique identifier for this scan.
        output_dir: Directory where the STL will be written.
        poll_interval: Seconds between existence checks.
        max_wait_s: Maximum seconds to wait for the file to appear.

    Returns:
        Path to the exported STL file.

    Raises:
        RuntimeError: If the save dialog cannot be opened or the file
            does not appear within *max_wait_s*.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stl_path = output_dir / f"{scan_id}.stl"

    logger.info("Exporting STL to %s", stl_path)

    # 1. Open the save dialog (blocking WinWerth call)
    ok = await asyncio.to_thread(controller.open_save_dialog)
    if not ok:
        raise RuntimeError("Failed to open WinWerth save dialog")

    # 2. Set the save path
    ok = await asyncio.to_thread(controller.set_save_path, str(stl_path))
    if not ok:
        await asyncio.to_thread(controller.close_save_dialog)
        raise RuntimeError(f"Failed to set save path: {stl_path}")

    # 3. Confirm save
    ok = await asyncio.to_thread(controller.confirm_save)
    if not ok:
        await asyncio.to_thread(controller.close_save_dialog)
        raise RuntimeError("Failed to confirm STL save")

    # 4. Poll for the file to appear on disk
    elapsed = 0.0
    while elapsed < max_wait_s:
        if stl_path.exists() and stl_path.stat().st_size > 0:
            logger.info("STL exported successfully: %s (%d bytes)", stl_path, stl_path.stat().st_size)
            return stl_path
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    raise RuntimeError(f"STL file did not appear within {max_wait_s}s: {stl_path}")


async def export_stl_full(
    controller: ControllerProtocol,
    base_path: str | Path,
    scan_id: str | None = None,
) -> tuple[str, Path]:
    """High-level export: generate ID, create folder, export STL.

    Returns:
        Tuple of (scan_id, stl_path).
    """
    if scan_id is None:
        scan_id = generate_scan_id()

    folder = make_scan_folder(base_path, scan_id)
    stl_path = await export_stl(controller, scan_id, folder)
    return scan_id, stl_path
