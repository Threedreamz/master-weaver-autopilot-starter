---
name: autopilot-stl
description: Export STL files from WinWerth, run Soll-Ist comparison, and view deviation reports.
user_invocable: true
allowed-tools: [Bash, Read, WebFetch, Glob]
---

# /autopilot-stl — STL Export and Analysis

Trigger STL export from WinWerth (Kontur -> VxVol -> Grafik3D -> Save), run Soll-Ist (nominal vs. actual) comparison against CAD reference models, and view deviation reports with color maps.

## When to Use

- After a completed CT scan to export the mesh
- To re-export an STL from existing scan data
- To compare a scanned part against its CAD model
- To review deviation reports for quality control

## Steps

1. **Check for completed scan data**
   ```bash
   curl -s http://localhost:4802/scan/status
   ```
   - Confirm a scan has completed and volumetric data is available
   - If no scan data exists, run `/autopilot-scan` first

2. **Trigger STL export pipeline**
   - Execute the 4-step export chain in WinWerth:
     ```bash
     curl -X POST http://localhost:4802/export/stl \
       -H "Content-Type: application/json" \
       -d '{"outputName": "<part-name>", "outputDir": "D:/CT-Scans/output"}'
     ```
   - Pipeline steps:
     1. **Kontur** — Extract surface contour from volumetric data
     2. **VxVol** — Convert voxel volume to mesh
     3. **Grafik3D** — Render 3D graphics for preview
     4. **Save** — Export final STL file
   - Monitor progress:
     ```bash
     curl -s http://localhost:4802/export/status
     ```

3. **Verify STL output**
   - Check the exported file exists and has reasonable size:
     ```bash
     curl -s http://localhost:4802/export/result
     ```
   - Expected: file path, size in MB, vertex count, triangle count
   - Typical STL size: 5-500 MB depending on resolution and part complexity

4. **List available STL files**
   - Browse previous exports:
     ```bash
     curl -s http://localhost:4802/export/list
     ```
   - Shows: filename, date, size, associated scan parameters

5. **Run Soll-Ist comparison (optional)**
   - Compare the scanned STL against a CAD reference model:
     ```bash
     curl -X POST http://localhost:4802/analysis/soll-ist \
       -H "Content-Type: application/json" \
       -d '{"scanStl": "<scan-file>.stl", "referenceStl": "<cad-file>.stl", "tolerance": 0.05}'
     ```
   - Tolerance in mm (default: 0.05mm for precision parts)

6. **View deviation report**
   ```bash
   curl -s http://localhost:4802/analysis/deviation-report?scan=<scan-file>
   ```
   - Report includes:
     - **Max deviation**: Largest positive and negative deviation in mm
     - **Mean deviation**: Average deviation across all points
     - **Sigma**: Standard deviation
     - **In-tolerance percentage**: Percentage of surface within specified tolerance
     - **Color map URL**: Visual deviation heat map (red = over, blue = under, green = within tolerance)

7. **Export deviation report**
   ```bash
   curl -X POST http://localhost:4802/analysis/export-report \
     -H "Content-Type: application/json" \
     -d '{"scan": "<scan-file>", "format": "pdf"}'
   ```
   - Formats: pdf, csv, json

## What's Next

- `/autopilot-scan` — Run another scan with adjusted parameters if deviations are too high
- `/autopilot-calibrate` — Recalibrate if systematic deviations are detected
- `/autopilot-status` — View scan history and compare multiple measurements
