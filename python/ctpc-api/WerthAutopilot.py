"""WerthAutopilot — CT Scanner Remote Control Server

Runs the FastAPI server as a standalone Windows application.
Built with PyInstaller into a single .exe for deployment on the CT-PC.
"""

from __future__ import annotations

import logging
import os
import platform
import signal
import socket
import sys
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Logging setup — before any other imports so all modules use this config
# ---------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("WerthAutopilot")

VERSION = "1.0.0"
HOST = "0.0.0.0"
PORT = 4802


# ---------------------------------------------------------------------------
# Network helpers
# ---------------------------------------------------------------------------

def _get_local_ips() -> List[Tuple[str, str]]:
    """Return list of (interface_hint, ip) for all non-loopback IPv4 addresses."""
    results: List[Tuple[str, str]] = []
    try:
        # Use UDP socket trick to find the primary LAN IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            results.append(("primary", primary_ip))
    except Exception:
        pass

    # Also enumerate all interfaces via getaddrinfo
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip != "127.0.0.1" and not any(ip == r[1] for r in results):
                results.append(("additional", ip))
    except Exception:
        pass

    if not results:
        results.append(("loopback", "127.0.0.1"))

    return results


def _detect_winwerth() -> bool:
    """Check if WinWerth is likely available (Windows + expected process/path)."""
    if platform.system() != "Windows":
        return False
    # Check for typical WinWerth installation paths
    winwerth_paths = [
        r"C:\WinWerth",
        r"C:\Program Files\WinWerth",
        r"C:\Program Files (x86)\WinWerth",
    ]
    return any(os.path.isdir(p) for p in winwerth_paths)


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def _print_banner(mock_mode: bool) -> None:
    """Print startup banner with server info."""
    mode = "MOCK MODE" if mock_mode else "LIVE MODE"
    ips = _get_local_ips()

    print()
    print("=" * 60)
    print(f"  WerthAutopilot v{VERSION} -- CT Scanner Server")
    print(f"  Mode: {mode}")
    print("=" * 60)
    print()

    if mock_mode:
        print("  [!] WinWerth not detected — running in mock mode.")
        print("      All scan commands will be simulated.")
        print()

    print("  Network addresses (point iPad browser here):")
    for hint, ip in ips:
        tag = " *" if hint == "primary" else ""
        print(f"    http://{ip}:{PORT}{tag}")
    print()
    print(f"  Server running at http://{HOST}:{PORT}")
    print(f"  API docs at http://localhost:{PORT}/docs")
    print()
    print("  Press Ctrl+C to stop the server.")
    print("-" * 60)
    print()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the WerthAutopilot server."""
    # Late import so PyInstaller can trace the dependency
    import uvicorn

    mock_mode = not _detect_winwerth()
    _print_banner(mock_mode)

    # Graceful shutdown on Ctrl+C
    def _signal_handler(sig: int, frame: object) -> None:
        print()
        logger.info("Shutdown requested (Ctrl+C) — stopping server...")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGBREAK"):
        # Windows-specific: Ctrl+Break
        signal.signal(signal.SIGBREAK, _signal_handler)

    try:
        logger.info("Starting uvicorn on %s:%d", HOST, PORT)
        uvicorn.run(
            "src.main:app",
            host=HOST,
            port=PORT,
            log_level="info",
            # No reload in production .exe
            reload=False,
            # Workers=1 for Windows compatibility (pywinauto is not multiprocess-safe)
            workers=1,
        )
    except SystemExit:
        logger.info("Server stopped.")
    except Exception:
        logger.exception("Fatal error — server crashed")
        if platform.system() == "Windows":
            print()
            print("Press Enter to close this window...")
            input()
        sys.exit(1)


if __name__ == "__main__":
    main()
