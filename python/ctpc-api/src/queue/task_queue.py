"""
Task Queue — replaces Trello board for scan job management.

In-memory priority queue with JSON persistence to disk.
Thread-safe via threading.Lock.

Trello mapping:
  - Queue list     -> status=queued
  - Auftrag list   -> status=active
  - Fertig list    -> status=completed
  - Defect list    -> status=failed / cancelled
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

TaskStatus = Literal["queued", "active", "completed", "failed", "cancelled"]
ScanResult = Literal["IO", "NIO"]


@dataclass
class ScanTask:
    """A single scan task in the queue."""

    id: str
    part_name: str
    profile_name: str
    priority: int = 0
    status: TaskStatus = "queued"
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[ScanResult] = None
    stl_path: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ScanTask:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class QueueStats:
    """Aggregate statistics for the queue."""

    total: int = 0
    queued: int = 0
    active: int = 0
    completed: int = 0
    failed: int = 0
    cancelled: int = 0
    avg_duration_s: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ScanTaskQueue:
    """In-memory task queue with JSON persistence.

    Replaces the Trello board (queue/auftrag/fertig/defect lists)
    with a local, self-contained priority queue.
    """

    def __init__(self, data_dir: str | Path = "data") -> None:
        self._lock = threading.Lock()
        self._data_dir = Path(data_dir)
        self._persist_path = self._data_dir / "task_queue.json"
        self._tasks: Dict[str, ScanTask] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load tasks from disk if the file exists."""
        if not self._persist_path.exists():
            return
        try:
            raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
            for item in raw:
                task = ScanTask.from_dict(item)
                self._tasks[task.id] = task
            logger.info("Loaded %d tasks from %s", len(self._tasks), self._persist_path)
        except Exception as exc:
            logger.warning("Failed to load task queue from disk: %s", exc)

    def _save(self) -> None:
        """Persist all tasks to disk as JSON."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            payload = [t.to_dict() for t in self._tasks.values()]
            self._persist_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to save task queue to disk: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_task(
        self,
        part_name: str,
        profile_name: str,
        priority: int = 0,
    ) -> ScanTask:
        """Add a new task to the queue.

        Equivalent to Trello's addQueue_ (creating a card in the Queue list).
        """
        with self._lock:
            task = ScanTask(
                id=str(uuid.uuid4())[:8],
                part_name=part_name,
                profile_name=profile_name,
                priority=priority,
                status="queued",
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            self._tasks[task.id] = task
            self._save()
            logger.info("Task %s added: %s / %s (priority=%d)", task.id, part_name, profile_name, priority)
            return task

    def get_next(self) -> Optional[ScanTask]:
        """Return the highest-priority queued task (FIFO within same priority).

        Equivalent to Trello's queueGetNext (first card in Queue list).
        Does NOT change the task status — call activate() separately.
        """
        with self._lock:
            queued = [t for t in self._tasks.values() if t.status == "queued"]
            if not queued:
                return None
            # Sort by priority descending, then by created_at ascending (FIFO)
            queued.sort(key=lambda t: (-t.priority, t.created_at))
            return queued[0]

    def activate_task(self, task_id: str) -> ScanTask:
        """Move a task from queued to active.

        Equivalent to Trello's moveToAuftrag.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task '{task_id}' not found")
            if task.status != "queued":
                raise ValueError(f"Task '{task_id}' is not queued (status={task.status})")
            # Only one active task at a time (same as Trello's single-Auftrag rule)
            active = self.get_active_unlocked()
            if active is not None:
                raise ValueError(
                    f"Cannot activate '{task_id}' — task '{active.id}' is already active"
                )
            task.status = "active"
            task.started_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info("Task %s activated", task_id)
            return task

    def get_active(self) -> Optional[ScanTask]:
        """Return the currently active task (if any).

        Equivalent to Trello's getAuftrag.
        """
        with self._lock:
            return self.get_active_unlocked()

    def get_active_unlocked(self) -> Optional[ScanTask]:
        """Non-locking version for internal use."""
        for t in self._tasks.values():
            if t.status == "active":
                return t
        return None

    def complete_task(
        self,
        task_id: str,
        result: ScanResult,
        stl_path: Optional[str] = None,
    ) -> ScanTask:
        """Mark a task as completed with result IO or NIO.

        Equivalent to Trello's moveToFertig.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task '{task_id}' not found")
            if task.status != "active":
                raise ValueError(f"Task '{task_id}' is not active (status={task.status})")
            task.status = "completed"
            task.result = result
            task.stl_path = stl_path
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info("Task %s completed: %s", task_id, result)
            return task

    def fail_task(self, task_id: str, error_message: str) -> ScanTask:
        """Mark a task as failed.

        Equivalent to Trello's moveToDefect.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task '{task_id}' not found")
            if task.status not in ("queued", "active"):
                raise ValueError(f"Task '{task_id}' cannot fail (status={task.status})")
            task.status = "failed"
            task.error_message = error_message
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.warning("Task %s failed: %s", task_id, error_message)
            return task

    def cancel_task(self, task_id: str) -> ScanTask:
        """Cancel a queued task.

        Equivalent to Trello's moveToDefect for queued items.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task '{task_id}' not found")
            if task.status != "queued":
                raise ValueError(f"Task '{task_id}' is not queued (status={task.status})")
            task.status = "cancelled"
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._save()
            logger.info("Task %s cancelled", task_id)
            return task

    def delete_task(self, task_id: str) -> None:
        """Remove a task from history (completed/failed/cancelled only)."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(f"Task '{task_id}' not found")
            if task.status in ("queued", "active"):
                raise ValueError(
                    f"Cannot delete task '{task_id}' with status '{task.status}' — cancel or complete it first"
                )
            del self._tasks[task_id]
            self._save()
            logger.info("Task %s deleted from history", task_id)

    def get_queue(self) -> List[ScanTask]:
        """Return all queued tasks, sorted by priority desc then FIFO."""
        with self._lock:
            queued = [t for t in self._tasks.values() if t.status == "queued"]
            queued.sort(key=lambda t: (-t.priority, t.created_at))
            return queued

    def get_history(self, limit: int = 50) -> List[ScanTask]:
        """Return completed/failed/cancelled tasks, newest first."""
        with self._lock:
            done = [
                t for t in self._tasks.values()
                if t.status in ("completed", "failed", "cancelled")
            ]
            done.sort(key=lambda t: t.completed_at or "", reverse=True)
            return done[:limit]

    def get_stats(self) -> QueueStats:
        """Aggregate queue statistics."""
        with self._lock:
            tasks = list(self._tasks.values())

        total = len(tasks)
        by_status = {}
        for t in tasks:
            by_status[t.status] = by_status.get(t.status, 0) + 1

        # Average duration for completed tasks
        durations: List[float] = []
        for t in tasks:
            if t.status == "completed" and t.started_at and t.completed_at:
                try:
                    start = datetime.fromisoformat(t.started_at)
                    end = datetime.fromisoformat(t.completed_at)
                    durations.append((end - start).total_seconds())
                except (ValueError, TypeError):
                    pass

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return QueueStats(
            total=total,
            queued=by_status.get("queued", 0),
            active=by_status.get("active", 0),
            completed=by_status.get("completed", 0),
            failed=by_status.get("failed", 0),
            cancelled=by_status.get("cancelled", 0),
            avg_duration_s=round(avg_duration, 2),
        )
