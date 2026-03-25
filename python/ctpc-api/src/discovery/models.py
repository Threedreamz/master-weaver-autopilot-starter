"""
Data models for network discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict


@dataclass
class NodeInfo:
    """Represents a discovered autopilot node on the local network."""

    ip: str
    port: int
    node_type: str  # "ipad" | "pi" | "ct" | "health"
    last_seen: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    name: str = ""
    version: str = ""
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NodeInfo:
        return cls(
            ip=data["ip"],
            port=data["port"],
            node_type=data["node_type"],
            last_seen=data.get("last_seen", datetime.utcnow().isoformat() + "Z"),
            name=data.get("name", ""),
            version=data.get("version", ""),
            extras=data.get("extras", {}),
        )
