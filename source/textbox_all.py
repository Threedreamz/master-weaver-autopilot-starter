from pywinauto import Application
from libs.pywinauto.process import winWerth_Process
def list_textboxes(dlg):
    """
    Verbindet sich mit einem Fenster anhand seines Titels und listet alle Textboxen auf.
    Gibt für jede Textbox Automation-ID, Name und Textwert aus.
    """


    print(f"[+] Verbunden mit Fenster: {dlg.element_info.name}")
    print("[+] Scanne nach Textboxen...\n")

    # Alle Edit Controls durchsuchen
    for edit in dlg.descendants(control_type="Edit"):
        try:
            auto_id = getattr(edit.element_info, "automation_id", "")
            name = getattr(edit.element_info, "name", "")
            value = ""
            try:
                value = edit.get_value()
            except Exception:
                # Manche Edit-Felder erlauben keinen direkten get_value
                try:
                    value = edit.window_text()
                except Exception:
                    value = "<kein Text auslesbar>"

            print(f"[Textbox] Name: {name}, ID: {auto_id}, Text: '{value}'")

        except Exception as e:
            print(f"[!] Fehler bei Element: {e}")

if __name__ == "__main__":
    ww = winWerth_Process()
    ww.init()
    # Beispiel: Fenster anhand Titel (oder Teilstring) verbinden
    list_textboxes(ww.dlg)   # oder z. B. "Notepad", "Calculator", etc.
