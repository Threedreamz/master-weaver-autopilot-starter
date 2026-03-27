# AutoPilot Conventions

## Port Registry
| Service | Port |
|---------|------|
| iPad UI | 4800 |
| Pi (firmware/AP) | 4801 |
| CT-PC (WinWerth API) | 4802 |
| Health endpoints | 4803 |
| Setup / Orchestrator | 4804 |

All ports in the 4800-4829 ecosystem block as registered in `ecosystem.json`.

## Monorepo Structure
```
apps/              Next.js web applications (iPad UI, health dashboard)
packages/          Shared TypeScript packages
python/            Python services
  ctpc-api/src/    MW FastAPI clean architecture (CT-PC server)
  pi-firmware/     Raspberry Pi firmware and AP management
source/            trello_era legacy code (battle-tested pywinauto automation)
scripts/           Build, flash, and deploy scripts
```

## Two Python Layers
- **`python/ctpc-api/src/`** — Master Weaver FastAPI clean architecture. New development goes here.
- **`source/`** — trello_era battle-tested pywinauto automation. Proven working code, do not rewrite without reason.
- **Bridge**: `src/winwerth/pywinauto_bridge.py` connects the two layers
- When adding new WinWerth automation, implement in the MW layer and delegate to trello_era handlers where they already exist

## State Machine
12 states define the scan lifecycle:
```
IDLE -> PROFILE_SELECT -> TUBE_ON -> ROTATE_PREVIEW -> GREEN_BOX
     -> ERROR_CORRECT -> SCANNING -> WAIT_COMPLETE -> EXPORT_STL
     -> ANALYSE -> DONE -> ERROR
```
- State transitions are strictly ordered — no skipping states
- ERROR state can be reached from any state
- IDLE is the only valid starting state after a reset

## Configuration
- `winWerth_data.json` holds all UI coordinates, control identifiers, and scan parameters
- Load configuration via `src/winwerth/config.py` — never read JSON directly
- Never edit `winWerth_data.json` without testing on the actual screen resolution
- Config changes require a server restart to take effect

## Offline Network
- Raspberry Pi 5 broadcasts WiFi access point "AutoPilot-CT"
- iPad and CT-PC connect to this AP — no internet required for local operation
- Pi acts as DHCP server and network bridge
- Internet connectivity is optional (for remote monitoring and updates only)

## Deployment
| Target | Method | Command |
|--------|--------|---------|
| CT-PC | PyInstaller | `build.bat` produces `dist/WerthAutopilot.exe` |
| Raspberry Pi | SD card flash | `scripts/flash-pi.sh` writes image to SD |
| iPad UI / Health | Next.js build | `pnpm build` in respective app directory |
