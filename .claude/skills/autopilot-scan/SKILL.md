---
name: autopilot-scan
description: Run a full 7-step CT scan workflow from iPad or CLI via the Leitfaden pipeline.
user_invocable: true
allowed-tools: [Bash, Read, Grep, WebFetch]
---

# /autopilot-scan — Full CT Scan Workflow

Run a complete CT scan through the 7-step Leitfaden workflow. Orchestrates the iPad UI, Pi Camera Server, and CT-PC API to automate the entire measurement cycle from sensor selection through STL export.

## When to Use

- Starting a new CT scan measurement
- Re-running a scan with different parameters (voltage, current, steps)
- Automating batch scans from the CLI
- Troubleshooting a failed scan step

## Steps

1. **Check system readiness**
   - Ping all 4 nodes to confirm they are online:
     ```bash
     curl -s http://localhost:4800/api/health  # iPad UI
     curl -s http://localhost:4801/health       # Pi Camera Server
     curl -s http://localhost:4802/health       # CT-PC API
     curl -s http://localhost:4803/api/health   # Health Dashboard
     ```
   - If any node is down, suggest running `/autopilot-health` first

2. **Gather scan parameters**
   - Ask the user for (or read from a preset file):
     - **Sensor**: Which detector to use
     - **Size profile**: Small / Medium / Large part
     - **Voltage** (kV): Typical range 80-225
     - **Current** (uA): Typical range 50-1000
     - **Integration time** (ms): Exposure per projection
     - **Quality**: Draft / Standard / High
     - **Steps**: Number of rotation steps (e.g., 400, 800, 1600)

3. **Step 1 — Sensor selection + size profile**
   - POST to CT-PC API to select sensor and load size profile:
     ```bash
     curl -X POST http://localhost:4802/scan/step/1 \
       -H "Content-Type: application/json" \
       -d '{"sensor": "<sensor>", "sizeProfile": "<profile>"}'
     ```

4. **Step 2 — CT tab switch**
   - Switch WinWerth to the CT measurement tab:
     ```bash
     curl -X POST http://localhost:4802/scan/step/2
     ```

5. **Step 3 — Parameter entry**
   - Enter voltage, current, integration time, quality, and steps:
     ```bash
     curl -X POST http://localhost:4802/scan/step/3 \
       -H "Content-Type: application/json" \
       -d '{"voltage": <kV>, "current": <uA>, "integrationTime": <ms>, "quality": "<quality>", "steps": <n>}'
     ```

6. **Step 4 — Tube activation**
   - Activate the X-ray tube and wait for warmup:
     ```bash
     curl -X POST http://localhost:4802/scan/step/4
     ```
   - Monitor tube status until ready (poll `/scan/status`)

7. **Step 5 — Position check**
   - Trigger rotation preview and verify Bilddynamik is within 20-220 range:
     ```bash
     curl -X POST http://localhost:4802/scan/step/5
     ```
   - If dynamics are out of range, suggest `/autopilot-calibrate` to adjust

8. **Step 6 — Run the scan (Messen)**
   - Start the measurement:
     ```bash
     curl -X POST http://localhost:4802/scan/step/6
     ```
   - Poll scan progress until complete:
     ```bash
     curl -s http://localhost:4802/scan/status
     ```

9. **Step 7 — STL export**
   - Run the export pipeline: Kontur -> VxVol -> Grafik3D -> Save:
     ```bash
     curl -X POST http://localhost:4802/scan/step/7 \
       -H "Content-Type: application/json" \
       -d '{"outputName": "<part-name>"}'
     ```

10. **Or start full scan in one call**
    - Use the combined endpoint to run all 7 steps:
      ```bash
      curl -X POST http://localhost:4802/scan/start \
        -H "Content-Type: application/json" \
        -d '{"sensor": "<sensor>", "sizeProfile": "<profile>", "voltage": <kV>, "current": <uA>, "integrationTime": <ms>, "quality": "<quality>", "steps": <n>, "outputName": "<part-name>"}'
      ```

11. **Verify result**
    - Check scan completed successfully and STL file was exported
    - Show scan duration, file size, and output path

## What's Next

- `/autopilot-stl` — Analyze the exported STL, run Soll-Ist comparison
- `/autopilot-calibrate` — Adjust calibration if dynamics were out of range
- `/autopilot-status` — View scan history and queue
- `/autopilot-health` — Verify all nodes are still healthy after the scan
