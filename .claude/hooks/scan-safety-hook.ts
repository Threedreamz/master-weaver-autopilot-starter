// Hook: PreBash validation for AutoPilot CT-Scanner
// Prevents accidental triggering of real CT scans and protects running scan processes

const command = process.argv[2] || "";

const result: { status: string; message: string } = { status: "pass", message: "" };

// Rule 1: Warn before triggering a real CT scan via API
// /scan/start initiates an actual CT scan in LIVE mode — this moves physical hardware
if (/\b(curl|httpie|http|wget)\b/.test(command) && /\/scan\/start/.test(command)) {
  result.status = "warn";
  result.message =
    "WARNING: This command will POST to /scan/start which initiates a real CT scan in LIVE mode. " +
    "This moves physical CT hardware and starts an X-ray scan cycle. " +
    "Use MOCK mode (SCAN_MODE=mock) for testing. Continue only if you intend to run a real scan.";
}

// Rule 2: Block killing the CT-PC API process during an active scan
// Killing uvicorn/python while a scan is in progress can leave the CT machine in an undefined state
const killPatterns = /\b(kill|pkill|killall|taskkill)\b.*(uvicorn|python|fastapi|ct[-_]?api|scan[-_]?server)/;
const stopPatterns = /\b(systemctl\s+stop|supervisorctl\s+stop)\b.*(ct[-_]?api|scan[-_]?server|autopilot)/;
if (killPatterns.test(command) || stopPatterns.test(command)) {
  result.status = "block";
  result.message =
    "BLOCKED: Killing the CT-PC API process during an active scan can leave the CT machine in an undefined state. " +
    "Check scan status first with GET /scan/status. If a scan is in progress, wait for completion or use POST /scan/abort for a safe stop.";
}

// Rule 3: Warn before PyInstaller builds — takes 2-5 minutes with large output
if (/\bpyinstaller\b/.test(command)) {
  result.status = "warn";
  result.message =
    "WARNING: PyInstaller builds take 2-5 minutes and produce large output. " +
    "Consider running with --noconfirm to skip prompts. " +
    "The resulting executable will be in the dist/ directory.";
}

console.log(JSON.stringify(result));
