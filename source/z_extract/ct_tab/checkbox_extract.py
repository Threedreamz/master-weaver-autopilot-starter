from pywinauto.findwindows import ElementNotFoundError
from pywinauto import Application


def list_all_checkboxes(dlg, print_debug=True, only_with_id=False):
    """
    Durchsucht den Dialog nach allen CheckBox-Elementen und gibt deren
    Automation-ID, Namen/Text und CheckState zurück.
    """
    checkboxes_info = []
    try:
        # Alle CheckBox-Elemente finden (UIA backend)
        checkboxes = dlg.descendants(control_type="CheckBox")

        for cb in checkboxes:
            try:
                element = cb.element_info
                auto_id = element.automation_id or ""
                name = element.name or "<kein Name>"
                # get_toggle_state() gibt 0, 1 oder 2 zurück (Unchecked, Checked, Indeterminate)
                try:
                    state = cb.get_toggle_state() == 1
                except Exception:
                    state = None  # Falls kein State gelesen werden kann

                if only_with_id and not auto_id:
                    continue

                checkboxes_info.append({
                    "automation_id": auto_id,
                    "name": name,
                    "checked": state
                })

            except Exception as e:
                print(f"[!] Fehler beim Lesen einer Checkbox: {e}")

        if print_debug:
            print("\n[+] Gefundene Checkboxen:")
            for info in checkboxes_info:
                print(f"  [Checkbox] Name: {info['name']}, ID: {info['automation_id']}, Checked: {info['checked']}")

    except ElementNotFoundError:
        print("[!] Keine Checkboxen gefunden.")
    except Exception as e:
        print(f"[!] Fehler beim Durchsuchen des Dialogs: {e}")

    return checkboxes_info
winWerth_title = r"WinWerth - \[\]"
app = Application(backend="uia").connect(title_re=winWerth_title)
dlg = app.window(title_re=winWerth_title)
checkboxes = list_all_checkboxes(dlg, only_with_id=True)
