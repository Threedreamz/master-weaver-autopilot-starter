"""
CT-PC FastAPI Server — wraps WinWerth automation for remote control.

Starts in mock mode when not running on Windows or when WinWerth is unavailable.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .api.ws import ws_router, broadcast
from .winwerth.controller import WinWerthController
from .discovery.network_scanner import NetworkScanner
from .timetracking.tracker import TimeTracker

logger = logging.getLogger("ctpc-api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

# Global controller instance — set during startup
controller: WinWerthController | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    global controller

    logger.info("Starting CT-PC API server...")

    try:
        controller = WinWerthController()
        mode = "LIVE" if not controller.mock_mode else "MOCK"
        logger.info(f"WinWerthController initialised in {mode} mode")
    except Exception as exc:
        logger.warning(f"WinWerthController init failed ({exc}), falling back to mock mode")
        controller = WinWerthController(force_mock=True)

    app.state.controller = controller

    # Start network discovery scanner
    scanner = NetworkScanner(cache_dir=Path(__file__).parent.parent)
    app.state.network_scanner = scanner
    await scanner.start()
    logger.info("Network scanner started (auto-refresh every 60s)")

    # Zeiterfassung initialisieren
    time_tracker = TimeTracker(data_dir=Path(__file__).parent.parent / "data")
    app.state.time_tracker = time_tracker
    logger.info("TimeTracker initialisiert (Auto-Logout nach %d min)", time_tracker._auto_logout_minutes)

    # Background-Task: Auto-Logout-Prüfung alle 60 Sekunden
    async def _auto_logout_loop():
        while True:
            await asyncio.sleep(60)
            try:
                log = time_tracker.auto_logout_check()
                if log is not None:
                    await broadcast({
                        "type": "timetracking",
                        "event": "auto_logout",
                        "worker_id": log.worker_id,
                        "worker_name": log.worker_name,
                        "log": log.to_dict(),
                    })
                    logger.info("Auto-Logout broadcast: %s", log.worker_name)
            except Exception as exc:
                logger.warning("Auto-Logout-Prüfung fehlgeschlagen: %s", exc)

    auto_logout_task = asyncio.create_task(_auto_logout_loop())

    await broadcast({
        "type": "system",
        "event": "server_started",
        "mock_mode": controller.mock_mode,
    })

    yield  # ---- app is running ----

    logger.info("Shutting down CT-PC API server...")
    auto_logout_task.cancel()
    try:
        await auto_logout_task
    except asyncio.CancelledError:
        pass
    logger.info("Auto-Logout-Task gestoppt")
    await scanner.stop()
    logger.info("Network scanner stopped")
    await broadcast({"type": "system", "event": "server_stopped"})


app = FastAPI(
    title="CT-PC API",
    description="Remote control interface for WinWerth CT scanner",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow everything for local-network usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


def main():
    """CLI entry point."""
    import os
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "4802"))
    logger.info(f"Launching uvicorn on {host}:{port}")
    uvicorn.run("src.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()
