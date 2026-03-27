#!/usr/bin/env npx tsx
/**
 * AutoPilot WinWerth Safety Hook — pre-write validation for CT-Scanner files.
 *
 * Protects hardware-specific configuration and safety-critical modules from
 * accidental or dangerous edits. This is a PRE-WRITE hook.
 *
 * BLOCKS:
 *   - Hardcoded pixel coordinates in Python files (must use config.py)
 *   - Deletion of winWerth_data.json (calibration data)
 *   - Writes to tube.py / rohr.py without explicit warning (X-ray tube control)
 *
 * WARNS:
 *   - Edits to winWerth_data.json (hardware-calibrated coordinates)
 *   - Edits to pywinauto library files (battle-tested automation)
 *   - Edits to error_correction/ (recovery algorithms)
 *   - Edits to orchestrator/transitions.py (timeout values are safety limits)
 *   - Edits to scan state machine files
 *   - New pixel coordinates out of 4K range in JSON files
 */

const filePath = process.argv[2] || "";
const content = process.argv.slice(3).join(" ");

const result: { status: string; message: string } = { status: "pass", message: "" };

// Normalize path separators for cross-platform matching
const fp = filePath.replace(/\\/g, "/");

// -------------------------------------------------------------------------
// BLOCK: Deletion of winWerth_data.json — this is calibrated hardware data
// (Claude Code passes empty content for file deletion in some cases)
// -------------------------------------------------------------------------
if (fp.includes("winWerth_data.json") && (!content || content.trim() === "")) {
  result.status = "block";
  result.message =
    "BLOCKED: Deleting winWerth_data.json would destroy hardware-calibrated " +
    "pixel coordinates. This file must be regenerated on the CT-PC using " +
    "/autopilot-extract if coordinates become invalid. Deletion is not allowed.";
  console.log(JSON.stringify(result));
  process.exit(0);
}

// -------------------------------------------------------------------------
// BLOCK: Hardcoded pixel coordinates in Python files (must use config.py)
// -------------------------------------------------------------------------
if (fp.endsWith(".py") && !fp.includes("config.py") && !fp.includes("test")) {
  const hardcodedCoordPattern =
    /\b(?:click|move_to|moveTo|move|position|locateOnScreen|press|hotkey)\s*\(\s*\d{2,4}\s*,\s*\d{2,4}\s*\)/;
  if (hardcodedCoordPattern.test(content)) {
    result.status = "block";
    result.message =
      "BLOCKED: Hardcoded pixel coordinates detected in Python file. " +
      "All screen coordinates MUST be defined in config.py (sourced from " +
      "winWerth_data.json) and referenced by name. Hardcoded coordinates break " +
      "when screen resolution, DPI, or window position changes on the CT-PC.";
    console.log(JSON.stringify(result));
    process.exit(0);
  }
}

// -------------------------------------------------------------------------
// BLOCK/WARN: Writes to tube.py / rohr.py — X-ray tube control modules
// These modules directly control radiation-emitting hardware.
// -------------------------------------------------------------------------
if (/\b(tube|rohr)\.py$/.test(fp)) {
  result.status = "warn";
  result.message =
    "SAFETY WARNING: You are editing an X-ray tube control module (tube.py/rohr.py). " +
    "This code directly controls radiation-emitting hardware. Changes to: " +
    "- Power on/off sequences can leave the tube energized " +
    "- Timeout values are SAFETY LIMITS (not performance tuning) " +
    "- Status polling intervals affect radiation monitoring " +
    "Review changes with extreme care. Test in MOCK mode first.";
}

// -------------------------------------------------------------------------
// WARN: winWerth_data.json edits — hardware-calibrated coordinates
// -------------------------------------------------------------------------
if (fp.includes("winWerth_data.json") && result.status === "pass") {
  // Validate coordinate ranges in the new content
  const coordIssues: string[] = [];
  try {
    const data = JSON.parse(content);
    const checkCoords = (obj: any, prefix: string): void => {
      if (typeof obj !== "object" || obj === null) return;
      for (const [k, v] of Object.entries(obj)) {
        if (typeof v !== "object" || v === null) continue;
        const val = v as Record<string, unknown>;
        if ("x" in val && "y" in val) {
          const { x, y } = val;
          if (typeof x === "number" && (x < 0 || x > 3840))
            coordIssues.push(`${prefix}.${k}: x=${x} outside 4K range (0-3840)`);
          if (typeof y === "number" && (y < 0 || y > 2160))
            coordIssues.push(`${prefix}.${k}: y=${y} outside 4K range (0-2160)`);
        } else {
          checkCoords(v, `${prefix}.${k}`);
        }
      }
    };
    checkCoords(data, "root");
  } catch {
    // Content may not be full JSON (partial edit) — skip validation
  }

  if (coordIssues.length > 0) {
    result.status = "block";
    result.message =
      "BLOCKED: Pixel coordinates out of 4K range (3840x2160) detected: " +
      coordIssues.join("; ") +
      ". Coordinates must match the CT-PC screen resolution. " +
      "Verify on the actual CT-PC before committing.";
  } else {
    result.status = "warn";
    result.message =
      "WARNING: winWerth_data.json contains hardware-specific pixel coordinates " +
      "calibrated to the CT-PC screen. Only edit after verifying on the actual " +
      "CT-PC screen resolution. Wrong values cause WinWerth UI mis-clicks which " +
      "can trigger unintended scan operations or leave dialogs in wrong state.";
  }
}

// -------------------------------------------------------------------------
// WARN: pywinauto library files — battle-tested automation code
// -------------------------------------------------------------------------
if (fp.includes("source/libs/pywinauto/") || fp.includes("libs/pywinauto/")) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: source/libs/pywinauto/ contains battle-tested CT-PC automation code. " +
      "Changes here directly affect how the software interacts with WinWerth UI. " +
      "Test thoroughly on the actual Windows CT-PC before merging. " +
      "Broken automation can leave WinWerth in an inconsistent UI state.";
  }
}

// -------------------------------------------------------------------------
// WARN: error_correction/ — recovery algorithms for scan failures
// These algorithms handle mid-scan errors and prevent hardware damage.
// -------------------------------------------------------------------------
if (fp.includes("error_correction/") || fp.includes("error_correction\\")) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: error_correction/ contains algorithms that recover from mid-scan " +
      "failures. These prevent hardware damage by detecting stuck states, dialog " +
      "popups, and automation failures. Changes could cause error recovery to fail, " +
      "potentially leaving the X-ray tube powered during an error condition. " +
      "Test all error scenarios in MOCK mode before deploying.";
  }
}

// -------------------------------------------------------------------------
// WARN: orchestrator/transitions.py — state machine with safety timeouts
// Timeout values in this file are SAFETY LIMITS, not performance parameters.
// -------------------------------------------------------------------------
if (fp.includes("orchestrator/transitions") || fp.includes("orchestrator\\transitions")) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: orchestrator/transitions.py defines the scan state machine, " +
      "including timeout values that serve as SAFETY LIMITS. " +
      "- SCAN_TIMEOUT (600s) = max X-ray tube on-time per scan cycle " +
      "- STATE_TIMEOUT (60s) = max time in any single state before abort " +
      "- COOLDOWN_TIME (30s) = mandatory pause between scans " +
      "Increasing timeouts increases radiation exposure duration. " +
      "Decreasing them may abort legitimate long scans. " +
      "Changes require review by someone who understands the CT hardware.";
  }
}

// -------------------------------------------------------------------------
// WARN: Scan state machine files (beyond transitions)
// -------------------------------------------------------------------------
if ((fp.includes("orchestrator/") || fp.includes("state_machine")) &&
    fp.endsWith(".py") && result.status === "pass") {
  result.status = "warn";
  result.message =
    "WARNING: This file is part of the scan orchestration / state machine. " +
    "The state machine controls the sequence: idle -> scanning -> exporting -> idle. " +
    "Incorrect transitions can leave the system in a stuck state with the tube on. " +
    "Ensure every state has a timeout path back to idle.";
}

// -------------------------------------------------------------------------
// WARN: FastAPI endpoint definitions (the safety API surface)
// -------------------------------------------------------------------------
if ((fp.includes("main.py") || fp.includes("routes/") || fp.includes("api/")) &&
    fp.endsWith(".py") && result.status === "pass") {
  if (/\b(tube|scan|rohr)\b/i.test(content) && /\b(post|put|delete)\b/i.test(content)) {
    result.status = "warn";
    result.message =
      "WARNING: Editing API endpoints that control tube or scan operations. " +
      "These endpoints are the safety boundary between the user and the hardware. " +
      "Ensure: 1) All mutating endpoints check tube state before acting, " +
      "2) Error responses include tube state for debugging, " +
      "3) Timeout enforcement is preserved in scan endpoints.";
  }
}

console.log(JSON.stringify(result));
