# WerthAutopilot — CT Scanner Remote Control Server

Standalone Windows executable that runs the CT-PC API server, enabling remote control of the Werth CT scanner from an iPad or any browser on the local network.

## Prerequisites

- **Python 3.11+** (with pip)
- **Windows 10/11** — the .exe must run on the CT-PC where WinWerth is installed
- **Network** — the CT-PC must be on the same WiFi/LAN as the iPad (AutoPilot-CT network from the Raspberry Pi)

## Building the .exe

On the CT-PC (Windows):

```bat
cd python\ctpc-api
build.bat
```

This will:
1. Install PyInstaller
2. Install all project dependencies
3. Build `dist\WerthAutopilot.exe` (single-file executable)

The build takes 2-5 minutes depending on the machine.

## Running

### Option A: Double-click
Double-click `WerthAutopilot.exe` — a console window opens showing the server banner and logs.

### Option B: Command line
```bat
cd dist
WerthAutopilot.exe
```

### What you will see

```
============================================================
  WerthAutopilot v1.0 -- CT Scanner Server
  Mode: LIVE MODE
============================================================

  Network addresses (point iPad browser here):
    http://192.168.1.100:4802 *

  Server running at http://0.0.0.0:4802
  API docs at http://localhost:4802/docs

  Press Ctrl+C to stop the server.
------------------------------------------------------------
```

Point the iPad browser to the IP address marked with `*`.

## Network Setup

The AutoPilot system uses a dedicated WiFi network broadcast by the Raspberry Pi:

```
[iPad] --WiFi--> [Raspberry Pi AP: AutoPilot-CT] --Ethernet--> [CT-PC]
```

- The CT-PC must be connected to the AutoPilot-CT network (WiFi or Ethernet)
- WerthAutopilot binds to `0.0.0.0` so it accepts connections from any interface
- Port **4802** must not be blocked by the Windows firewall

If the firewall blocks connections, run once as Administrator:
```bat
netsh advfirewall firewall add rule name="WerthAutopilot" dir=in action=allow protocol=TCP localport=4802
```

## Mock Mode

If WinWerth is not installed (e.g., running on a development machine), the server starts in **mock mode** automatically. All scan commands return simulated results with realistic delays. This is useful for:

- Developing the iPad UI without access to the CT scanner
- Testing the API endpoints
- Running on non-Windows machines during development

## API Documentation

While the server is running, visit `http://localhost:4802/docs` for the interactive Swagger UI.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Python not found" during build | Install Python 3.11+ and ensure it is in PATH |
| .exe won't start | Run from command line to see error output |
| iPad can't connect | Check firewall, verify both devices on same network |
| "MOCK MODE" when WinWerth is installed | Check WinWerth is in `C:\WinWerth` or `C:\Program Files\WinWerth` |
| .exe is very large (100MB+) | Normal — it bundles Python, OpenCV, and all dependencies |
| Antivirus blocks .exe | Add an exception for `WerthAutopilot.exe` |

## Project Structure

```
python/ctpc-api/
  WerthAutopilot.py       Entry point for the .exe
  WerthAutopilot.spec     PyInstaller build configuration
  build.bat               Windows build script
  build.sh                Linux/macOS build script (reference)
  pyproject.toml          Python project metadata + dependencies
  src/                    Source code
    main.py               FastAPI application
    api/                  REST + WebSocket routes
    winwerth/             WinWerth automation modules
    orchestrator/         Scan workflow state machine
    discovery/            Network device discovery
    analysis/             Soll/Ist deviation analysis
    optical/              Image processing
    queue/                Scan task queue
    notifications/        Email notifications
    timetracking/         Worker time tracking
```
