"""
Network auto-discovery for autopilot nodes.

Ported from Stream_Era branch (auto_find_server / auto_connect_h) and adapted
for the autopilot-starter ecosystem.  Uses mDNS as primary discovery and falls
back to async IP-range scanning when mDNS is unavailable.
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from .models import NodeInfo

logger = logging.getLogger("ctpc-api.discovery")

# ── Port conventions (from ecosystem port registry) ──────────────────────────
# Pi camera server:  4801
# CT-PC API:         4802
# iPad relay:        4803
# Health dashboard:  4804
AUTOPILOT_PORTS: Dict[int, str] = {
    4800: "health",
    4801: "pi",
    4802: "ct",
    4803: "ipad",
    4804: "health",
}

MDNS_SERVICE_TYPE = "_autopilot-pi._tcp.local."
CACHE_FILE = "discovery_cache.json"
SCAN_CONCURRENCY = 30
SCAN_TIMEOUT_S = 1.5
CACHE_REFRESH_INTERVAL_S = 60


class NetworkScanner:
    """Discovers autopilot nodes on the local network.

    Primary: mDNS (zeroconf)
    Fallback: async /health probe on every IP in the local /24 subnet
    """

    def __init__(
        self,
        cache_dir: Path | str = Path("."),
        concurrency: int = SCAN_CONCURRENCY,
        timeout: float = SCAN_TIMEOUT_S,
        refresh_interval: float = CACHE_REFRESH_INTERVAL_S,
    ) -> None:
        self._cache_path = Path(cache_dir) / CACHE_FILE
        self._concurrency = concurrency
        self._timeout = timeout
        self._refresh_interval = refresh_interval

        self._nodes: Dict[str, NodeInfo] = {}  # key = "ip:port"
        self._lock = threading.Lock()
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False

        # Load persisted cache on init
        self._load_cache()

    # ── Public API ───────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the background auto-refresh loop."""
        if self._running:
            return
        self._running = True
        self._refresh_task = asyncio.create_task(self._refresh_loop())
        logger.info("NetworkScanner started (refresh every %ss)", self._refresh_interval)

    async def stop(self) -> None:
        """Stop the background refresh loop."""
        self._running = False
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None
        logger.info("NetworkScanner stopped")

    async def discover_nodes(self) -> List[NodeInfo]:
        """Run a full discovery cycle and return all found nodes."""
        nodes: List[NodeInfo] = []

        # 1. Try mDNS first
        mdns_nodes = await self._discover_mdns()
        if mdns_nodes:
            nodes.extend(mdns_nodes)
            logger.info("mDNS discovered %d node(s)", len(mdns_nodes))

        # 2. Always run IP scan to catch nodes without mDNS
        scan_nodes = await self._scan_ip_range()
        if scan_nodes:
            nodes.extend(scan_nodes)
            logger.info("IP scan discovered %d node(s)", len(scan_nodes))

        # Merge into cache (dedup by ip:port)
        with self._lock:
            for node in nodes:
                key = f"{node.ip}:{node.port}"
                self._nodes[key] = node

        self._save_cache()
        return self._get_all_nodes()

    def get_node(self, node_type: str) -> Optional[NodeInfo]:
        """Quick lookup for a specific node type (e.g. 'pi', 'ct', 'ipad')."""
        with self._lock:
            for node in self._nodes.values():
                if node.node_type == node_type:
                    return node
        return None

    def get_all_cached(self) -> List[NodeInfo]:
        """Return all currently cached nodes without triggering a scan."""
        return self._get_all_nodes()

    # ── mDNS discovery ───────────────────────────────────────────────────────

    async def _discover_mdns(self) -> List[NodeInfo]:
        """Use zeroconf to discover autopilot services via mDNS."""
        try:
            from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
            import socket as _socket
        except ImportError:
            logger.debug("zeroconf not installed, skipping mDNS discovery")
            return []

        found: List[NodeInfo] = []
        event = asyncio.Event()

        def on_service_state_change(
            zeroconf: Zeroconf,
            service_type: str,
            name: str,
            state_change: ServiceStateChange,
        ) -> None:
            if state_change != ServiceStateChange.Added:
                return
            info = zeroconf.get_service_info(service_type, name)
            if info is None:
                return

            addresses = info.parsed_addresses()
            ip = addresses[0] if addresses else None
            if not ip:
                return

            txt = {
                k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                for k, v in (info.properties or {}).items()
            }

            node_type = _infer_node_type_from_txt(txt, info.port)
            found.append(NodeInfo(
                ip=ip,
                port=info.port,
                node_type=node_type,
                last_seen=datetime.utcnow().isoformat() + "Z",
                name=name,
                version=txt.get("version", ""),
                extras=txt,
            ))

        zc = Zeroconf()
        try:
            browser = ServiceBrowser(zc, MDNS_SERVICE_TYPE, handlers=[on_service_state_change])
            # Give mDNS 3 seconds to collect responses
            await asyncio.sleep(3)
        finally:
            zc.close()

        return found

    # ── IP range scanner ─────────────────────────────────────────────────────

    @staticmethod
    def get_local_ip() -> str:
        """Detect the local IPv4 address (same approach as Stream_Era)."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = socket.gethostbyname(socket.gethostname())
        finally:
            s.close()
        return ip

    async def _scan_ip_range(
        self,
        base: Optional[str] = None,
        start: int = 1,
        stop: int = 255,
    ) -> List[NodeInfo]:
        """Scan the local /24 subnet for autopilot health endpoints."""
        if base is None:
            local_ip = self.get_local_ip()
            parts = local_ip.split(".")
            if len(parts) != 4:
                logger.error("Could not determine local IPv4 subnet")
                return []
            base = ".".join(parts[:3])

        logger.info("Scanning %s.0/24 (range %d-%d, concurrency=%d)", base, start, stop - 1, self._concurrency)

        sem = asyncio.Semaphore(self._concurrency)
        found: List[NodeInfo] = []
        found_lock = asyncio.Lock()

        async def probe(ip: str, port: int, node_type: str) -> None:
            async with sem:
                node = await self._probe_health(ip, port, node_type)
                if node:
                    async with found_lock:
                        found.append(node)

        tasks = []
        for i in range(start, stop):
            ip = f"{base}.{i}"
            for port, node_type in AUTOPILOT_PORTS.items():
                tasks.append(asyncio.create_task(probe(ip, port, node_type)))

        await asyncio.gather(*tasks)
        logger.info("IP scan complete — found %d node(s)", len(found))
        return found

    async def _probe_health(self, ip: str, port: int, node_type: str) -> Optional[NodeInfo]:
        """Probe a single ip:port for /health or /api/health endpoint."""
        urls = [
            f"http://{ip}:{port}/health",
            f"http://{ip}:{port}/api/health",
        ]

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for url in urls:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                        detected_type = data.get("app", node_type)
                        # Map app names to canonical node types
                        type_map = {
                            "ctpc-api": "ct",
                            "pi-firmware": "pi",
                            "pi-camera": "pi",
                            "ipad-relay": "ipad",
                            "autopilot-health": "health",
                        }
                        resolved_type = type_map.get(detected_type, node_type)

                        return NodeInfo(
                            ip=ip,
                            port=port,
                            node_type=resolved_type,
                            last_seen=datetime.utcnow().isoformat() + "Z",
                            name=data.get("app", ""),
                            version=data.get("version", ""),
                            extras=data,
                        )
                except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                    continue
                except Exception:
                    continue
        return None

    # ── Background refresh ───────────────────────────────────────────────────

    async def _refresh_loop(self) -> None:
        """Periodically re-scan the network."""
        while self._running:
            try:
                await self.discover_nodes()
            except Exception as exc:
                logger.warning("Discovery refresh failed: %s", exc)
            await asyncio.sleep(self._refresh_interval)

    # ── Cache persistence ────────────────────────────────────────────────────

    def _get_all_nodes(self) -> List[NodeInfo]:
        with self._lock:
            return list(self._nodes.values())

    def _save_cache(self) -> None:
        with self._lock:
            data = {k: v.to_dict() for k, v in self._nodes.items()}
        try:
            self._cache_path.write_text(json.dumps(data, indent=2))
        except Exception as exc:
            logger.warning("Failed to write discovery cache: %s", exc)

    def _load_cache(self) -> None:
        if not self._cache_path.exists():
            return
        try:
            raw = json.loads(self._cache_path.read_text())
            with self._lock:
                for key, val in raw.items():
                    self._nodes[key] = NodeInfo.from_dict(val)
            logger.info("Loaded %d node(s) from cache", len(self._nodes))
        except Exception as exc:
            logger.warning("Failed to load discovery cache: %s", exc)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _infer_node_type_from_txt(txt: Dict[str, str], port: int) -> str:
    """Guess node type from mDNS TXT record or port."""
    if "cameras" in txt:
        return "pi"
    return AUTOPILOT_PORTS.get(port, "health")
