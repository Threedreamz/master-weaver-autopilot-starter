# WinWerth UI Automation Rules

## Identification Methods (by reliability)
1. **`automation_id`** — Best. Stable across sessions and language packs. Prefer this always.
2. **`control_type` + `index`** — Good fallback. Index may shift if UI layout changes.
3. **`name` / `text`** — Least reliable. Language-dependent (German UI) and changes with state.

Always use the highest-reliability method available for each control.

## Module Pattern
Each UI control follows a 3-file pattern:
- **`.py`** — Public interface (functions called by the state machine)
- **`_h.py`** — Handler with pywinauto calls (actual UI interaction)
- **`_e.py`** — Enums defining automation_ids, control indices, and string constants

Never put pywinauto calls in the interface file. Never put business logic in the handler file.

## Process Connection
- Always connect through `winWerth_Process.init("uia")` — uses the UIA backend
- WinWerth executable path: `C:\Program Files (x86)\WinWerth\WinWerth 2023\WinWerth.exe`
- Connection must be established before any UI operations
- If the process is not running, report an error — never attempt to launch WinWerth automatically

## Discovery
- Use `z_extract/` tools to discover automation_ids for new or unknown controls
- Discovery tools must be run on the actual WinWerth PC with the application open
- Document newly discovered IDs in the corresponding `_e.py` enum file immediately
- Never guess automation_ids — always verify through discovery

## German UI Labels
All WinWerth labels are in German. Use exact strings:
- "Rohre an" — Tube on
- "Rohre aus" — Tube off
- "Speichern unter" — Save as
- "Messen" — Measure
- "Volle Umdrehung" — Full rotation
- "Bilddynamik" — Image dynamics
- "Fehlerkorrektur" — Error correction
- "Profil laden" — Load profile

String matching must be exact — no partial matches, no case normalization.

## Dialog Handling
- **Profile window**: Requires `getCTSensorDlg()` to obtain the dialog handle before interaction
- **Save dialog**: Detected by window title "Speichern unter" — wait for it to appear before typing path
- **Loading windows**: Block execution until dismissed — poll with timeout, do not ignore
- **Modal dialogs**: Must be closed before any other UI interaction can proceed

## Error States
- Red labels in the WinWerth UI indicate error conditions
- The `error_correction` module adjusts voltage and ampere to resolve errors
- Maximum 8 correction iterations with alternating +/- adjustments
- If corrections exhaust all iterations, transition to ERROR state and notify the user
- Log every correction attempt with before/after values for diagnostics
