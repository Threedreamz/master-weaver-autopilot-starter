"""
Datenmodelle für die Zeiterfassung.

Worker       — Mitarbeiter-Stammdaten
TimeLog      — Einzelner Zeitstempel (Login/Logout/Auto-Logout)
TimeTrackingStats — Tagesstatistiken + Stundenübersicht
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

TimeAction = Literal["login", "logout", "auto-logout"]


@dataclass
class Worker:
    """Ein Mitarbeiter, der sich am CT-Scanner an-/abmelden kann."""

    id: str
    name: str
    active: bool = False
    last_login: Optional[str] = None
    last_logout: Optional[str] = None
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Worker:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TimeLog:
    """Einzelner Zeiterfassungseintrag — Login, Logout oder Auto-Logout."""

    id: str
    worker_id: str
    worker_name: str
    action: TimeAction
    timestamp: str
    scan_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimeLog:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TimeTrackingStats:
    """Aggregierte Tagesstatistik für die Zeiterfassung."""

    total_hours_today: float = 0.0
    active_worker: Optional[Dict[str, Any]] = None
    today_logs: List[Dict[str, Any]] = field(default_factory=list)
    worker_hours: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TimeTrackingStats:
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
