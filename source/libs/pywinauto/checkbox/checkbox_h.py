from pywinauto.findwindows import ElementNotFoundError
from libs.pywinauto.checkbox.checkbox_e import checkbox_e


class checkbox_h:
    ck_e = checkbox_e()
    checkbox_LiveBild = ck_e.checkbox_SchnellesLiveBild["id"]

    def checkState(self, dlg, automation_id):
        """Gibt den CheckState (True/False) einer Checkbox anhand ihrer Automation-ID zurück."""
        try:
            checkbox = dlg.child_window(auto_id=automation_id, control_type="CheckBox")
            # Direkt .get_toggle_state() ohne wrapper_object(), da dlg.child_window schon Wrapper liefert
            state = checkbox.get_toggle_state()
            return state == 1  # 1 = checked, 0 = unchecked, 2 = indeterminate
        except ElementNotFoundError:
            print(f"[!] Checkbox mit Automation-ID '{automation_id}' wurde nicht gefunden.")
            return None
        except Exception as e:
            print(f"[!] Fehler beim Lesen des CheckState ({automation_id}): {e}")
            return None

    def isLiveBildChecked(self, dlg):
        """Prüft, ob das 'Schnelles Livebild'-Checkboxfeld aktiviert ist."""
        return self.checkState(dlg, self.checkbox_LiveBild)

    def setLiveBildChecked(self, dlg):
        """Aktiviert die 'Schnelles Livebild'-Checkbox, wenn sie noch nicht aktiviert ist."""
        current = self.isLiveBildChecked(dlg)
        if current is None:
            print("[!] LiveBild-Checkbox nicht gefunden.")
            return
        if not current:
            self.setCheckState(dlg, self.checkbox_LiveBild, True)
        else:
            print("[-] LiveBild ist bereits aktiviert.")

    def setCheckState(self, dlg, automation_id, checkState):
        """Setzt den CheckState einer Checkbox (True = checked, False = unchecked)."""
        try:
            checkbox = dlg.child_window(auto_id=automation_id, control_type="CheckBox")
            current_state = checkbox.get_toggle_state() == 1

            if checkState != current_state:
                checkbox.toggle()  # toggelt zwischen checked/unchecked
                print(f"[+] Checkbox '{automation_id}' wurde auf {checkState} gesetzt.")
            else:
                print(f"[-] Checkbox '{automation_id}' war bereits {checkState}. Keine Änderung nötig.")
        except ElementNotFoundError:
            print(f"[!] Checkbox mit Automation-ID '{automation_id}' wurde nicht gefunden.")
        except Exception as e:
            print(f"[!] Fehler beim Setzen des CheckState ({automation_id}): {e}")
