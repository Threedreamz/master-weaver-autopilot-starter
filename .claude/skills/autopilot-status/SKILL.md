---
name: autopilot-status
description: Show CT scanner ecosystem overview — running services, scan history, queue, and worker time logs.
user_invocable: true
allowed-tools: [Bash, Read, WebFetch, Grep]
---

# /autopilot-status — CT Scanner Ecosystem Overview

Display a comprehensive overview of the AutoPilot CT-Scanner system including running services, recent scan history, queued jobs, and worker time tracking.

## When to Use

- Starting a work session to see the current state
- Checking what scans have been completed today
- Reviewing the scan queue before adding new jobs
- Tracking worker hours and scan throughput
- Getting a quick overview for reporting

## Steps

1. **Show service status**
   - Ping all services and display a status table:
     ```bash
     echo "=== AutoPilot CT-Scanner Status ==="
     echo ""
     echo "Service              Port   Status"
     echo "-------              ----   ------"
     for endpoint in "localhost:4800/api/health" "10.0.0.1:4801/health" "localhost:4802/health" "localhost:4803/api/health" "localhost:4804/api/health"; do
       curl -sf "http://$endpoint" --max-time 3 > /dev/null 2>&1 && echo "OK" || echo "DOWN"
     done
     ```
   - Map results to the 5 services:
     | Service | Port | Technology |
     |---------|------|------------|
     | iPad UI | 4800 | Next.js |
     | Pi Camera Server | 4801 | Fastify |
     | CT-PC API | 4802 | FastAPI |
     | Health Dashboard | 4803 | Next.js |
     | Setup Portal | 4804 | Next.js |

2. **Show current scan state**
   ```bash
   curl -s http://localhost:4802/scan/status
   ```
   - Displays: current step (1-7 or idle), progress, part name, elapsed time
   - If a scan is running, show estimated time remaining

3. **Show scan history**
   ```bash
   curl -s http://localhost:4802/scan/history?limit=10
   ```
   - Display recent scans in a table:
     ```
     Date        Part Name        Steps   Duration   Result     STL Size
     ----        ---------        -----   --------   ------     --------
     2026-03-27  housing-v3       1600    45m        completed  128 MB
     2026-03-27  bracket-test     800     22m        completed  45 MB
     2026-03-26  gear-prototype   400     12m        failed:s5  -
     ```
   - Show total scans today, this week, and success rate

4. **Show scan queue**
   ```bash
   curl -s http://localhost:4802/scan/queue
   ```
   - Display queued scan jobs with parameters and priority
   - Show estimated total queue time

5. **Show worker time logs**
   ```bash
   curl -s http://localhost:4802/workers/time-log?date=today
   ```
   - Display worker activity:
     ```
     Worker       Clock In    Clock Out   Scans   Hours
     ------       --------    ---------   -----   -----
     Operator-1   08:00       -           5       4.5h
     Operator-2   09:30       12:00       3       2.5h
     ```

6. **Show system metrics**
   ```bash
   curl -s http://localhost:4802/metrics
   ```
   - Disk space remaining on scan output drive
   - Camera uptime
   - Tube hours (lifetime counter)
   - Last calibration timestamp

7. **Show configuration summary**
   - Read and display current settings:
     ```bash
     curl -s http://localhost:4802/config
     ```
   - Active sensor, default scan parameters, output directory, calibration profile

## What's Next

- `/autopilot-scan` — Start a new scan
- `/autopilot-health` — Deep health check if any service shows as DOWN
- `/autopilot-stl` — Export or analyze STL files from recent scans
- `/autopilot-calibrate` — Run calibration if it has been more than 24 hours
