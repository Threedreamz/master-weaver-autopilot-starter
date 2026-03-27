#!/usr/bin/env npx tsx
/**
 * AutoPilot Config Validator — validates hardware config on session start.
 * Catches corrupted winWerth_data.json BEFORE it causes mid-scan KeyErrors.
 *
 * Checks:
 *   1. winWerth_data.json exists and is valid JSON
 *   2. Required keys present (WinWerth_Window, Profile_Window, STL_Speichern_Unter)
 *   3. Pixel coordinates within 4K range (0-3840 x 0-2160)
 *   4. Port config matches ecosystem range (4800-4829)
 *   5. .env has required variables
 */

import * as fs from "fs";
import * as path from "path";

const ROOT = process.cwd();
const issues: string[] = [];
const warnings: string[] = [];

// ---------------------------------------------------------------------------
// 1. Validate winWerth_data.json
// ---------------------------------------------------------------------------
const configPaths = [
  path.join(ROOT, "source", "winWerth_data.json"),
  path.join(ROOT, "python", "ctpc-api", "winWerth_data.json"),
];

const MAX_X = 3840;
const MAX_Y = 2160;

function checkCoords(obj: any, prefix: string): void {
  if (typeof obj !== "object" || obj === null) return;
  for (const [k, v] of Object.entries(obj)) {
    if (typeof v !== "object" || v === null) continue;
    const val = v as Record<string, unknown>;
    if ("x" in val && "y" in val) {
      const { x, y } = val;
      if (typeof x === "number" && (x < 0 || x > MAX_X))
        issues.push(`${prefix}.${k}: x=${x} out of range (0-${MAX_X})`);
      if (typeof y === "number" && (y < 0 || y > MAX_Y))
        issues.push(`${prefix}.${k}: y=${y} out of range (0-${MAX_Y})`);
    } else {
      checkCoords(v, `${prefix}.${k}`);
    }
  }
}

let configFound = false;
for (const p of configPaths) {
  if (!fs.existsSync(p)) continue;
  configFound = true;

  try {
    const data = JSON.parse(fs.readFileSync(p, "utf-8"));
    const requiredKeys = [
      "WinWerth_Window",
      "Profile_Window",
      "STL_Speichern_Unter",
    ];
    for (const key of requiredKeys) {
      if (!(key in data)) {
        issues.push(`${path.basename(p)}: missing required key "${key}"`);
      }
    }
    checkCoords(data, path.basename(p));
  } catch (e) {
    issues.push(`${path.basename(p)}: INVALID JSON — ${e}`);
  }
}

if (!configFound) {
  warnings.push(
    "winWerth_data.json not found in source/ or python/ctpc-api/ — " +
      "run /autopilot-extract on the CT-PC to generate it"
  );
}

// ---------------------------------------------------------------------------
// 2. Validate .env
// ---------------------------------------------------------------------------
const envCandidates = [
  path.join(ROOT, ".env"),
  path.join(ROOT, "python", "ctpc-api", ".env"),
];

let envFound = false;
for (const envPath of envCandidates) {
  if (!fs.existsSync(envPath)) continue;
  envFound = true;

  const envContent = fs.readFileSync(envPath, "utf-8");
  const requiredVars = ["HOST", "PORT"];
  for (const v of requiredVars) {
    // Match KEY= at start of line (allows KEY= with empty value as present)
    if (!new RegExp(`^${v}=`, "m").test(envContent)) {
      issues.push(`.env: missing required variable ${v}`);
    }
  }

  // Validate PORT is in autopilot range 4800-4829
  const portMatch = envContent.match(/^PORT=(\d+)/m);
  if (portMatch) {
    const port = parseInt(portMatch[1], 10);
    if (port < 4800 || port > 4829) {
      warnings.push(
        `.env: PORT=${port} outside AutoPilot range (4800-4829). ` +
          "Check port-registry.md for assigned ports."
      );
    }
  }
}

if (!envFound) {
  const examplePaths = envCandidates.map((p) => p + ".example");
  const hasExample = examplePaths.some((p) => fs.existsSync(p));
  if (hasExample) {
    warnings.push(".env missing — copy .env.example and configure for your CT-PC");
  } else {
    warnings.push(".env missing and no .env.example found");
  }
}

// ---------------------------------------------------------------------------
// 3. Check Python dependencies (informational)
// ---------------------------------------------------------------------------
const requirementsPath = path.join(ROOT, "python", "ctpc-api", "requirements.txt");
if (fs.existsSync(requirementsPath)) {
  const reqs = fs.readFileSync(requirementsPath, "utf-8");
  const criticalDeps = ["fastapi", "uvicorn", "pyautogui", "pywinauto"];
  for (const dep of criticalDeps) {
    if (!reqs.toLowerCase().includes(dep)) {
      warnings.push(`requirements.txt: missing critical dependency "${dep}"`);
    }
  }
}

// ---------------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------------
if (issues.length > 0) {
  console.error("");
  console.error(`  AutoPilot Config ISSUES (${issues.length}):`);
  for (const issue of issues) console.error(`    [!] ${issue}`);
}

if (warnings.length > 0) {
  console.error("");
  console.error(`  AutoPilot Config Warnings (${warnings.length}):`);
  for (const w of warnings) console.error(`    [~] ${w}`);
}

if (issues.length === 0 && warnings.length === 0) {
  console.error("  AutoPilot config: OK");
}

if (issues.length > 0 || warnings.length > 0) {
  console.error("");
}

// Always pass — config issues are warnings, not session blockers
console.log(
  JSON.stringify({
    status: issues.length > 0 ? "warn" : "pass",
    issues: issues.length,
    warnings: warnings.length,
  })
);
