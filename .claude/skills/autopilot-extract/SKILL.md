---
name: autopilot-extract
description: Extract WinWerth UI automation IDs using pywinauto and update winWerth_data.json.
user_invocable: true
allowed-tools: [Bash, Read, Write, Grep]
---

# /autopilot-extract — WinWerth UI Element Extraction

Run pywinauto inspection on the WinWerth application to discover automation_ids for all interactive UI elements (buttons, textboxes, checkboxes, labels, tabs). Updates the `winWerth_data.json` mapping file used by the CT-PC API for scan automation.

## When to Use

- Setting up a new WinWerth PC for the first time
- After a WinWerth software update that may have changed UI elements
- When a scan step fails because an automation ID is not found
- To discover new UI elements for extending automation coverage

## Steps

1. **Verify WinWerth is running**
   - Check that the WinWerth application is open and visible:
     ```bash
     curl -s http://localhost:4802/winwerth/status
     ```
   - If not running, ask the user to launch WinWerth manually

2. **Read current winWerth_data.json**
   - Load the existing element mapping to understand what is already mapped:
     ```bash
     cat apps/ct-pc-api/data/winWerth_data.json
     ```
   - Note which elements are present and which may be missing

3. **Run full UI tree extraction**
   - Execute the extraction script on the CT-PC (via API or directly):
     ```bash
     curl -X POST http://localhost:4802/extract/full-tree
     ```
   - Or run directly on the Windows PC:
     ```bash
     python scripts/extract_ui_elements.py --output data/extraction_raw.json
     ```
   - This dumps the entire UIA element tree with automation_id, control_type, name, and bounding_rect

4. **Extract specific window/tab elements**
   - Target specific areas of the WinWerth UI:
     ```bash
     # CT measurement tab
     curl -X POST http://localhost:4802/extract/tab -d '{"tab": "CT"}'

     # Sensor selection panel
     curl -X POST http://localhost:4802/extract/panel -d '{"panel": "Sensor"}'

     # Export dialog
     curl -X POST http://localhost:4802/extract/dialog -d '{"dialog": "Export"}'
     ```

5. **Review extracted elements**
   - Compare raw extraction against the current winWerth_data.json
   - Identify key elements needed for the 7-step workflow:
     - **Step 1**: Sensor dropdown, size profile radio buttons
     - **Step 2**: CT tab button/header
     - **Step 3**: Voltage, Current, Integration Time, Quality, Steps input fields
     - **Step 4**: Tube activation button (Roehre Ein/Aus)
     - **Step 5**: Rotation preview button, Bilddynamik display
     - **Step 6**: Messen button
     - **Step 7**: Kontur, VxVol, Grafik3D, Save buttons in export chain
   - Grep for specific German labels:
     ```bash
     grep -i "messen\|roehre\|kontur\|dynamik\|spannung\|strom" data/extraction_raw.json
     ```

6. **Update winWerth_data.json**
   - Merge newly discovered automation IDs into the mapping file
   - Preserve the structured format with sections per workflow step
   - Back up the previous version:
     ```bash
     cp apps/ct-pc-api/data/winWerth_data.json apps/ct-pc-api/data/winWerth_data.json.bak
     ```

7. **Validate the updated mapping**
   - Run the validation script to confirm all required elements are mapped:
     ```bash
     curl -X POST http://localhost:4802/extract/validate
     ```
   - This checks that every automation ID in winWerth_data.json resolves to a live UI element

## What's Next

- `/autopilot-scan` — Test the updated element mapping with a full scan
- `/autopilot-deploy` — Redeploy the CT-PC API with the updated mapping
- `/autopilot-calibrate` — Verify calibration elements are correctly mapped
- `/autopilot-health` — Confirm the CT-PC API is healthy after the update
