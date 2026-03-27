from pywinauto import Desktop

def list_save_dialog_controls():
    """
    Findet den aktuell geöffneten Datei-/Speichern-Dialog
    und listet alle enthaltenen Elemente (rekursiv) auf.
    Gibt Index, Text (Name) und AutomationId aus.
    """
    try:
        # Neuestes Top-Level-Fenster vom Typ "Window" finden
        all_windows = Desktop(backend="uia").windows(control_type="Window")
        if not all_windows:
            print("[x] Kein Fenster gefunden.")
            return False

        # Das letzte (neueste) Fenster ist meist der 'Speichern unter'-Dialog
        dlg_save = all_windows[-1]

        elements = dlg_save.descendants()
        print(f"[i] Elemente im Speichern-Dialog: {len(elements)}")

        for i, elem in enumerate(elements):
            try:
                ctrl_type = elem.friendly_class_name()
                name = elem.window_text()
                auto_id = getattr(elem, "automation_id", lambda: None)()
                print(f"[{i}] Type='{ctrl_type}' | Text='{name}' | AutomationId='{auto_id}'")
            except Exception as inner_e:
                print(f"[{i}] [!] Fehler beim Lesen eines Elements: {inner_e}")
        return True

    except Exception as e:
        print(f"[x] Fehler beim Auflisten der Save-Dialog-Controls: {e}")
        return False
