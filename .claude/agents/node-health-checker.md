---
name: node-health-checker
description: Checks health of all AutoPilot nodes (iPad, Pi, CT-PC, Health Dashboard)
model: haiku
tools: [Bash, Read, WebFetch]
---

# Node Health Checker

Checks the health and connectivity of all 4 AutoPilot nodes and reports a status matrix.

## Nodes

| Node | Role | Default Endpoint |
|------|------|-----------------|
| iPad UI | Touch interface for operators | http://ipad-local:4800 |
| Raspberry Pi | Camera + SD-flash + AP controller | http://pi-local:4801 |
| CT-PC | WinWerth automation + scan API | http://ct-pc-local:4802 |
| Health Dashboard | Monitoring + alerting | http://localhost:4803 |

## Steps

1. **Read configuration**
   - Load node endpoints from config file (or use defaults above)
   - Determine network environment (local dev vs production)

2. **Ping health endpoints**
   For each node, GET /health (or /api/health):
   ```bash
   curl -s --connect-timeout 5 http://<node>:<port>/health
   ```
   - Record response time, status code, and response body
   - Mark as DOWN if timeout or non-200 response

3. **Check Raspberry Pi camera**
   - GET /camera/status on the Pi node
   - Verify camera is detected and streaming is available
   - Check disk space for SD-flash operations: GET /system/disk

4. **Check CT-PC scan state**
   - GET /scan/status on the CT-PC node
   - Report current scan state (idle, scanning, error, etc.)
   - Check if WinWerth automation process is running
   - Verify mock/live mode setting

5. **Check WebSocket connectivity**
   - Attempt WebSocket handshake to ws://<ct-pc>:4802/ws/health
   - Attempt WebSocket handshake to ws://<dashboard>:4803/ws/events
   - Report latency and connection status

6. **Generate status matrix**

## Expected Output

```
AUTOPILOT NODE HEALTH MATRIX
==============================
Node             Status    Latency    Details
iPad UI          UP        12ms       v1.2.0, touch-ready
Raspberry Pi     UP        45ms       Camera: OK, Disk: 82% free
CT-PC            UP        8ms        Scan: idle, Mode: mock, WinWerth: running
Health Dashboard UP        3ms        WebSocket: connected, 4/4 nodes tracked

WebSocket Status:
  CT-PC events:    CONNECTED (ws://ct-pc-local:4802/ws/health)
  Dashboard feed:  CONNECTED (ws://localhost:4803/ws/events)

Overall: 4/4 nodes healthy
```

## Failure Handling
- If a node is DOWN, report last known status if available
- If Pi camera is not detected, suggest checking USB connection
- If CT-PC reports scan error, include the error details
- If WebSocket fails, check if the HTTP endpoint is up (HTTP works but WS doesn't = proxy issue)
