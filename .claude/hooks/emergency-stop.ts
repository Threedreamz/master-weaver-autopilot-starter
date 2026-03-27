#!/usr/bin/env npx tsx
/**
 * AutoPilot Emergency Stop — powers down X-ray tube and aborts scan.
 * Triggered by: sustained errors, thermal runaway, or manual invocation.
 *
 * Usage: npx tsx emergency-stop.ts [reason]
 *
 * Actions:
 *   1. POST /scan/stop — abort any active scan
 *   2. POST /tube/off  — power down X-ray tube
 *   3. Log to .claude/logs/emergency-stops.json
 *   4. Output clear warning to user
 */

import * as fs from "fs";
import * as path from "path";

const reason = process.argv[2] || "manual emergency stop";
const CT_PC_URL = process.env.CT_PC_URL || "http://localhost:4802";
const LOG_FILE = path.join(process.cwd(), ".claude", "logs", "emergency-stops.json");

interface EmergencyLog {
  timestamp: string;
  reason: string;
  scanAbort: string;
  tubeOff: string;
  action: "emergency_stop";
}

async function emergencyStop(): Promise<void> {
  const timestamp = new Date().toISOString();
  let scanAbort = "unknown";
  let tubeOff = "unknown";

  console.error("");
  console.error("========================================");
  console.error("  EMERGENCY STOP TRIGGERED");
  console.error("========================================");
  console.error(`  Reason:    ${reason}`);
  console.error(`  Time:      ${timestamp}`);
  console.error(`  CT-PC URL: ${CT_PC_URL}`);
  console.error("----------------------------------------");

  // Step 1: Abort active scan
  try {
    const resp = await fetch(`${CT_PC_URL}/scan/stop`, {
      method: "POST",
      signal: AbortSignal.timeout(5000),
    });
    scanAbort = resp.ok ? "OK" : `HTTP ${resp.status}`;
    console.error(`  [1/2] Scan abort:  ${scanAbort}`);
  } catch (e: any) {
    scanAbort = `FAILED (${e.message || e})`;
    console.error(`  [1/2] Scan abort:  ${scanAbort}`);
  }

  // Step 2: Power down X-ray tube
  try {
    const resp = await fetch(`${CT_PC_URL}/tube/off`, {
      method: "POST",
      signal: AbortSignal.timeout(5000),
    });
    tubeOff = resp.ok ? "OK" : `HTTP ${resp.status}`;
    console.error(`  [2/2] Tube off:    ${tubeOff}`);
  } catch (e: any) {
    tubeOff = `FAILED (${e.message || e})`;
    console.error(`  [2/2] Tube off:    ${tubeOff}`);
  }

  // Step 3: Log emergency
  let logs: EmergencyLog[] = [];
  try {
    logs = JSON.parse(fs.readFileSync(LOG_FILE, "utf-8"));
  } catch {
    // File doesn't exist or invalid — start fresh
  }
  logs.push({ timestamp, reason, scanAbort, tubeOff, action: "emergency_stop" });

  const dir = path.dirname(LOG_FILE);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(LOG_FILE, JSON.stringify(logs, null, 2));

  // Step 4: User warnings
  console.error("----------------------------------------");
  console.error(`  Logged to: ${LOG_FILE}`);
  console.error("");

  if (tubeOff.includes("FAILED") || tubeOff.includes("HTTP")) {
    console.error("  !!! TUBE SHUTDOWN MAY HAVE FAILED !!!");
    console.error("  !!! PHYSICALLY VERIFY TUBE IS OFF  !!!");
    console.error("");
  }

  console.error("  REQUIRED MANUAL CHECKS:");
  console.error("    1. Verify X-ray tube is OFF on WinWerth PC");
  console.error(`    2. Check ${CT_PC_URL}/status for tube_on state`);
  console.error("    3. Verify door interlock is engaged");
  console.error("    4. Do NOT restart scan until root cause is identified");
  console.error("========================================");
  console.error("");
}

emergencyStop().catch((e) => {
  console.error(`Emergency stop script failed: ${e}`);
  console.error("MANUALLY POWER OFF X-RAY TUBE IMMEDIATELY!");
  process.exit(1);
});
