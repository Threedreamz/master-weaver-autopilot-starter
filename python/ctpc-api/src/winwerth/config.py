"""
JSON configuration loader for WinWerth element coordinates and colors.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ctpc-api.config")

# Default config location — relative to the ctpc-api package root
_DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "winWerth_data.json")


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load WinWerth configuration from a JSON file.

    Args:
        config_file: Path to JSON config. Defaults to winWerth_data.json in package root.

    Returns:
        Parsed configuration dict.  Returns empty dict on failure.
    """
    path = config_file or _DEFAULT_CONFIG
    path = os.path.abspath(path)

    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {path}")
        return config
    except FileNotFoundError:
        logger.warning(f"Config file not found: {path}")
        return {}
    except json.JSONDecodeError as exc:
        logger.error(f"Error parsing JSON config: {exc}")
        return {}


def get_coords(element: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    """
    Extract (x, y) coordinates from an element dict.

    Supports both ``{"x": .., "y": ..}`` and ``{"pos": {"x": .., "y": ..}}``.
    """
    if not isinstance(element, dict):
        return None
    if "x" in element and "y" in element:
        return (int(element["x"]), int(element["y"]))
    pos = element.get("pos")
    if isinstance(pos, dict) and "x" in pos and "y" in pos:
        return (int(pos["x"]), int(pos["y"]))
    return None


def get_color(element: Dict[str, Any]) -> Optional[Tuple[int, int, int]]:
    """Extract RGB color tuple from element dict."""
    if isinstance(element, dict) and "color" in element:
        c = element["color"]
        return tuple(c) if isinstance(c, list) else c
    return None


def get_from_possible_keys(container: Dict[str, Any], candidates: List[str]) -> Any:
    """
    Return value for the first matching key among *candidates*.

    Useful for handling UTF-8 vs mis-encoded keys (e.g. 'Rohre_An' vs 'RÃ¶hre_An').
    """
    for key in candidates:
        if key in container:
            return container[key]
    raise KeyError(f"None of the keys found: {candidates}")
