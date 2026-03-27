---
name: autopilot-calibrate
description: Run WinWerth calibration — Hell/Dunkelkorrektur, voltage/ampere tuning, and Bilddynamik check.
user_invocable: true
allowed-tools: [Bash, Read, WebFetch]
---

# /autopilot-calibrate — WinWerth Calibration Sequence

Run the WinWerth CT calibration pipeline via the CT-PC API. Performs Hell/Dunkelkorrektur (bright/dark correction), tunes voltage and ampere settings, and verifies Bilddynamik is within the acceptable 20-220 range.

## When to Use

- Before the first scan of the day
- After changing the sensor or detector
- When Bilddynamik values are out of range during a scan
- After WinWerth software updates or hardware maintenance
- When scan quality has degraded (artifacts, noise)

## Steps

1. **Verify CT-PC API is reachable**
   ```bash
   curl -sf http://localhost:4802/health --max-time 5
   ```
   - Confirm WinWerth is connected and tube is off
   - If not ready, run `/autopilot-health` first

2. **Run Dunkelkorrektur (dark correction)**
   - Captures reference images with no X-ray (tube off):
     ```bash
     curl -X POST http://localhost:4802/calibrate/dark-correction
     ```
   - Wait for completion (typically 30-60 seconds)
   - Verify dark reference was saved:
     ```bash
     curl -s http://localhost:4802/calibrate/status
     ```

3. **Activate tube for bright correction**
   - Turn on the X-ray tube at a safe low power:
     ```bash
     curl -X POST http://localhost:4802/calibrate/tube-on \
       -H "Content-Type: application/json" \
       -d '{"voltage": 100, "current": 100}'
     ```
   - Wait for tube warmup (status changes from "warming" to "ready")

4. **Run Hellkorrektur (bright correction)**
   - Captures reference images with X-ray active (no part in beam):
     ```bash
     curl -X POST http://localhost:4802/calibrate/bright-correction
     ```
   - IMPORTANT: Ensure no part is placed in the CT scanner during bright correction

5. **Tune voltage and ampere**
   - Adjust to target voltage and current for the planned scan:
     ```bash
     curl -X POST http://localhost:4802/calibrate/tune \
       -H "Content-Type: application/json" \
       -d '{"targetVoltage": <kV>, "targetCurrent": <uA>}'
     ```
   - The API ramps voltage/current gradually to avoid tube stress

6. **Check Bilddynamik**
   - Read the current image dynamics value:
     ```bash
     curl -s http://localhost:4802/calibrate/dynamics
     ```
   - Expected: value between 20 and 220
   - If too low (<20): Increase voltage or current, or increase integration time
   - If too high (>220): Decrease voltage or current, or decrease integration time
   - Adjust and re-check:
     ```bash
     curl -X POST http://localhost:4802/calibrate/adjust-dynamics \
       -H "Content-Type: application/json" \
       -d '{"integrationTime": <ms>}'
     ```

7. **Run rotation preview**
   - Verify the part is centered and dynamics stay in range through full rotation:
     ```bash
     curl -X POST http://localhost:4802/calibrate/rotation-preview
     ```
   - Reports min/max dynamics across all rotation angles
   - If any angle is out of range, suggests repositioning the part

8. **Save calibration profile**
   - Store the calibrated settings for reuse:
     ```bash
     curl -X POST http://localhost:4802/calibrate/save \
       -H "Content-Type: application/json" \
       -d '{"profileName": "<part-type>-<date>"}'
     ```

## What's Next

- `/autopilot-scan` — Calibration complete, ready to scan
- `/autopilot-extract` — Re-extract UI elements if calibration controls were not found
- `/autopilot-health` — Verify system state after calibration
