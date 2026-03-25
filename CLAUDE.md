# master-weaver-autopilot-starter

AutoPilot — Remote control and automation for the Werth X-ray Tomograph (CT Scanner).

## Architecture

4-node system:
- **iPad App** (`apps/ipad/`, port 4800) — Touch-optimized Next.js scan control UI
- **Raspberry Pi** (`python/pi-firmware/`, port 4801) — 2× 4K camera streaming + mDNS discovery
- **CT-PC API** (`python/ctpc-api/`, port 4802) — FastAPI server wrapping WinWerth automation
- **Health Dashboard** (`apps/health/`, port 4803) — Real-time 4-node monitoring

## Quick Start

```bash
# JS apps (iPad + Health Dashboard)
pnpm install
pnpm dev --filter=ipad
pnpm dev --filter=health

# Python CT-PC API (Windows only)
cd python/ctpc-api
pip install -e .
uvicorn src.main:app --host 0.0.0.0 --port 4802

# Raspberry Pi (on Pi hardware)
cd python/pi-firmware
npm install
node src/server.ts
```

## Directory Structure

```
apps/
  ipad/           Next.js iPad scan UI (port 4800)
  health/         Next.js health dashboard (port 4803)
python/
  ctpc-api/       FastAPI WinWerth automation server (port 4802)
  pi-firmware/    Node.js camera server for Raspberry Pi (port 4801)
packages/
  autopilot-types/  Shared TypeScript types
  autopilot-ws/     WebSocket protocol definitions
```

## Conventions

- Ports: 4800-4804 (autopilot ecosystem range)
- WinWerth control: NEVER send commands faster than 200ms apart (UI needs processing time)
- Pixel coordinates: All in `python/ctpc-api/winWerth_data.json` — resolution-dependent!
- Camera streams: MJPEG over HTTP, snapshots via REST
- Health: Every service exposes `/health` or `/api/health`

## Safety

- CT-PC API is Windows-only (PyAutoGUI + PyWinAuto)
- Raspberry Pi firmware is Linux/ARM64-only
- iPad app and Health Dashboard are deployable to Railway
- NEVER send tube power commands without status verification first
- NEVER modify winWerth_data.json without testing on actual CT-PC screen resolution
