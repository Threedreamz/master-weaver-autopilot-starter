#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.controls.uiawrapper import UIAWrapper
import sys

def attach_window(title=None, title_re=None, pid=None, backend="uia"):
    app = Application(backend=backend)
    try:
        if pid is not None:
            app.connect(process=pid, timeout=10)
        elif title_re is not None:
            app.connect(title_re=title_re, timeout=10)
        elif title is not None:
            app.connect(title=title, timeout=10)
        else:
            raise ValueError("Provide title, title_re, or pid.")
    except (ElementNotFoundError, RuntimeError, ValueError) as e:
        print(f"[Error] Could not connect to window: {e}")
        sys.exit(1)

    try:
        if title is not None:
            dlg = app.window(title=title)
        elif title_re is not None:
            dlg = app.window(title_re=title_re)
        else:
            dlg = app.window(process=pid)
        dlg.wait("exists ready", timeout=10)
        return dlg
    except Exception as e:
        print(f"[Error] Could not fetch top-level window: {e}")
        sys.exit(1)

def safe_text(elem: UIAWrapper) -> str:
    try:
        return getattr(elem.element_info, "name", "") or ""
    except Exception:
        return ""

def safe_autoid(elem: UIAWrapper) -> str:
    try:
        a = getattr(elem.element_info, "automation_id", None)
        return a if a not in (None, "") else "None"
    except Exception:
        return "None"

def rect_top(elem: UIAWrapper) -> int:
    try:
        return elem.rectangle().top
    except Exception:
        return 10**9

def list_head_items(dlg: UIAWrapper, head_band_px: int = 120):
    """
    Scan the top band of the window for typical head controls (MenuBar, ToolBar/Ribbon,
    MenuItems, Buttons) and print Text (Name) + AutomationId.
    """
    dlg_rect = dlg.rectangle()
    head_limit = dlg_rect.top + head_band_px

    # Containers that usually live in the head area
    containers = dlg.descendants(control_type="MenuBar")
    containers += dlg.descendants(control_type="ToolBar")
    containers += dlg.descendants(control_type="Menu")

    # Direct candidates near the top
    direct_candidates = [
        e for e in dlg.descendants(depth=3)
        if getattr(e.element_info, "control_type", "") in ("MenuItem", "Button", "SplitButton", "TabItem")
        and rect_top(e) <= head_limit
    ]

    # Children inside containers
    inner_candidates = []
    for c in containers:
        try:
            inner_candidates += c.descendants()
        except Exception:
            continue

    # Merge + de-dupe
    all_candidates = containers + inner_candidates + direct_candidates
    filtered = []
    seen = set()
    for e in all_candidates:
        try:
            if rect_top(e) <= head_limit:
                handle = getattr(e.element_info, "handle", None)
                aid = safe_autoid(e)
                name = safe_text(e)
                ctype = getattr(e.element_info, "control_type", "")
                key = (handle, aid, name, ctype)
                if key not in seen:
                    seen.add(key)
                    filtered.append(e)
        except Exception:
            continue

    # Sort for a stable, readable listing
    filtered.sort(key=lambda x: (getattr(x.element_info, "control_type", ""),
                                 rect_top(x),
                                 safe_text(x).lower()))

    print(f"Head controls found (~{head_band_px}px from top): {len(filtered)}\n")
    for idx, e in enumerate(filtered, 1):
        ctype = getattr(e.element_info, "control_type", "Unknown")
        name = safe_text(e) or "(no text)"
        aid = safe_autoid(e)
        try:
            rect = e.rectangle()
            pos = f"{rect.left},{rect.top} {rect.width()}x{rect.height()}"
        except Exception:
            pos = "?,? ?x?"
        print(f"[{idx:02d}] Type={ctype:11s}  Text={name!r}  AutomationId={aid!r}  Pos={pos}")

def main():
    # Attach via regex to your WinWerth window title
    dlg = attach_window(title_re=r"WinWerth - \[\]", backend="uia")

    try:
        dlg.set_focus()
    except Exception:
        pass

    # Print the head items
    list_head_items(dlg, head_band_px=140)

if __name__ == "__main__":
    main()
