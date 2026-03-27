---
name: autopilot-deploy
description: Deploy the CT-PC API to the WinWerth PC with PyInstaller or pip, including firewall and health checks.
user_invocable: true
allowed-tools: [Bash, Read, Write, Glob, Grep]
---

# /autopilot-deploy — Deploy CT-PC API to WinWerth PC

Build and deploy the CT-PC API (FastAPI/Python) to the WinWerth Windows PC. Supports two deployment modes: PyInstaller standalone executable or pip-based install with a Windows service.

## When to Use

- Initial setup of a new WinWerth PC
- Deploying a new version of the CT-PC API
- Fixing a broken deployment or service
- Setting up firewall rules for port 4802

## Steps

1. **Check prerequisites**
   - Verify Python 3.11+ is available on the target PC
   - Verify WinWerth software is installed and accessible
   - Check if pywinauto can detect the WinWerth window:
     ```bash
     python -c "from pywinauto import Desktop; print([w.window_text() for w in Desktop(backend='uia').windows()])"
     ```

2. **Choose deployment mode**
   - **PyInstaller** (recommended for production): Single .exe, no Python required on target
   - **pip install** (recommended for development): Easier to update, requires Python on target

3. **Build with PyInstaller (production)**
   ```bash
   cd apps/ct-pc-api
   pip install -r requirements.txt
   pip install pyinstaller
   pyinstaller --onefile --name ct-pc-api \
     --hidden-import pywinauto \
     --hidden-import uvicorn \
     src/main.py
   ```
   - Output: `dist/ct-pc-api.exe`

4. **Or install with pip (development)**
   ```bash
   cd apps/ct-pc-api
   pip install -e .
   ```

5. **Configure environment**
   - Create or update `.env` on the target PC:
     ```
     PORT=4802
     HOSTNAME=0.0.0.0
     WINWERTH_PROCESS=WinWerth
     LOG_LEVEL=info
     SCAN_OUTPUT_DIR=D:/CT-Scans/output
     ```
   - Verify the scan output directory exists

6. **Set up Windows firewall**
   ```bash
   # Run as Administrator on Windows
   netsh advfirewall firewall add rule name="CT-PC API" dir=in action=allow protocol=TCP localport=4802
   ```

7. **Install as Windows service (optional)**
   ```bash
   pip install pywin32
   python scripts/install-service.py --startup auto
   ```
   - Or use NSSM for service management:
     ```bash
     nssm install ct-pc-api "C:\path\to\ct-pc-api.exe"
     nssm set ct-pc-api AppDirectory "C:\path\to\ct-pc-api"
     nssm start ct-pc-api
     ```

8. **Start and verify**
   ```bash
   # Manual start
   python -m uvicorn src.main:app --host 0.0.0.0 --port 4802
   ```
   - Health check:
     ```bash
     curl -s http://localhost:4802/health
     ```
   - Verify pywinauto can reach WinWerth:
     ```bash
     curl -s http://localhost:4802/winwerth/status
     ```

9. **Run smoke test**
   - Execute a dry-run scan (no X-ray) to verify all 7 steps respond:
     ```bash
     curl -X POST http://localhost:4802/scan/dry-run
     ```

## What's Next

- `/autopilot-extract` — Discover WinWerth UI automation IDs for the deployed PC
- `/autopilot-health` — Verify all 4 nodes can reach the new deployment
- `/autopilot-calibrate` — Run initial calibration on the WinWerth system
- `/autopilot-scan` — Run a test scan to validate the full pipeline
