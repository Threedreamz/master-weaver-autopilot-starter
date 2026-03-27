#!/usr/bin/env npx tsx
/**
 * AutoPilot Tube Safety Hook — pre-bash hook for X-ray tube / radiation safety.
 *
 * BLOCKS: Direct tube power commands without safety checks
 * WARNS:  Scan start in LIVE mode, direct pyautogui/pywinauto, API process kills
 *
 * This hook complements scan-safety-hook.ts (which handles scan lifecycle).
 * This hook focuses on RADIATION safety — tube power, interlocks, direct automation.
 */

const command = process.argv.slice(2).join(" ");
const result: { status: string; message: string } = { status: "pass", message: "" };

// -------------------------------------------------------------------------
// BLOCK: Direct tube power-on commands via curl/httpie
// The tube should only be activated through the scan pipeline which includes
// interlock checks, status polling, timeout limits, and auto-shutdown.
// -------------------------------------------------------------------------
if (/\b(curl|httpie|http|wget|fetch)\b/i.test(command) &&
    /\/tube\/(on|power|activate|start|enable)/i.test(command)) {
  result.status = "block";
  result.message =
    "BLOCKED: Direct X-ray tube power commands are extremely dangerous. " +
    "The tube must only be activated through the scan pipeline (/scan/start) " +
    "which includes: interlock verification, warm-up sequence, status polling, " +
    "timeout limits (600s), and automatic shutdown on error. " +
    "Use /autopilot-scan skill which wraps these safety checks.";
}

// -------------------------------------------------------------------------
// WARN: /scan/start in potentially LIVE mode
// This overlaps with scan-safety-hook but adds tube-specific guidance.
// -------------------------------------------------------------------------
if (/\b(curl|httpie|http|wget|fetch)\b/i.test(command) &&
    /\/scan\/start/i.test(command) &&
    !/mock/i.test(command)) {
  // Only set if not already blocked
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: /scan/start will activate the X-ray tube in LIVE mode. " +
      "Pre-flight checklist: " +
      "1) Door interlock engaged (indicator green on WinWerth), " +
      "2) Workpiece positioned and secured, " +
      "3) No personnel near CT chamber, " +
      "4) CT-PC WinWerth application is running. " +
      "Add SCAN_MODE=mock to the request for safe testing.";
  }
}

// -------------------------------------------------------------------------
// WARN: Direct pyautogui/pywinauto commands bypass safety pipeline
// The FastAPI endpoints include error correction, state verification,
// and timeout handling. Direct automation skips all of that.
// -------------------------------------------------------------------------
if (/python.*-c.*(?:pyautogui|pywinauto|click|press|hotkey|typewrite)/i.test(command) ||
    /python.*(?:pyautogui|pywinauto).*(?:click|press|move)/i.test(command)) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: Direct pyautogui/pywinauto commands bypass the safety pipeline. " +
      "The FastAPI endpoints at :4802 include: tube state verification, " +
      "error correction algorithms, coordinate validation from winWerth_data.json, " +
      "and scan timeout enforcement. Use the API endpoints instead.";
  }
}

// -------------------------------------------------------------------------
// WARN: Killing API process during potential active scan
// If the API dies mid-scan, the tube may stay powered with no software control.
// -------------------------------------------------------------------------
if (/\b(kill|pkill|killall|taskkill)\b/i.test(command) &&
    /\b(uvicorn|python|fastapi|WerthAutopilot|ctpc|autopilot)/i.test(command)) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: Killing the CT-PC API during an active scan could leave the X-ray tube " +
      "powered with NO software control. Check scan state first: " +
      "GET /status — if scan_active is true, use POST /scan/stop first, then wait " +
      "for tube_on=false before killing the process.";
  }
}

// -------------------------------------------------------------------------
// WARN: Restarting services that manage tube state
// -------------------------------------------------------------------------
if (/\b(systemctl|supervisorctl|service)\s+(restart|stop)\b/i.test(command) &&
    /\b(ct[-_]?api|scan[-_]?server|autopilot|WerthAutopilot)/i.test(command)) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "WARNING: Restarting the CT service while a scan may be active. " +
      "Verify no scan is in progress (GET /status) before restarting. " +
      "A service restart during scan leaves the tube in an uncontrolled state.";
  }
}

// -------------------------------------------------------------------------
// WARN: SSH/remote commands to CT-PC (informational)
// -------------------------------------------------------------------------
if (/\bssh\b/i.test(command) && /\b(ct[-_]?pc|werth|4802)\b/i.test(command)) {
  if (result.status === "pass") {
    result.status = "warn";
    result.message =
      "NOTE: Connecting to CT-PC via SSH. Be aware that commands on the CT-PC " +
      "can directly affect X-ray tube state and WinWerth automation. " +
      "Check /status before making changes.";
  }
}

console.log(JSON.stringify(result));
