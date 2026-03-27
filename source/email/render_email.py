import json
import re
import html
from pathlib import Path

def render_email(scan_id: str) -> str:
    """
    Loads ./scans/{scan_id}.json and ./config.json,
    merges them, replaces placeholders in the HTML template,
    and returns the rendered HTML as a string.
    """

    base_dir = Path(__file__).parent
    scan_file = base_dir / "scans" / f"{scan_id}.json"
    config_file = base_dir / "config.json"
    template_file = base_dir / "notify.html"

    # --- Error handling ---
    if not scan_file.exists():
        raise FileNotFoundError(f"Scan file not found: {scan_file}")
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")
    if not template_file.exists():
        raise FileNotFoundError(f"Template file not found: {template_file}")

    # --- Load JSONs ---
    with open(scan_file, "r", encoding="utf-8") as f:
        scan_data = json.load(f)
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = json.load(f)

    if not isinstance(scan_data, dict) or not isinstance(config_data, dict):
        raise ValueError("Invalid JSON structure in scan or config file.")

    # --- Merge data (scan overrides config) ---
    data = {**config_data, **scan_data}

    # --- Load template ---
    template = template_file.read_text(encoding="utf-8")

    # --- Replace placeholders {{key}} with escaped value ---
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            continue
        safe_value = html.escape(str(value))
        template = template.replace(f"{{{{{key}}}}}", safe_value)

    # --- Remove unfilled {{...}} placeholders ---
    template = re.sub(r"{{[^}]+}}", "", template)

    return template




