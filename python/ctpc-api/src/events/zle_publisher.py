"""
ZLE (OpenBounty) Event Publisher — Sends scan events to OpenBounty for time tracking.

Usage:
    from events import ZlePublisher

    publisher = ZlePublisher()  # reads ZLE_API_URL from env

    # In callback wiring:
    await publisher.publish('autopilot.scan.completed', {
        'scanId': '42',
        'stlPath': '/path/to/output.stl',
    })
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Try httpx first (async), fall back to urllib (sync)
try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
    import json
    import urllib.request
    import urllib.error


class ZlePublisher:
    """Fire-and-forget event publisher for OpenBounty."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0):
        self.base_url = base_url or os.environ.get("ZLE_API_URL", "http://localhost:4670")
        self.timeout = timeout
        self._endpoint = f"{self.base_url}/api/opendesktop/events"
        self._client: "httpx.AsyncClient | None" = None
        logger.info("ZlePublisher initialized: %s", self._endpoint)

    async def _get_client(self) -> "httpx.AsyncClient":
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def publish(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        user_id: str | None = None,
        arbeitsplatz_id: str | None = None,
    ) -> bool:
        """
        Send an event to OpenBounty. Returns True on success, False on failure.
        Never raises — errors are logged.
        """
        payload = {
            "source": "autopilot",
            "eventType": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }
        if user_id:
            payload["userId"] = user_id
        if arbeitsplatz_id:
            payload["arbeitsplatzId"] = arbeitsplatz_id

        try:
            if _HAS_HTTPX:
                client = await self._get_client()
                resp = await client.post(self._endpoint, json=payload)
                if resp.status_code >= 400:
                    logger.warning(
                        "ZLE event %s failed: %d %s",
                        event_type, resp.status_code, resp.text[:200],
                    )
                    return False
                logger.debug("ZLE event %s sent successfully", event_type)
                return True
            else:
                # Sync fallback with urllib
                req = urllib.request.Request(
                    self._endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status >= 400:
                        logger.warning("ZLE event %s failed: %d", event_type, resp.status)
                        return False
                logger.debug("ZLE event %s sent successfully", event_type)
                return True

        except Exception as exc:
            logger.warning("ZLE event %s error: %s", event_type, exc)
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
