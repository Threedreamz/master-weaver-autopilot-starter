"""
WebSocket endpoint for real-time event broadcasting.

Clients connect to /ws/events and receive JSON messages for:
  - scan state changes
  - system status updates
  - error notifications
  - heartbeat pings
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("ctpc-api.ws")

ws_router = APIRouter()

# Active WebSocket connections
_clients: Set[WebSocket] = set()

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 5.0


async def broadcast(message: Dict[str, Any]) -> None:
    """Send a JSON message to all connected WebSocket clients."""
    if not _clients:
        return

    payload = json.dumps({
        **message,
        "ts": time.time(),
    })

    disconnected: list[WebSocket] = []
    for ws in _clients:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        _clients.discard(ws)


async def _heartbeat_loop(ws: WebSocket) -> None:
    """Send periodic heartbeat pings to a single client."""
    try:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await ws.send_text(json.dumps({
                "type": "heartbeat",
                "ts": time.time(),
            }))
    except Exception:
        pass  # connection gone


@ws_router.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    _clients.add(ws)
    logger.info(f"WebSocket client connected (total: {len(_clients)})")

    # Start heartbeat task for this connection
    heartbeat_task = asyncio.create_task(_heartbeat_loop(ws))

    try:
        # Send welcome message
        await ws.send_text(json.dumps({
            "type": "connected",
            "message": "CT-PC event stream",
            "ts": time.time(),
        }))

        # Keep connection alive — listen for client messages (pings, commands)
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await ws.send_text(json.dumps({
                        "type": "pong",
                        "ts": time.time(),
                    }))
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.warning(f"WebSocket error: {exc}")
    finally:
        heartbeat_task.cancel()
        _clients.discard(ws)
        logger.info(f"WebSocket clients remaining: {len(_clients)}")
