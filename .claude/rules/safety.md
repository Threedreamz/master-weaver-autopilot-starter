# CT Scanner Safety Rules

## Radiation Safety (CRITICAL)

- X-ray tube emits ionizing radiation when powered — treat every tube-on state as an active radiation hazard
- Door interlock MUST be green before executing "Rohre an" — NEVER bypass interlock checks
- NEVER leave the tube powered on unattended
- NEVER send tube power commands without verifying current tube status first via GET /status
- If tube state is unknown after an error: **assume the tube is ON** and verify via the /status endpoint
- Always verify tube is off after scan completes, regardless of success or failure
- Emergency stop procedure: POST /scan/stop -> verify tube_on=false via GET /status -> physical power check if API unreachable

## Damage Prevention

- **WinWerth is single-instance** — NEVER run multiple pywinauto processes simultaneously
- **200ms minimum between UI commands** — pywinauto is not thread-safe, faster sequences cause UI race conditions
- **NEVER send concurrent mouse clicks** — MouseController has a lock for this reason; always route through it
- **Scan timeout 600s is a HARD safety limit** — do not increase this value; it prevents runaway tube operation
- **Error correction max 10 iterations** — prevents infinite voltage adjustment loops; escalate to manual intervention after
- **pyautogui.FAILSAFE=True** — moving mouse to screen corner (0,0) triggers emergency stop
- Queue all WinWerth commands through the command sequencer, never fire-and-forget
- pywinauto `click_input()` requires the real mouse cursor — no concurrent UI automation operations

## Data Protection

- STL files may contain proprietary part geometry — treat as confidential, never expose to public endpoints
- `winWerth_data.json` contains calibrated pixel coordinates — backup before editing, restore from git if corrupted
- Scan data path (`Y:\3D-Druck_CT\`) may be on a network drive — verify it is writeable before starting a scan
- NEVER overwrite an existing STL file without explicit user confirmation
- STL save path must exist before triggering export — create directories if needed
- Default export path: `Y:\3D-Druck_CT\Auftage-2023`
- Validate file write succeeded before reporting export complete

## Recovery Procedures

- **Stuck scan:** POST /scan/stop -> wait 5s -> GET /status -> verify state is IDLE
- **Tube won't turn off:** run emergency-stop.ts -> physical CT-PC power check
- **State machine in ERROR:** GET /scan/state -> POST /scan/stop -> verify IDLE before retry
- **WinWerth window lost:** controller auto-detects via `win_api.find_window_by_title()` -> falls back to mock mode
- **Config corrupted:** restore `winWerth_data.json` from git -> restart server

## Operational Limits

| Parameter | Limit | Reason |
|-----------|-------|--------|
| Scan timeout | 600s (10 min) | Prevents runaway tube operation |
| Error correction retries | 10 | Prevents infinite voltage oscillation |
| Command interval | 200ms | pywinauto thread safety |
| Bilddynamik range | 20-220 | Below 20: underexposed. Above 220: saturated |
| Tube warmup | varies | Never skip Aufwarmphase on cold start |
| Concurrent scans | 1 | asyncio.Lock prevents, but always verify |
| Profile window timeout | 10s | getCTSensorDlg waits max 10s |

## Pixel Coordinates

- All UI coordinates are defined in `winWerth_data.json` — load via `src/winwerth/config.py`
- NEVER hardcode pixel positions in source code
- Coordinates are resolution-dependent — verify on the actual CT-PC screen before use
- If resolution changes, re-run discovery tools in `z_extract/` to update coordinates

## Network

- CT-PC server: port 4802
- Raspberry Pi: port 4801
- iPad UI: port 4800
- Health endpoints: port 4803 for all services
- All devices must be on the same network (AutoPilot-CT AP or shared LAN)

## Mock Mode

- Server auto-detects mock mode when not running on Windows or WinWerth executable not found
- Mock mode is safe for development and testing — all hardware commands are simulated
- NEVER deploy mock mode to the production CT-PC — verify `MOCK_MODE=false` before production use
- Mock responses should mirror real WinWerth timing (include artificial delays)
