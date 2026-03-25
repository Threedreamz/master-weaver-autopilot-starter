"""
REST API routes for CT-PC control.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..queue.task_queue import ScanTaskQueue
from ..notifications.email_notify import EmailNotifier
from ..timetracking.tracker import TimeTracker

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


class ScanRecord(BaseModel):
    id: str
    profileId: str
    partId: str
    status: str  # pending | scanning | completed | failed | stopped
    startedAt: str
    completedAt: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_controller(request: Request):
    ctrl = getattr(request.app.state, "controller", None)
    if ctrl is None:
        raise HTTPException(status_code=503, detail="Controller not initialised")
    return ctrl


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
    return {
        "mock_mode": ctrl.mock_mode,
        "system": system_status,
        "active_scans": sum(1 for s in _scans.values() if s["status"] == "scanning"),
        "total_scans": len(_scans),
    }


@router.get("/profiles")
async def list_profiles(request: Request):
    ctrl = _get_controller(request)
    profiles = ctrl.get_available_profiles()
    return {"profiles": profiles}


@router.post("/profiles/{name}/select")
async def select_profile(name: str, request: Request):
    ctrl = _get_controller(request)
    success = ctrl.complete_profile_selection_sequence(name)
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to select profile '{name}'")
    return {"selected": name, "success": True}


@router.post("/scan/start")
async def scan_start(body: ScanStartRequest, request: Request):
    ctrl = _get_controller(request)

    scan_id = str(uuid.uuid4())[:8]
    record: Dict[str, Any] = {
        "id": scan_id,
        "profileId": body.profileId,
        "partId": body.partId,
        "status": "pending",
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "completedAt": None,
        "error": None,
    }
    _scans[scan_id] = record

    # Select profile first
    profile_ok = ctrl.complete_profile_selection_sequence(body.profileId)
    if not profile_ok:
        record["status"] = "failed"
        record["error"] = f"Profile selection failed for '{body.profileId}'"
        raise HTTPException(status_code=400, detail=record["error"])

    # Activate rotation if needed
    ctrl.activate_drehen()

    # Run error correction
    correction_ok = ctrl.error_correction()
    if not correction_ok:
        record["status"] = "failed"
        record["error"] = "Error correction failed"
        raise HTTPException(status_code=400, detail=record["error"])

    record["status"] = "scanning"
    return {"scan": record}


@router.post("/scan/stop")
async def scan_stop(request: Request):
    # Mark all active scans as stopped
    stopped = []
    for scan_id, record in _scans.items():
        if record["status"] == "scanning":
            record["status"] = "stopped"
            record["completedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            stopped.append(scan_id)
    return {"stopped": stopped, "count": len(stopped)}


@router.post("/stl/export")
async def stl_export(request: Request):
    ctrl = _get_controller(request)
    success = ctrl.complete_save_sequence()
    if not success:
        raise HTTPException(status_code=500, detail="STL export sequence failed")
    return {"success": True, "message": "STL export initiated"}


@router.get("/scans")
async def list_scans():
    return {"scans": list(_scans.values()), "total": len(_scans)}


@router.get("/scans/{scan_id}")
async def get_scan(scan_id: str):
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
    task = task_queue.add_task(
        part_name=body.part_name,
        profile_name=body.profile_name,
        priority=body.priority,
    )
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
