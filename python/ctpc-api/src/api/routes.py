"""
REST API routes for CT-PC control.

Scan endpoints are driven by the ScanMachine state machine from
``orchestrator.scan_machine``.  All scan state transitions, progress
updates, and errors are broadcast to connected WebSocket clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from pydantic import BaseModel

from ..orchestrator.scan_machine import ScanMachine, ScanAlreadyRunningError, ScanResult
from ..orchestrator.states import ScanState
from ..queue.task_queue import ScanTaskQueue
from ..notifications.email_notify import EmailNotifier
from ..timetracking.tracker import TimeTracker
from ..analysis.soll_ist import compare_stl

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Task Queue & Email singletons
# ---------------------------------------------------------------------------
task_queue = ScanTaskQueue()
email_notifier = EmailNotifier()

# ---------------------------------------------------------------------------
# In-memory scan store (replaced by real DB later)
# ---------------------------------------------------------------------------
_scans: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class ScanStartRequest(BaseModel):
    profileId: str
    partId: str
    profileName: Optional[str] = None
    referenceStlPath: Optional[str] = None
    notes: Optional[str] = None


class ScanRecord(BaseModel):
    id: str
    jobId: str = ""
    profileId: str
    partId: str
    state: str = "IDLE"  # matches ScanState enum values
    startedAt: str
    completedAt: Optional[str] = None
    stlPath: Optional[str] = None
    deviationReport: Optional[dict] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_controller(request: Request):
    ctrl = getattr(request.app.state, "controller", None)
    if ctrl is None:
        raise HTTPException(status_code=503, detail="Controller not initialised")
    return ctrl


def _get_scan_machine(request: Request) -> Optional[ScanMachine]:
    """Return the active ScanMachine instance from app.state, or None."""
    return getattr(request.app.state, "scan_machine", None)


def _scan_result_to_record(result: ScanResult) -> Dict[str, Any]:
    """Convert a ScanResult dataclass into the dict format stored in _scans."""
    return {
        "id": result.scan_id,
        "jobId": result.job_id,
        "profileId": result.profile_id,
        "partId": result.part_id,
        "state": result.state.value if isinstance(result.state, ScanState) else str(result.state),
        "startedAt": result.started_at or "",
        "completedAt": result.completed_at,
        "stlPath": result.stl_path,
        "deviationReport": result.deviation_report,
        "error": result.error,
    }


# ---------------------------------------------------------------------------
# ScanMachine WebSocket callback wiring
# ---------------------------------------------------------------------------

def _wire_scan_callbacks(machine: ScanMachine, loop: asyncio.AbstractEventLoop) -> None:
    """Register callbacks on *machine* that broadcast events via WebSocket.

    The callbacks are plain (non-async) functions because ``ScanMachine``
    invokes them synchronously.  We use ``asyncio.run_coroutine_threadsafe``
    to schedule the actual ``broadcast()`` call on the running event loop.
    """
    from .ws import broadcast

    def _on_state_change(old: ScanState, new: ScanState, meta: dict) -> None:
        msg = {
            "type": "scan.state_change",
            "oldState": old.value,
            "state": new.value,
            "meta": meta,
        }
        asyncio.run_coroutine_threadsafe(broadcast(msg), loop)

    def _on_progress(state: ScanState, pct: float, message: str) -> None:
        msg = {
            "type": "scan.progress",
            "state": state.value,
            "progress": round(pct, 4),
            "message": message,
        }
        asyncio.run_coroutine_threadsafe(broadcast(msg), loop)

    def _on_error(state: ScanState, exc: Exception, recoverable: bool) -> None:
        msg = {
            "type": "scan.error",
            "state": state.value,
            "error": str(exc),
            "recoverable": recoverable,
        }
        asyncio.run_coroutine_threadsafe(broadcast(msg), loop)

    machine.on_state_change = _on_state_change
    machine.on_progress = _on_progress
    machine.on_error = _on_error


# ---------------------------------------------------------------------------
# Background task: run the full scan pipeline
# ---------------------------------------------------------------------------

async def _run_scan_pipeline(
    machine: ScanMachine,
    job: dict,
    app_state: Any,
) -> None:
    """Execute ScanMachine.run_scan and persist the result."""
    from .ws import broadcast

    try:
        result: ScanResult = await machine.run_scan(job)
    except ScanAlreadyRunningError:
        logger.warning("Scan pipeline rejected — another scan is already running")
        return
    except Exception as exc:
        logger.exception("Scan pipeline crashed unexpectedly")
        await broadcast({
            "type": "scan.error",
            "state": "ERROR",
            "error": str(exc),
            "recoverable": False,
        })
        return

    # Persist to in-memory store
    record = _scan_result_to_record(result)
    _scans[result.scan_id] = record

    # Broadcast completion or error
    if result.state == ScanState.DONE:
        await broadcast({
            "type": "scan.complete",
            "scanId": result.scan_id,
            "jobId": result.job_id,
            "stlPath": result.stl_path,
            "deviationReport": result.deviation_report,
        })
    else:
        await broadcast({
            "type": "scan.state_change",
            "state": result.state.value if isinstance(result.state, ScanState) else str(result.state),
            "scanId": result.scan_id,
            "error": result.error,
        })

    # Clear active machine reference
    app_state.scan_machine = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "ctpc-api",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


@router.get("/status")
async def status(request: Request):
    ctrl = _get_controller(request)
    system_status = ctrl.get_system_status()

    machine = _get_scan_machine(request)
    scan_state = machine.state.value if machine else ScanState.IDLE.value

    return {
        "mock_mode": ctrl.mock_mode,
        "system": system_status,
        "scan_state": scan_state,
        "scan_running": machine.is_running if machine else False,
        "active_scans": 1 if (machine and machine.is_running) else 0,
        "total_scans": len(_scans),
    }


@router.get("/profiles")
async def list_profiles_simple(request: Request):
    ctrl = _get_controller(request)
    profiles = ctrl.get_available_profiles()
    return {"profiles": profiles}


@router.post("/profiles/{name}/select")
async def select_profile(name: str, request: Request):
    from .ws import broadcast

    ctrl = _get_controller(request)
    success = ctrl.complete_profile_selection_sequence(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to select profile '{name}'")

    await broadcast({
        "type": "system.status",
        "event": "profile_selected",
        "profile": name,
    })

    return {"selected": name, "success": True}


# ---------------------------------------------------------------------------
# Profile CRUD — JSON persistence
# ---------------------------------------------------------------------------
_profiles_file = Path("data/profiles.json")
_profiles_lock = threading.Lock()


class ProfileCreateRequest(BaseModel):
    name: str
    magnification: str  # "125L", "100L", "50L"
    voltage: Optional[float] = None
    ampere: Optional[float] = None
    rotationDegrees: float = 360.0
    description: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    magnification: Optional[str] = None
    voltage: Optional[float] = None
    ampere: Optional[float] = None
    rotationDegrees: Optional[float] = None
    description: Optional[str] = None


def _load_profiles() -> Dict[str, Any]:
    """Load profiles from disk. Returns dict keyed by profile ID."""
    if not _profiles_file.exists():
        return {}
    try:
        with open(_profiles_file, "r") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load profiles from disk: %s", exc)
        return {}


def _save_profiles(profiles: Dict[str, Any]) -> None:
    """Persist profiles dict to disk as JSON."""
    try:
        _profiles_file.parent.mkdir(parents=True, exist_ok=True)
        with open(_profiles_file, "w") as f:
            json.dump(profiles, f, indent=2)
    except Exception as exc:
        logger.error("Failed to save profiles to disk: %s", exc)


@router.get("/profiles")
async def list_profiles(request: Request):
    """Return stored profiles with full data (merged with controller profiles)."""
    ctrl = _get_controller(request)
    controller_profiles = ctrl.get_available_profiles()

    with _profiles_lock:
        stored = _load_profiles()

    # Build response: stored profiles first, then controller-only profiles
    result = list(stored.values())

    # Add controller profiles that aren't already stored
    stored_names = {p.get("name") for p in stored.values()}
    for cp in controller_profiles:
        if cp["name"] not in stored_names:
            result.append({
                "id": cp["name"],
                "name": cp["name"],
                "magnification": cp["name"],
                "voltage": None,
                "ampere": None,
                "rotationDegrees": 360.0,
                "description": None,
                "createdAt": None,
                "updatedAt": None,
            })

    return {"profiles": result}


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a single profile by ID."""
    with _profiles_lock:
        stored = _load_profiles()

    profile = stored.get(profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
    return profile


@router.post("/profiles", status_code=201)
async def create_profile(body: ProfileCreateRequest):
    """Create a new profile with auto-generated ID and timestamps."""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    profile_id = str(uuid.uuid4())[:8]

    profile = {
        "id": profile_id,
        "name": body.name,
        "magnification": body.magnification,
        "voltage": body.voltage,
        "ampere": body.ampere,
        "rotationDegrees": body.rotationDegrees,
        "description": body.description,
        "createdAt": now,
        "updatedAt": now,
    }

    with _profiles_lock:
        stored = _load_profiles()
        stored[profile_id] = profile
        _save_profiles(stored)

    return profile


@router.patch("/profiles/{profile_id}")
async def update_profile(profile_id: str, body: ProfileUpdateRequest):
    """Update profile fields (partial update)."""
    with _profiles_lock:
        stored = _load_profiles()
        profile = stored.get(profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

        updates = body.model_dump(exclude_unset=True)
        for key, value in updates.items():
            profile[key] = value
        profile["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        stored[profile_id] = profile
        _save_profiles(stored)

    return profile


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile by ID."""
    with _profiles_lock:
        stored = _load_profiles()
        if profile_id not in stored:
            raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
        del stored[profile_id]
        _save_profiles(stored)

    return {"deleted": profile_id}


# ---------------------------------------------------------------------------
# Analysis / Soll-Ist endpoints
# ---------------------------------------------------------------------------
_references_dir = Path("data/references")


class AnalysisRequest(BaseModel):
    scanStlPath: str
    referenceStlPath: str
    toleranceMm: float = 0.1


@router.post("/analysis/upload-reference")
async def upload_reference(file: UploadFile = File(...)):
    """Upload a reference STL file for Soll-Ist comparison."""
    _references_dir.mkdir(parents=True, exist_ok=True)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Sanitise filename — keep only the basename
    safe_name = Path(file.filename).name
    dest = _references_dir / safe_name

    try:
        contents = await file.read()
        with open(dest, "wb") as f:
            f.write(contents)
    except Exception as exc:
        logger.error("Failed to save reference file: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {exc}")

    logger.info("Reference STL uploaded: %s (%d bytes)", dest, len(contents))
    return {"path": str(dest), "filename": safe_name, "size": len(contents)}


@router.post("/analysis/compare")
async def analysis_compare(body: AnalysisRequest):
    """Run Soll-Ist STL comparison using KDTree deviation analysis."""
    try:
        report = compare_stl(
            reference_path=body.referenceStlPath,
            scan_path=body.scanStlPath,
            tolerance_mm=body.toleranceMm,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Analysis comparison failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    return {"report": report}


@router.get("/analysis/references")
async def list_references():
    """List all uploaded reference STL files."""
    _references_dir.mkdir(parents=True, exist_ok=True)

    files = []
    for p in sorted(_references_dir.iterdir()):
        if p.is_file():
            files.append({
                "filename": p.name,
                "path": str(p),
                "size": p.stat().st_size,
            })

    return {"references": files, "count": len(files)}


@router.delete("/analysis/references/{filename}")
async def delete_reference(filename: str):
    """Delete a reference STL file."""
    # Prevent path traversal
    safe_name = Path(filename).name
    target = _references_dir / safe_name

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Reference file '{safe_name}' not found")

    target.unlink()
    logger.info("Reference STL deleted: %s", target)
    return {"deleted": safe_name}


# ---------------------------------------------------------------------------
# Scan start / stop — driven by ScanMachine
# ---------------------------------------------------------------------------

@router.post("/scan/start")
async def scan_start(body: ScanStartRequest, request: Request):
    """Start a CT scan using the ScanMachine state machine.

    Only one scan can run at a time.  The scan executes as a background
    task; this endpoint returns immediately with the initial scan record.
    All state transitions are broadcast via WebSocket.
    """
    from .ws import broadcast

    ctrl = _get_controller(request)

    # Reject if a scan is already running
    existing = _get_scan_machine(request)
    if existing and existing.is_running:
        raise HTTPException(status_code=409, detail="A scan is already in progress")

    # Reset mock scan state so progress starts from 0
    ctrl.reset_mock_scan_state()

    # Create the ScanMachine with the controller
    data_path = getattr(request.app.state, "scan_data_path", Path("data"))
    machine = ScanMachine(controller=ctrl, base_path=data_path)

    # Wire WebSocket broadcast callbacks
    loop = asyncio.get_running_loop()
    _wire_scan_callbacks(machine, loop)

    # Store on app.state (singleton — only 1 scan at a time)
    request.app.state.scan_machine = machine

    # Build the job dict for ScanMachine.run_scan
    job = {
        "profileId": body.profileId,
        "partId": body.partId,
        "profileName": body.profileName or body.profileId,
        "referenceStlPath": body.referenceStlPath,
        "notes": body.notes,
    }

    # Create preliminary scan record for immediate response
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    preliminary_id = str(uuid.uuid4())[:8]
    record: Dict[str, Any] = {
        "id": preliminary_id,
        "jobId": f"job-{preliminary_id}",
        "profileId": body.profileId,
        "partId": body.partId,
        "state": ScanState.PROFILE_SELECT.value,
        "startedAt": now,
        "completedAt": None,
        "stlPath": None,
        "deviationReport": None,
        "error": None,
    }
    _scans[preliminary_id] = record

    # Broadcast scan started
    await broadcast({
        "type": "scan.state_change",
        "state": ScanState.PROFILE_SELECT.value,
        "oldState": ScanState.IDLE.value,
        "scanId": preliminary_id,
        "profileId": body.profileId,
        "partId": body.partId,
    })

    # Launch the full pipeline as a background task
    asyncio.create_task(_run_scan_pipeline(machine, job, request.app.state))

    return {"scan": record}


@router.post("/scan/stop")
async def scan_stop(request: Request):
    """Stop the currently running scan.

    Cancels the active ScanMachine task and marks all in-progress scan
    records as stopped.  Broadcasts the state change via WebSocket.
    """
    from .ws import broadcast

    machine = _get_scan_machine(request)

    # Cancel the background task if the machine is running
    if machine and machine.is_running:
        # Force the machine into ERROR -> IDLE by setting state directly.
        # The background task will catch the resulting exception on the
        # next await and clean up.
        machine._running = False
        machine._state = ScanState.ERROR
        logger.info("ScanMachine forcefully stopped")

    # Mark all in-progress scan records as stopped
    stopped = []
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for scan_id, record in _scans.items():
        state = record.get("state", "")
        if state not in (ScanState.DONE.value, ScanState.ERROR.value, ScanState.IDLE.value, "stopped"):
            record["state"] = "stopped"
            record["completedAt"] = now
            stopped.append(scan_id)

    # Clear active machine
    request.app.state.scan_machine = None

    await broadcast({
        "type": "scan.state_change",
        "state": ScanState.IDLE.value,
        "event": "scan_stopped",
        "stoppedScans": stopped,
    })

    return {"stopped": stopped, "count": len(stopped)}


@router.get("/scan/state")
async def scan_state(request: Request):
    """Return the current ScanMachine state (or IDLE if no scan is active)."""
    machine = _get_scan_machine(request)
    if machine:
        return {
            "state": machine.state.value,
            "running": machine.is_running,
        }
    return {
        "state": ScanState.IDLE.value,
        "running": False,
    }


@router.post("/stl/export")
async def stl_export(request: Request):
    """Trigger a manual STL export via the controller save sequence."""
    from .ws import broadcast

    ctrl = _get_controller(request)
    success = ctrl.complete_save_sequence()
    if not success:
        raise HTTPException(status_code=500, detail="STL export sequence failed")

    await broadcast({
        "type": "scan.complete",
        "event": "stl_export",
        "success": True,
        "message": "STL export initiated",
    })

    return {"success": True, "message": "STL export initiated"}


@router.get("/scans")
async def list_scans():
    """List all scan records in the ScanResult-compatible format."""
    return {"scans": list(_scans.values()), "total": len(_scans)}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
    """Get a single scan record in the ScanResult-compatible format."""
    record = _scans.get(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found")
    return {"scan": record}


# ---------------------------------------------------------------------------
# Discovery endpoints
# ---------------------------------------------------------------------------

def _get_scanner(request: Request):
    scanner = getattr(request.app.state, "network_scanner", None)
    if scanner is None:
        raise HTTPException(status_code=503, detail="Network scanner not initialised")
    return scanner


@router.get("/discovery/nodes")
async def discovery_nodes(request: Request):
    """Return all currently discovered autopilot nodes (from cache)."""
    scanner = _get_scanner(request)
    nodes = scanner.get_all_cached()
    return {
        "nodes": [n.to_dict() for n in nodes],
        "count": len(nodes),
    }


@router.post("/discovery/scan")
async def discovery_scan(request: Request):
    """Trigger a manual network scan and return discovered nodes."""
    scanner = _get_scanner(request)
    nodes = await scanner.discover_nodes()
    return {
        "nodes": [n.to_dict() for n in nodes],
        "count": len(nodes),
        "message": "Scan complete",
    }


@router.get("/discovery/node/{node_type}")
async def discovery_node(node_type: str, request: Request):
    """Look up a specific node by type (pi, ct, ipad, health)."""
    scanner = _get_scanner(request)
    node = scanner.get_node(node_type)
    if node is None:
        raise HTTPException(status_code=404, detail=f"No node of type '{node_type}' discovered")
    return {"node": node.to_dict()}


# ---------------------------------------------------------------------------
# Task Queue — replaces Trello board
# ---------------------------------------------------------------------------

class QueueAddRequest(BaseModel):
    part_name: str
    profile_name: str
    priority: int = 0


@router.get("/queue")
async def queue_list():
    """List all queued tasks (sorted by priority desc, then FIFO)."""
    tasks = task_queue.get_queue()
    return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}


@router.post("/queue", status_code=201)
async def queue_add(body: QueueAddRequest):
    """Add a new scan task to the queue."""
    from .ws import broadcast

    task = task_queue.add_task(
        part_name=body.part_name,
        profile_name=body.profile_name,
        priority=body.priority,
    )

    await broadcast({
        "type": "scan.progress",
        "event": "queue_task_added",
        "task": task.to_dict(),
        "queueLength": len(task_queue.get_queue()),
    })

    return {"task": task.to_dict()}


@router.get("/queue/active")
async def queue_active():
    """Get the currently active (running) task, if any."""
    task = task_queue.get_active()
    if task is None:
        return {"task": None, "message": "Kein aktiver Auftrag"}
    return {"task": task.to_dict()}


@router.get("/queue/stats")
async def queue_stats():
    """Queue statistics: totals, avg duration, etc."""
    stats = task_queue.get_stats()
    return {"stats": stats.to_dict()}


@router.get("/queue/history")
async def queue_history(limit: int = 50):
    """Completed, failed, and cancelled tasks (newest first)."""
    tasks = task_queue.get_history(limit=limit)
    return {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}


@router.post("/queue/{task_id}/cancel")
async def queue_cancel(task_id: str):
    """Cancel a queued task."""
    try:
        task = task_queue.cancel_task(task_id)
        return {"task": task.to_dict()}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/queue/{task_id}")
async def queue_delete(task_id: str):
    """Remove a completed/failed/cancelled task from history."""
    try:
        task_queue.delete_task(task_id)
        return {"deleted": task_id}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Zeiterfassung — Worker Login/Logout + TimeLogs
# ---------------------------------------------------------------------------

def _get_tracker(request: Request) -> TimeTracker:
    tracker = getattr(request.app.state, "time_tracker", None)
    if tracker is None:
        raise HTTPException(status_code=503, detail="TimeTracker not initialised")
    return tracker


class WorkerCreateRequest(BaseModel):
    name: str


@router.get("/workers")
async def workers_list(request: Request):
    """Alle Mitarbeiter auflisten."""
    tracker = _get_tracker(request)
    workers = tracker.get_workers()
    return {"workers": [w.to_dict() for w in workers], "count": len(workers)}


@router.post("/workers", status_code=201)
async def workers_create(body: WorkerCreateRequest, request: Request):
    """Neuen Mitarbeiter anlegen."""
    tracker = _get_tracker(request)
    worker = tracker.add_worker(body.name)
    return {"worker": worker.to_dict()}


@router.delete("/workers/{worker_id}")
async def workers_delete(worker_id: str, request: Request):
    """Mitarbeiter entfernen."""
    tracker = _get_tracker(request)
    success = tracker.remove_worker(worker_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' nicht gefunden")
    return {"deleted": worker_id}


@router.get("/workers/active")
async def workers_active(request: Request):
    """Aktuell angemeldeten Worker abfragen."""
    tracker = _get_tracker(request)
    active = tracker.get_active_worker()
    if active is None:
        return {"worker": None, "message": "Kein Mitarbeiter angemeldet"}
    return {"worker": active.to_dict()}


@router.post("/workers/{worker_id}/login")
async def workers_login(worker_id: str, request: Request):
    """Worker anmelden (vorheriger wird automatisch abgemeldet)."""
    from .ws import broadcast

    tracker = _get_tracker(request)
    try:
        log = tracker.login_worker(worker_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' nicht gefunden")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # WebSocket-Broadcast: Login-Event
    await broadcast({
        "type": "timetracking",
        "event": "worker_login",
        "worker_id": worker_id,
        "worker_name": log.worker_name,
        "log": log.to_dict(),
    })

    return {"log": log.to_dict()}


@router.post("/workers/{worker_id}/logout")
async def workers_logout(worker_id: str, request: Request):
    """Worker abmelden."""
    from .ws import broadcast

    tracker = _get_tracker(request)
    try:
        log = tracker.logout_worker(worker_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Worker '{worker_id}' nicht gefunden")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # WebSocket-Broadcast: Logout-Event
    await broadcast({
        "type": "timetracking",
        "event": "worker_logout",
        "worker_id": worker_id,
        "worker_name": log.worker_name,
        "log": log.to_dict(),
    })

    return {"log": log.to_dict()}


@router.get("/timelogs")
async def timelogs_list(
    request: Request,
    date: Optional[str] = None,
    worker_id: Optional[str] = None,
):
    """Zeiteinträge abfragen (optional nach Datum/Worker gefiltert)."""
    tracker = _get_tracker(request)
    logs = tracker.get_timelogs(date=date, worker_id=worker_id)
    return {"logs": [tl.to_dict() for tl in logs], "count": len(logs)}


@router.get("/timelogs/export")
async def timelogs_export(
    request: Request,
    date: Optional[str] = None,
):
    """Zeiteinträge als CSV exportieren."""
    from fastapi.responses import Response

    tracker = _get_tracker(request)
    csv_data = tracker.export_csv(date=date)

    filename = f"timelogs_{date or 'all'}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/timelogs/stats")
async def timelogs_stats(request: Request):
    """Tagesstatistik der Zeiterfassung."""
    tracker = _get_tracker(request)
    stats = tracker.get_stats()
    return {"stats": stats.to_dict()}
