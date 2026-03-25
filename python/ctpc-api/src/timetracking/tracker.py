"""
TimeTracker — Kern-Logik der Zeiterfassung.

Verwaltet Mitarbeiter (Worker) und Zeiteinträge (TimeLog) mit
JSON-Persistenz und Thread-Sicherheit.

Features:
  - Nur ein Worker gleichzeitig aktiv (Login loggt Vorgänger automatisch aus)
  - Auto-Logout nach konfigurierbarer Dauer (Standard: 8 Stunden)
  - CSV-Export für Abrechnungszwecke
"""

from __future__ import annotations

import csv
import io
import json
import logging
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .models import TimeAction, TimeLog, TimeTrackingStats, Worker

logger = logging.getLogger(__name__)


class TimeTracker:
    """In-memory Zeiterfassung mit JSON-Persistenz.

    Gleiche Architektur wie ScanTaskQueue: threading.Lock + JSON-Dateien.
    """

    def __init__(
        self,
        data_dir: str | Path = "data",
        auto_logout_minutes: int = 480,
    ) -> None:
        self._lock = threading.Lock()
        self._data_dir = Path(data_dir)
        self._workers_path = self._data_dir / "workers.json"
        self._timelogs_path = self._data_dir / "timelogs.json"
        self._auto_logout_minutes = auto_logout_minutes

        self._workers: Dict[str, Worker] = {}
        self._timelogs: List[TimeLog] = []

        self._load()

    # ------------------------------------------------------------------
    # Persistenz
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Lade Workers und TimeLogs von Disk."""
        if self._workers_path.exists():
            try:
                raw = json.loads(self._workers_path.read_text(encoding="utf-8"))
                for item in raw:
                    w = Worker.from_dict(item)
                    self._workers[w.id] = w
                logger.info("Loaded %d workers from %s", len(self._workers), self._workers_path)
            except Exception as exc:
                logger.warning("Failed to load workers: %s", exc)

        if self._timelogs_path.exists():
            try:
                raw = json.loads(self._timelogs_path.read_text(encoding="utf-8"))
                self._timelogs = [TimeLog.from_dict(item) for item in raw]
                logger.info("Loaded %d timelogs from %s", len(self._timelogs), self._timelogs_path)
            except Exception as exc:
                logger.warning("Failed to load timelogs: %s", exc)

    def _save_workers(self) -> None:
        """Alle Workers auf Disk schreiben."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            payload = [w.to_dict() for w in self._workers.values()]
            self._workers_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to save workers: %s", exc)

    def _save_timelogs(self) -> None:
        """Alle TimeLogs auf Disk schreiben."""
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            payload = [tl.to_dict() for tl in self._timelogs]
            self._timelogs_path.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning("Failed to save timelogs: %s", exc)

    def _save_all(self) -> None:
        """Workers + TimeLogs speichern."""
        self._save_workers()
        self._save_timelogs()

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _today_str(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _create_log(
        self,
        worker: Worker,
        action: TimeAction,
        scan_id: Optional[str] = None,
    ) -> TimeLog:
        """Neuen TimeLog-Eintrag erstellen und zur Liste hinzufügen."""
        log = TimeLog(
            id=str(uuid.uuid4())[:8],
            worker_id=worker.id,
            worker_name=worker.name,
            action=action,
            timestamp=self._now_iso(),
            scan_id=scan_id,
        )
        self._timelogs.append(log)
        return log

    def _get_active_worker_unlocked(self) -> Optional[Worker]:
        """Aktiven Worker finden (ohne Lock)."""
        for w in self._workers.values():
            if w.active:
                return w
        return None

    # ------------------------------------------------------------------
    # Worker-Verwaltung
    # ------------------------------------------------------------------

    def add_worker(self, name: str) -> Worker:
        """Neuen Mitarbeiter anlegen."""
        with self._lock:
            worker = Worker(
                id=str(uuid.uuid4())[:8],
                name=name,
                active=False,
                created_at=self._now_iso(),
            )
            self._workers[worker.id] = worker
            self._save_workers()
            logger.info("Worker angelegt: %s (%s)", worker.name, worker.id)
            return worker

    def remove_worker(self, worker_id: str) -> bool:
        """Mitarbeiter entfernen. Aktive Worker werden vorher ausgeloggt."""
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker is None:
                return False

            # Aktiven Worker vorher ausloggen
            if worker.active:
                worker.active = False
                worker.last_logout = self._now_iso()
                self._create_log(worker, "logout")

            del self._workers[worker_id]
            self._save_all()
            logger.info("Worker entfernt: %s (%s)", worker.name, worker_id)
            return True

    def get_workers(self) -> List[Worker]:
        """Alle Mitarbeiter zurückgeben."""
        with self._lock:
            return list(self._workers.values())

    def get_active_worker(self) -> Optional[Worker]:
        """Aktuell angemeldeten Worker zurückgeben."""
        with self._lock:
            return self._get_active_worker_unlocked()

    # ------------------------------------------------------------------
    # Login / Logout
    # ------------------------------------------------------------------

    def login_worker(self, worker_id: str) -> TimeLog:
        """Worker anmelden. Vorheriger Worker wird automatisch abgemeldet.

        Raises:
            KeyError: Worker existiert nicht
            ValueError: Worker ist bereits angemeldet
        """
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker is None:
                raise KeyError(f"Worker '{worker_id}' nicht gefunden")

            if worker.active:
                raise ValueError(f"Worker '{worker.name}' ist bereits angemeldet")

            # Vorherigen Worker automatisch abmelden
            prev = self._get_active_worker_unlocked()
            if prev is not None:
                prev.active = False
                prev.last_logout = self._now_iso()
                self._create_log(prev, "auto-logout")
                logger.info("Auto-Logout: %s (ersetzt durch %s)", prev.name, worker.name)

            # Neuen Worker anmelden
            worker.active = True
            worker.last_login = self._now_iso()
            log = self._create_log(worker, "login")

            self._save_all()
            logger.info("Login: %s (%s)", worker.name, worker.id)
            return log

    def logout_worker(self, worker_id: str) -> TimeLog:
        """Worker abmelden.

        Raises:
            KeyError: Worker existiert nicht
            ValueError: Worker ist nicht angemeldet
        """
        with self._lock:
            worker = self._workers.get(worker_id)
            if worker is None:
                raise KeyError(f"Worker '{worker_id}' nicht gefunden")

            if not worker.active:
                raise ValueError(f"Worker '{worker.name}' ist nicht angemeldet")

            worker.active = False
            worker.last_logout = self._now_iso()
            log = self._create_log(worker, "logout")

            self._save_all()
            logger.info("Logout: %s (%s)", worker.name, worker.id)
            return log

    def auto_logout_check(self) -> Optional[TimeLog]:
        """Prüfe ob der aktive Worker die maximale Arbeitszeit überschritten hat.

        Wird periodisch vom Background-Task aufgerufen (alle 60s).
        Gibt den erzeugten TimeLog zurück, falls ein Auto-Logout stattfand.
        """
        with self._lock:
            active = self._get_active_worker_unlocked()
            if active is None or active.last_login is None:
                return None

            try:
                login_time = datetime.fromisoformat(active.last_login)
            except (ValueError, TypeError):
                return None

            now = datetime.now(timezone.utc)
            elapsed = now - login_time

            if elapsed < timedelta(minutes=self._auto_logout_minutes):
                return None

            # Auto-Logout durchführen
            active.active = False
            active.last_logout = self._now_iso()
            log = self._create_log(active, "auto-logout")

            self._save_all()
            logger.warning(
                "Auto-Logout: %s nach %d Minuten (Limit: %d min)",
                active.name,
                int(elapsed.total_seconds() / 60),
                self._auto_logout_minutes,
            )
            return log

    # ------------------------------------------------------------------
    # Abfragen & Statistiken
    # ------------------------------------------------------------------

    def get_timelogs(
        self,
        date: Optional[str] = None,
        worker_id: Optional[str] = None,
    ) -> List[TimeLog]:
        """TimeLogs filtern nach Datum (YYYY-MM-DD) und/oder Worker-ID."""
        with self._lock:
            logs = list(self._timelogs)

        if date:
            logs = [tl for tl in logs if tl.timestamp.startswith(date)]

        if worker_id:
            logs = [tl for tl in logs if tl.worker_id == worker_id]

        # Neueste zuerst
        logs.sort(key=lambda tl: tl.timestamp, reverse=True)
        return logs

    def get_stats(self) -> TimeTrackingStats:
        """Tagesstatistik berechnen: Stunden pro Worker, aktiver Worker, Logs."""
        today = self._today_str()
        today_logs = self.get_timelogs(date=today)

        # Stunden pro Worker berechnen
        worker_hours: Dict[str, float] = {}
        with self._lock:
            for w in self._workers.values():
                hours = self._calc_worker_hours_today(w.id, today)
                if hours > 0:
                    worker_hours[w.name] = round(hours, 2)

            active = self._get_active_worker_unlocked()

        total_hours = sum(worker_hours.values())

        return TimeTrackingStats(
            total_hours_today=round(total_hours, 2),
            active_worker=active.to_dict() if active else None,
            today_logs=[tl.to_dict() for tl in today_logs],
            worker_hours=worker_hours,
        )

    def _calc_worker_hours_today(self, worker_id: str, today: str) -> float:
        """Arbeitsstunden eines Workers für einen Tag berechnen (Lock muss gehalten werden)."""
        # Alle Logs des Workers für heute, chronologisch
        logs = [
            tl for tl in self._timelogs
            if tl.worker_id == worker_id and tl.timestamp.startswith(today)
        ]
        logs.sort(key=lambda tl: tl.timestamp)

        total_seconds = 0.0
        login_time: Optional[datetime] = None

        for log in logs:
            try:
                ts = datetime.fromisoformat(log.timestamp)
            except (ValueError, TypeError):
                continue

            if log.action == "login":
                login_time = ts
            elif log.action in ("logout", "auto-logout") and login_time is not None:
                total_seconds += (ts - login_time).total_seconds()
                login_time = None

        # Falls Worker noch eingeloggt ist: Zeit bis jetzt zählen
        if login_time is not None:
            worker = self._workers.get(worker_id)
            if worker and worker.active:
                total_seconds += (datetime.now(timezone.utc) - login_time).total_seconds()

        return total_seconds / 3600.0

    # ------------------------------------------------------------------
    # CSV-Export
    # ------------------------------------------------------------------

    def export_csv(self, date: Optional[str] = None) -> str:
        """TimeLogs als CSV exportieren.

        Args:
            date: Optionaler Filter (YYYY-MM-DD). Ohne Filter: alle Logs.

        Returns:
            CSV-String mit Header-Zeile.
        """
        logs = self.get_timelogs(date=date)
        # Chronologisch für Export (älteste zuerst)
        logs.sort(key=lambda tl: tl.timestamp)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["ID", "Worker-ID", "Worker-Name", "Aktion", "Zeitstempel", "Scan-ID"])

        for log in logs:
            writer.writerow([
                log.id,
                log.worker_id,
                log.worker_name,
                log.action,
                log.timestamp,
                log.scan_id or "",
            ])

        return output.getvalue()
