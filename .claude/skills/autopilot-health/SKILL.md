---
name: autopilot-health
description: Check health of all 4 CT scanner nodes — iPad UI, Pi Camera, CT-PC API, and Health Dashboard.
user_invocable: true
allowed-tools: [Bash, Read, WebFetch]
---

# /autopilot-health — CT Scanner Health Check

Ping all 4 nodes of the CT scanner system and report their status, including camera feeds, scan state, and WinWerth connectivity.

## When to Use

- Before starting a scan to confirm all systems are ready
- After deploying or restarting any node
- When a scan fails and you need to isolate which node is down
- Routine check of the CT scanner setup

## Steps

1. **Check iPad UI (port 4800)**
   ```bash
   curl -sf http://localhost:4800/api/health --max-time 5 && echo "OK" || echo "UNREACHABLE"
   ```
   - Expected: `{"status":"ok","app":"autopilot-ipad","timestamp":"..."}`
   - If down: The iPad Next.js app is not running. Check `pnpm dev` in `apps/ipad-ui/`

2. **Check Pi Camera Server (port 4801)**
   ```bash
   curl -sf http://10.0.0.1:4801/health --max-time 5 && echo "OK" || echo "UNREACHABLE"
   ```
   - Expected: `{"status":"ok","cameras":2,"streaming":true}`
   - Also check individual cameras:
     ```bash
     curl -sf http://10.0.0.1:4801/cameras --max-time 5
     ```
   - Expected: Two cameras with status "active" and resolution "3840x2160"
   - If down: Pi may not be powered on, or WiFi AP may not be broadcasting

3. **Check CT-PC API (port 4802)**
   ```bash
   curl -sf http://localhost:4802/health --max-time 5 && echo "OK" || echo "UNREACHABLE"
   ```
   - Expected: `{"status":"ok","winwerth_connected":true,"tube_status":"off"}`
   - Also check WinWerth connectivity:
     ```bash
     curl -sf http://localhost:4802/winwerth/status --max-time 5
     ```
   - Expected: WinWerth process detected, automation IDs loaded
   - If down: Check if the Python service is running. Check Windows firewall for port 4802

4. **Check Health Dashboard (port 4803)**
   ```bash
   curl -sf http://localhost:4803/api/health --max-time 5 && echo "OK" || echo "UNREACHABLE"
   ```
   - Expected: `{"status":"ok","app":"autopilot-dashboard","timestamp":"..."}`
   - If down: Dashboard Next.js app is not running

5. **Check scan state**
   ```bash
   curl -sf http://localhost:4802/scan/status --max-time 5
   ```
   - Shows: current scan step (1-7 or idle), progress percentage, estimated time remaining
   - If a scan is stuck, report the last completed step

6. **Generate health summary**
   - Print a status table:
     ```
     Node              Port   Status      Details
     ----              ----   ------      -------
     iPad UI           4800   OK          v1.2.0
     Pi Camera Server  4801   OK          2 cameras, streaming
     CT-PC API         4802   OK          WinWerth connected, tube off
     Health Dashboard  4803   OK          v1.0.0

     Scan State: idle
     Last Scan: 2026-03-27T10:30:00Z (completed, 847 steps)
     ```
   - If any node is down, show it as UNREACHABLE with suggested fix

7. **Optional: Check Setup Portal (port 4804)**
   ```bash
   curl -sf http://localhost:4804/api/health --max-time 5 && echo "OK" || echo "UNREACHABLE"
   ```
   - Only relevant during initial setup

## What's Next

- `/autopilot-scan` — All nodes healthy, ready to start a scan
- `/autopilot-deploy` — Redeploy CT-PC API if it is unreachable
- `/autopilot-pi` — Re-flash Pi if the camera server is down
- `/autopilot-calibrate` — Run calibration if WinWerth is connected but uncalibrated
