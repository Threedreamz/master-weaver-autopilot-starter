"""Async scan state machine — orchestrates the full CT scan pipeline."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional, Protocol, runtime_checkable

from .folder_manager import disk_space_ok, generate_scan_id, make_scan_folder
from .states import ScanState
from .stl_export import export_stl
from .transitions import (
    ErrorSeverity,
    StatePolicy,
    get_policy,
    is_valid_transition,
    next_happy_state,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Controller protocol — injected for testability
# ---------------------------------------------------------------------------

@runtime_checkable
class ScanController(Protocol):
    """Interface that the WinWerth controller must satisfy."""

    def complete_profile_selection_sequence(self, profile_name: str) -> bool: ...
    def is_profile_selected(self, profile_name: str) -> bool: ...
    def click_tube_power_on(self) -> bool: ...
    def is_tube_on(self) -> bool: ...
    def activate_rotation(self) -> bool: ...
    def rotate_degrees(self, degrees: float) -> bool: ...
    def get_min_distances(self) -> dict: ...
    def set_green_box(self, boundaries: dict) -> bool: ...
    def run_error_correction(self) -> bool: ...
    def get_pixel_status(self) -> dict: ...
    def is_scan_complete(self) -> bool: ...
    def open_save_dialog(self) -> bool: ...
    def set_save_path(self, path: str) -> bool: ...
    def confirm_save(self) -> bool: ...
    def close_save_dialog(self) -> bool: ...


# ---------------------------------------------------------------------------
# Event callbacks
# ---------------------------------------------------------------------------

StateChangeCallback = Callable[[ScanState, ScanState, dict], Any]
ProgressCallback = Callable[[ScanState, float, str], Any]
ErrorCallback = Callable[[ScanState, Exception, bool], Any]


# ---------------------------------------------------------------------------
# Scan result
# ---------------------------------------------------------------------------

@dataclass
class ScanResult:
    """Result returned when a scan completes (or fails)."""

    job_id: str
    scan_id: str
    part_id: str
    profile_id: str
    state: ScanState
    stl_path: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    deviation_report: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# ScanMachine
# ---------------------------------------------------------------------------

class ScanMachine:
    """Async state machine that drives a CT scan from IDLE to DONE.

    Thread-safe singleton guard: only one scan can run at a time.

    Usage::

        machine = ScanMachine(controller, base_path="/data")
        machine.on_state_change = my_callback
        result = await machine.run_scan(job)
    """

    def __init__(
        self,
        controller: ScanController,
        base_path: str | Path = "/data",
    ) -> None:
        self._controller = controller
        self._base_path = Path(base_path)
        self._state = ScanState.IDLE
        self._lock = asyncio.Lock()
        self._running = False

        # Event callbacks (set externally)
        self.on_state_change: Optional[StateChangeCallback] = None
        self.on_progress: Optional[ProgressCallback] = None
        self.on_error: Optional[ErrorCallback] = None

    # -- Properties ----------------------------------------------------------

    @property
    def state(self) -> ScanState:
        return self._state

    @property
    def is_running(self) -> bool:
        return self._running

    # -- State management ----------------------------------------------------

    async def _set_state(self, new_state: ScanState, metadata: dict | None = None) -> None:
        old = self._state
        if not is_valid_transition(old, new_state):
            raise InvalidTransitionError(old, new_state)
        self._state = new_state
        logger.info("State: %s -> %s", old.value, new_state.value)
        if self.on_state_change:
            try:
                self.on_state_change(old, new_state, metadata or {})
            except Exception:
                logger.exception("on_state_change callback error")

    async def _emit_progress(self, progress: float, message: str = "") -> None:
        if self.on_progress:
            try:
                self.on_progress(self._state, progress, message)
            except Exception:
                logger.exception("on_progress callback error")

    async def _emit_error(self, exc: Exception, recoverable: bool) -> None:
        if self.on_error:
            try:
                self.on_error(self._state, exc, recoverable)
            except Exception:
                logger.exception("on_error callback error")

    # -- Main entry point ----------------------------------------------------

    async def run_scan(self, job: dict) -> ScanResult:
        """Execute the full scan pipeline for *job*.

        Args:
            job: Dict with keys ``profileId``, ``partId``, and optionally
                ``referenceStlPath`` and ``notes``.

        Returns:
            ScanResult with final state and output paths.

        Raises:
            ScanAlreadyRunningError: If another scan is in progress.
        """
        if self._lock.locked():
            raise ScanAlreadyRunningError()

        async with self._lock:
            self._running = True
            scan_id = generate_scan_id()
            profile_id = job.get("profileId", "")
            part_id = job.get("partId", "")
            profile_name = job.get("profileName", profile_id)
            reference_stl = job.get("referenceStlPath")

            result = ScanResult(
                job_id=f"job-{scan_id}",
                scan_id=scan_id,
                part_id=part_id,
                profile_id=profile_id,
                state=ScanState.IDLE,
                started_at=datetime.now(timezone.utc).isoformat(),
            )

            try:
                # Pre-flight
                if not disk_space_ok(self._base_path):
                    raise RuntimeError("Insufficient disk space")

                scan_folder = make_scan_folder(self._base_path, scan_id)

                # -- Pipeline states -----------------------------------------
                await self._run_state(ScanState.PROFILE_SELECT, self._do_profile_select, profile_name)
                await self._run_state(ScanState.TUBE_ON, self._do_tube_on)
                await self._run_state(ScanState.ROTATE_PREVIEW, self._do_rotate_preview)
                await self._run_state(ScanState.GREEN_BOX, self._do_green_box)
                await self._run_state(ScanState.ERROR_CORRECT, self._do_error_correct)
                await self._run_state(ScanState.SCANNING, self._do_scanning)
                await self._run_state(ScanState.WAIT_COMPLETE, self._do_wait_complete)

                # Export
                stl_path = await self._run_state(
                    ScanState.EXPORT_STL, self._do_export_stl, scan_id, scan_folder
                )
                result.stl_path = str(stl_path) if stl_path else None

                # Analyse (optional)
                if reference_stl:
                    deviation = await self._run_state(
                        ScanState.ANALYSE, self._do_analyse, stl_path, reference_stl, scan_folder
                    )
                    result.deviation_report = deviation
                else:
                    # Skip analysis — go straight to DONE
                    await self._set_state(ScanState.ANALYSE)
                    await self._emit_progress(1.0, "No reference STL — skipping analysis")

                await self._set_state(ScanState.DONE)
                result.state = ScanState.DONE
                result.completed_at = datetime.now(timezone.utc).isoformat()
                logger.info("Scan %s completed successfully", scan_id)

            except Exception as exc:
                logger.exception("Scan %s failed in state %s", scan_id, self._state.value)
                try:
                    await self._set_state(ScanState.ERROR, {"error": str(exc)})
                except InvalidTransitionError:
                    self._state = ScanState.ERROR  # force
                result.state = ScanState.ERROR
                result.error = str(exc)
                result.completed_at = datetime.now(timezone.utc).isoformat()
                await self._emit_error(exc, recoverable=False)

            finally:
                # Reset to IDLE
                self._state = ScanState.IDLE
                self._running = False

            return result

    # -- State runner with retry/timeout -------------------------------------

    async def _run_state(self, state: ScanState, handler, *args) -> Any:
        """Transition to *state*, execute *handler* with retry/timeout policy."""
        await self._set_state(state)
        policy = get_policy(state)

        last_exc: Exception | None = None
        for attempt in range(policy.max_retries + 1):
            try:
                if policy.timeout_s > 0:
                    return await asyncio.wait_for(
                        handler(*args), timeout=policy.timeout_s
                    )
                else:
                    return await handler(*args)
            except asyncio.TimeoutError:
                last_exc = TimeoutError(
                    f"State {state.value} timed out after {policy.timeout_s}s "
                    f"(attempt {attempt + 1}/{policy.max_retries + 1})"
                )
                logger.warning(str(last_exc))
                await self._emit_error(last_exc, recoverable=attempt < policy.max_retries)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "State %s failed (attempt %d/%d): %s",
                    state.value,
                    attempt + 1,
                    policy.max_retries + 1,
                    exc,
                )
                await self._emit_error(exc, recoverable=attempt < policy.max_retries)

            if attempt < policy.max_retries:
                backoff = policy.backoff_s * (policy.backoff_factor ** attempt)
                logger.info("Retrying %s in %.1fs", state.value, backoff)
                await asyncio.sleep(backoff)

        raise last_exc or RuntimeError(f"State {state.value} failed")

    # -- State implementations -----------------------------------------------

    async def _do_profile_select(self, profile_name: str) -> None:
        await self._emit_progress(0.0, f"Selecting profile: {profile_name}")
        ok = await asyncio.to_thread(
            self._controller.complete_profile_selection_sequence, profile_name
        )
        if not ok:
            raise RuntimeError(f"Profile selection failed: {profile_name}")
        # Verify
        selected = await asyncio.to_thread(
            self._controller.is_profile_selected, profile_name
        )
        if not selected:
            raise RuntimeError(f"Profile not verified after selection: {profile_name}")
        await self._emit_progress(1.0, "Profile selected")

    async def _do_tube_on(self) -> None:
        await self._emit_progress(0.0, "Powering on X-ray tube")
        ok = await asyncio.to_thread(self._controller.click_tube_power_on)
        if not ok:
            raise RuntimeError("Failed to power on tube")

        # Poll for tube ready
        for i in range(60):
            is_on = await asyncio.to_thread(self._controller.is_tube_on)
            if is_on:
                await self._emit_progress(1.0, "Tube powered on")
                return
            await self._emit_progress(i / 60, "Waiting for tube...")
            await asyncio.sleep(1.0)

        raise RuntimeError("Tube did not reach ready state")

    async def _do_rotate_preview(self) -> None:
        await self._emit_progress(0.0, "Starting 360° preview rotation")
        ok = await asyncio.to_thread(self._controller.activate_rotation)
        if not ok:
            raise RuntimeError("Failed to activate rotation")

        ok = await asyncio.to_thread(self._controller.rotate_degrees, 360.0)
        if not ok:
            raise RuntimeError("360° rotation failed")

        await self._emit_progress(0.8, "Capturing min distances")
        distances = await asyncio.to_thread(self._controller.get_min_distances)
        if not distances:
            raise RuntimeError("Failed to capture min distances")

        # Store boundaries for GREEN_BOX state
        self._last_distances = distances
        await self._emit_progress(1.0, "Preview rotation complete")

    async def _do_green_box(self) -> None:
        await self._emit_progress(0.0, "Setting selection box from boundaries")
        distances = getattr(self, "_last_distances", None)
        if not distances:
            raise RuntimeError("No boundary data from rotation preview")

        ok = await asyncio.to_thread(self._controller.set_green_box, distances)
        if not ok:
            raise RuntimeError("Failed to set green selection box")
        await self._emit_progress(1.0, "Green box set")

    async def _do_error_correct(self) -> None:
        await self._emit_progress(0.0, "Running voltage/ampere correction")
        max_iterations = 10
        for i in range(max_iterations):
            await self._emit_progress(
                i / max_iterations,
                f"Correction iteration {i + 1}/{max_iterations}",
            )
            ok = await asyncio.to_thread(self._controller.run_error_correction)
            if ok:
                await self._emit_progress(1.0, "Error correction complete")
                return
            await asyncio.sleep(1.0)

        raise RuntimeError(f"Error correction did not converge after {max_iterations} iterations")

    async def _do_scanning(self) -> None:
        await self._emit_progress(0.0, "Scan in progress")
        poll_interval = 2.0
        elapsed = 0.0
        timeout = get_policy(ScanState.SCANNING).timeout_s

        while elapsed < timeout:
            status = await asyncio.to_thread(self._controller.get_pixel_status)
            progress = status.get("progress", 0.0) if status else 0.0
            await self._emit_progress(progress, f"Scanning... {progress * 100:.0f}%")

            if status and status.get("complete", False):
                await self._emit_progress(1.0, "Scan data acquisition complete")
                return

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise RuntimeError("Scan timed out waiting for completion")

    async def _do_wait_complete(self) -> None:
        await self._emit_progress(0.0, "Waiting for scan finalization")
        poll_interval = 1.0
        elapsed = 0.0
        timeout = get_policy(ScanState.WAIT_COMPLETE).timeout_s

        while elapsed < timeout:
            done = await asyncio.to_thread(self._controller.is_scan_complete)
            if done:
                await self._emit_progress(1.0, "Scan complete")
                return
            await self._emit_progress(elapsed / timeout, "Finalizing...")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise RuntimeError("Scan finalization timed out")

    async def _do_export_stl(self, scan_id: str, scan_folder: Path) -> Path:
        await self._emit_progress(0.0, "Exporting STL file")
        stl_path = await export_stl(
            self._controller, scan_id, scan_folder
        )
        await self._emit_progress(1.0, f"STL exported: {stl_path}")
        return stl_path

    async def _do_analyse(
        self, stl_path: Path, reference_stl: str, scan_folder: Path
    ) -> dict:
        await self._emit_progress(0.0, "Running Soll-Ist analysis")

        # Import here to avoid hard dependency when analysis is not needed
        from ..analysis.soll_ist import compare_stl
        from ..analysis.deviation_report import write_report

        report = await asyncio.to_thread(
            compare_stl, reference_stl, str(stl_path)
        )
        await self._emit_progress(0.8, "Writing deviation report")
        await asyncio.to_thread(write_report, report, scan_folder)
        await self._emit_progress(1.0, "Analysis complete")
        return report


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed."""

    def __init__(self, from_state: ScanState, to_state: ScanState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition: {from_state.value} -> {to_state.value}")


class ScanAlreadyRunningError(Exception):
    """Raised when a scan is attempted while another is in progress."""

    def __init__(self) -> None:
        super().__init__("A scan is already in progress")
