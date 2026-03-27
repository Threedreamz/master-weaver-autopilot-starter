# Emergency Procedures — AutoPilot CT-Scanner

## E1: X-Ray Tube Stuck On

**Severity:** CRITICAL — radiation exposure risk

**Symptoms:** tube_on=true after scan completion, tube won't respond to off command

**Steps:**
1. POST http://localhost:4802/scan/stop (abort scan)
2. Check: GET http://localhost:4802/status -> verify tube_on field
3. If still on: run `npx tsx .claude/hooks/emergency-stop.ts "tube stuck"`
4. If API unreachable: PHYSICALLY power off CT-PC
5. Log incident in .claude/logs/emergency-stops.json

## E2: Scan Timeout (>10 min)

**Severity:** HIGH — tube running beyond normal operation

**Steps:**
1. State machine auto-transitions to ERROR after 600s
2. Verify via GET /scan/state
3. If stuck in SCANNING: POST /scan/stop
4. If scan/stop fails: restart uvicorn (kill + restart)
5. Verify tube_on=false before next scan

## E3: WinWerth Application Crash

**Severity:** HIGH — automation lost, tube state unknown

**Steps:**
1. Server auto-detects WinWerth gone -> logs warning
2. Check tube: physical inspection of CT-PC screen
3. Restart WinWerth.exe
4. Restart CT-PC API server (it re-detects WinWerth on start)
5. Run /autopilot-health to verify all nodes

## E4: Network Loss (Pi <-> CT-PC)

**Severity:** MEDIUM — iPad control lost, but scan continues

**Steps:**
1. Scan in progress will COMPLETE (CT-PC runs independently)
2. Reconnect to AutoPilot-CT WiFi
3. Check status: GET http://CT-PC-IP:4802/status
4. If scan completed: STL is on CT-PC disk, retrieve manually

## E5: State Machine Deadlock

**Severity:** MEDIUM — scan stuck in intermediate state

**Steps:**
1. GET /scan/state -> identify stuck state
2. POST /scan/stop -> force transition to ERROR -> IDLE
3. If stop fails: restart server
4. Check tube state before retry

## E6: Pixel Coordinate Mismatch

**Severity:** LOW — clicks land on wrong UI elements

**Symptoms:** Profile selection fails, buttons unresponsive, wrong values entered

**Steps:**
1. Resolution changed or WinWerth theme updated
2. Run /autopilot-extract to rediscover automation_ids
3. Update winWerth_data.json with new coordinates
4. Test with /autopilot-calibrate before running scans
