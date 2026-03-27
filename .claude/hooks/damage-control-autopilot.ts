#!/usr/bin/env npx tsx
/**
 * AutoPilot Damage Control — classifies errors by severity for CT-Scanner domain.
 *
 * Severity levels:
 *   CRITICAL: Tube stuck on, scan timeout, radiation/interlock errors -> triggers emergency stop
 *   HIGH:     State machine stuck, communication lost, WinWerth missing
 *   MEDIUM:   Config errors, export failures, profile issues
 *   LOW:      Mock mode issues, cosmetic failures
 *
 * Usage: npx tsx damage-control-autopilot.ts "error text here"
 * Output: JSON with severity, category, action, requiresEmergencyStop
 */

import * as fs from "fs";
import * as path from "path";
import { execSync } from "child_process";

const errorText = process.argv.slice(2).join(" ");

interface DamageAssessment {
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  action: string;
  requiresEmergencyStop: boolean;
}

function classify(error: string): DamageAssessment {
  const e = error.toLowerCase();

  // -----------------------------------------------------------------------
  // CRITICAL — X-ray tube / radiation safety (trigger emergency stop)
  // -----------------------------------------------------------------------

  // Tube stuck or not responding — radiation may be active without control
  if (
    e.includes("tube") &&
    (e.includes("stuck") || e.includes("timeout") || e.includes("not responding") || e.includes("hung"))
  ) {
    return {
      severity: "critical",
      category: "tube-safety",
      action:
        "X-ray tube is unresponsive. Run emergency-stop.ts immediately. " +
        "PHYSICALLY verify tube is off on the WinWerth PC display. " +
        "Do NOT restart scan until root cause is identified.",
      requiresEmergencyStop: true,
    };
  }

  // Scan exceeded timeout — tube may have been on for too long
  if (
    (e.includes("scan") && e.includes("timeout")) ||
    (e.includes("timeout") && e.includes("600"))
  ) {
    return {
      severity: "critical",
      category: "scan-timeout",
      action:
        "Scan exceeded safety timeout limit. Aborting scan and powering down tube. " +
        "Check WinWerth for error dialogs. Verify tube_on=false before proceeding.",
      requiresEmergencyStop: true,
    };
  }

  // Interlock or radiation keywords — physical safety
  if (e.includes("interlock") || e.includes("radiation") || e.includes("door open")) {
    return {
      severity: "critical",
      category: "radiation-safety",
      action:
        "RADIATION SAFETY ALERT. STOP ALL OPERATIONS. " +
        "Check door interlock status on CT chamber. " +
        "Verify no personnel are near the CT chamber. " +
        "Do NOT proceed until interlock shows green/engaged.",
      requiresEmergencyStop: true,
    };
  }

  // Thermal runaway — tube overheating
  if (e.includes("thermal") || (e.includes("temperature") && e.includes("exceed"))) {
    return {
      severity: "critical",
      category: "thermal-runaway",
      action:
        "Tube temperature exceeding safe limits. Emergency shutdown required. " +
        "Allow minimum 30 minutes cooldown before any restart attempt.",
      requiresEmergencyStop: true,
    };
  }

  // Multiple consecutive errors (sustained failure pattern)
  if (e.includes("consecutive") && e.includes("error") && /\d{3,}/.test(e)) {
    return {
      severity: "critical",
      category: "sustained-failure",
      action:
        "Sustained error pattern detected. Shutting down to prevent hardware damage. " +
        "Review error logs before restart.",
      requiresEmergencyStop: true,
    };
  }

  // -----------------------------------------------------------------------
  // HIGH — State machine / communication (no emergency stop, but investigate)
  // -----------------------------------------------------------------------

  // State machine stuck or invalid transition
  if (e.includes("state") && (e.includes("stuck") || e.includes("invalid transition") || e.includes("deadlock"))) {
    return {
      severity: "high",
      category: "state-machine",
      action:
        "State machine is stuck. Reset via POST /scan/stop, then verify with GET /status. " +
        "If state persists, restart the CT-PC API (after confirming tube is off).",
      requiresEmergencyStop: false,
    };
  }

  // Communication lost to CT-PC
  if (
    (e.includes("connection") && (e.includes("refused") || e.includes("timeout") || e.includes("reset"))) ||
    e.includes("econnrefused") ||
    e.includes("unreachable")
  ) {
    return {
      severity: "high",
      category: "communication-lost",
      action:
        "CT-PC API unreachable. Check: " +
        "1) Is uvicorn/WerthAutopilot running on port 4802? " +
        "2) Is the CT-PC powered on and network-connected? " +
        "3) Firewall blocking port 4802? " +
        "If a scan was active, PHYSICALLY check tube state on CT-PC.",
      requiresEmergencyStop: false,
    };
  }

  // WinWerth application not found/running
  if (e.includes("winwerth") && (e.includes("not found") || e.includes("not running") || e.includes("not detected"))) {
    return {
      severity: "high",
      category: "winwerth-missing",
      action:
        "WinWerth application not detected on CT-PC. " +
        "The API will run in MOCK mode (no real hardware interaction). " +
        "Start WinWerth.exe on the CT-PC for LIVE mode. " +
        "Check Task Manager for WinWerth process.",
      requiresEmergencyStop: false,
    };
  }

  // Pi (SD card flasher) unreachable
  if (e.includes("pi") && (e.includes("unreachable") || e.includes("ssh") || e.includes("connection"))) {
    return {
      severity: "high",
      category: "pi-communication",
      action:
        "Raspberry Pi unreachable. Check: " +
        "1) Pi is powered and booted (green LED blinking), " +
        "2) Network cable connected, " +
        "3) PI_URL in .env matches Pi's IP address.",
      requiresEmergencyStop: false,
    };
  }

  // -----------------------------------------------------------------------
  // MEDIUM — Config / export / UI automation errors
  // -----------------------------------------------------------------------

  // Config key missing (KeyError in Python)
  if ((e.includes("keyerror") || e.includes("key error") || e.includes("missing key")) &&
      (e.includes("config") || e.includes("winwerth_data") || e.includes("json"))) {
    return {
      severity: "medium",
      category: "config-error",
      action:
        "winWerth_data.json is missing a required key. " +
        "Run /autopilot-extract to rediscover UI element positions. " +
        "This usually happens after WinWerth updates or resolution changes.",
      requiresEmergencyStop: false,
    };
  }

  // STL export failure
  if (e.includes("stl") && (e.includes("export") || e.includes("save") || e.includes("failed"))) {
    return {
      severity: "medium",
      category: "stl-export-failure",
      action:
        "STL export failed. Check: " +
        "1) Save dialog responded (no blocking popup), " +
        "2) Target directory exists and is writable, " +
        "3) Disk space available, " +
        "4) File name contains no invalid characters.",
      requiresEmergencyStop: false,
    };
  }

  // Profile selection failure
  if (e.includes("profile") && (e.includes("not found") || e.includes("failed") || e.includes("select"))) {
    return {
      severity: "medium",
      category: "profile-error",
      action:
        "CT scan profile selection failed. Verify: " +
        "1) CT-Sensor window is open on WinWerth, " +
        "2) Profile name matches exactly (case-sensitive), " +
        "3) Run /autopilot-extract to refresh profile coordinates.",
      requiresEmergencyStop: false,
    };
  }

  // PyAutoGUI / coordinate errors
  if (e.includes("pyautogui") && (e.includes("fail") || e.includes("error") || e.includes("outside"))) {
    return {
      severity: "medium",
      category: "automation-error",
      action:
        "UI automation error. The CT-PC screen layout may have changed. " +
        "Check: 1) Screen resolution matches config (typically 1920x1080 or 3840x2160), " +
        "2) No unexpected dialogs covering the target area, " +
        "3) Run /autopilot-extract to recalibrate coordinates.",
      requiresEmergencyStop: false,
    };
  }

  // PyInstaller / build errors
  if (e.includes("pyinstaller") || (e.includes("build") && e.includes("exe"))) {
    return {
      severity: "medium",
      category: "build-error",
      action:
        "Executable build failed. Check PyInstaller output for missing modules. " +
        "Common fix: add hidden imports to the .spec file.",
      requiresEmergencyStop: false,
    };
  }

  // -----------------------------------------------------------------------
  // LOW — Non-dangerous issues
  // -----------------------------------------------------------------------

  if (e.includes("mock")) {
    return {
      severity: "low",
      category: "mock-mode",
      action:
        "Running in mock mode. This is expected on non-Windows systems or " +
        "when WinWerth is not available. No real hardware interaction.",
      requiresEmergencyStop: false,
    };
  }

  if (e.includes("deprecat")) {
    return {
      severity: "low",
      category: "deprecation",
      action: "Deprecation warning. Note for future update but not blocking.",
      requiresEmergencyStop: false,
    };
  }

  // Default
  return {
    severity: "low",
    category: "unknown",
    action: "Check error details and context. Retry if transient.",
    requiresEmergencyStop: false,
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
const assessment = classify(errorText);

// Log assessment for audit trail
const logDir = path.join(process.cwd(), ".claude", "logs");
const logFile = path.join(logDir, "damage-assessments.jsonl");
try {
  if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
  const entry = JSON.stringify({
    timestamp: new Date().toISOString(),
    error: errorText.substring(0, 500),
    ...assessment,
  });
  fs.appendFileSync(logFile, entry + "\n");
} catch {
  // Logging failure should not block assessment output
}

// If critical and requires emergency stop, trigger it
if (assessment.requiresEmergencyStop) {
  console.error("");
  console.error("  !!! CRITICAL: " + assessment.category.toUpperCase() + " !!!");
  console.error("  " + assessment.action);
  console.error("");

  // Attempt to trigger emergency stop
  const emergencyScript = path.join(__dirname, "emergency-stop.ts");
  if (fs.existsSync(emergencyScript)) {
    console.error(`  Triggering emergency stop: npx tsx ${emergencyScript} "${assessment.category}"`);
    try {
      execSync(`npx tsx "${emergencyScript}" "${assessment.category}"`, {
        stdio: "inherit",
        timeout: 15000,
      });
    } catch {
      console.error("  Emergency stop script failed — MANUALLY POWER OFF TUBE!");
    }
  } else {
    console.error("  emergency-stop.ts not found — MANUALLY POWER OFF TUBE!");
    console.error(`  Or run: curl -X POST ${process.env.CT_PC_URL || "http://localhost:4802"}/tube/off`);
  }
} else if (assessment.severity === "high") {
  console.error("");
  console.error("  [HIGH] " + assessment.category + ": " + assessment.action);
  console.error("");
}

console.log(JSON.stringify(assessment));
