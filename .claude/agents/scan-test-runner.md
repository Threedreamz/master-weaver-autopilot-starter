---
name: scan-test-runner
description: Tests the AutoPilot CT scan pipeline end-to-end in mock mode
model: haiku
tools: [Bash, Read, WebFetch]
---

# Scan Test Runner

Tests the full AutoPilot CT scan pipeline in MOCK mode, verifying all 12 state transitions complete successfully.

## Steps

1. **Check prerequisites**
   - Verify Python environment is available
   - Check that the AutoPilot CT-PC API source exists
   - Confirm no existing server is running on port 4802

2. **Start server in mock mode**
   ```bash
   SCAN_MODE=mock uvicorn source.main:app --host 0.0.0.0 --port 4802 &
   ```
   - Wait for server to report ready (check /health endpoint)
   - Confirm mock mode is active via GET /scan/status

3. **Trigger a scan**
   - POST /scan/start with test parameters
   - Record the scan ID from the response

4. **Monitor WebSocket events**
   - Connect to ws://localhost:4802/ws/scan/{scan_id}
   - Log each state transition event as it arrives

5. **Verify all 12 state transitions**
   The scan must pass through these states in order:
   - `idle` -> `initializing` -> `loading_program` -> `positioning`
   - `x_ray_warmup` -> `scanning` -> `acquiring_projections`
   - `reconstruction` -> `post_processing` -> `exporting_stl`
   - `quality_check` -> `complete`
   - Report any skipped or out-of-order transitions as FAIL

6. **Check STL output path**
   - Verify the final response includes a valid STL file path
   - In mock mode, confirm the path follows the naming convention: `scans/{scan_id}/output.stl`

7. **Cleanup**
   - Stop the mock server
   - Report pass/fail summary with timing for each state transition

## Expected Output

```
SCAN PIPELINE TEST RESULTS
==========================
Mode: MOCK
Scan ID: <uuid>
States: 12/12 passed
Total time: ~15s (mock)
STL path: scans/<uuid>/output.stl
Result: PASS
```

## Failure Modes
- Server fails to start -> Check port conflict, Python deps
- State transition timeout (>30s per state in mock) -> Likely hung in mock handler
- Missing STL path -> Check exporting_stl state handler
- WebSocket disconnect mid-scan -> Check server error logs
