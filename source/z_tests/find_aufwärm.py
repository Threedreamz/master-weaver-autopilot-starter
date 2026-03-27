from pywinauto import Application
from libs.pywinauto.process import winWerth_Process

def find_label(dlg, search_terms=None):
    """
    Durchsucht ein Fenster nach Labels oder Text-ähnlichen UI-Elementen,
    deren sichtbarer Text bestimmte Begriffe enthält (z. B. "Aufwärmzeit", "3 min").
    Gibt Treffer mit Name, Automation-ID und Control-Type aus.
    """
    if search_terms is None:
        search_terms = ["Aufwärmzeit", "3 min"]

    print(f"[+] Verbunden mit Fenster: {dlg.element_info.name}")
    print(f"[+] Suche nach Begriffen: {search_terms}\n")

    for elem in dlg.descendants():
        try:
            name = getattr(elem.element_info, "name", "")
            ctrl_type = getattr(elem.element_info, "control_type", "")
            auto_id = getattr(elem.element_info, "automation_id", "")

            if any(term.lower() in name.lower() for term in search_terms):
                try:
                    color = getattr(elem.element_info, "FillColor", "")
                    print("UIA FillColor:", color)
                except Exception:
                    pass
                print(f"[Treffer] {ctrl_type} | Name: '{name}' | ID: {auto_id}")
        except Exception:
            continue


if __name__ == "__main__":
    ww = winWerth_Process()
    ww.init()  # stellt Verbindung her
    if ww.dlg:
        find_label(ww.dlg, ["Aufwärmzeit", "4 min", "3 min"])
    else:
        print("[-] Kein gültiges Dialogfenster gefunden.")
