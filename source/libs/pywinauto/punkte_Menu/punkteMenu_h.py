from libs.pywinauto.button.button_h import button_h

class punkteMenu_h:
    btn_h = button_h()

    def isButtonAvailableId(self, id_ : str, dlg_desc) -> bool:
        try:
            buttons = self.btn_h.getAllButtons(dlg_desc)
            for i, btn in enumerate(buttons):
                if btn.get("automation_id") == id_:
                    return True
        except Exception as e:
            print("Fehler bei isButtonAvailableId: %s", e)
        return False

    def isButtonAvailableText(self, text: str, dlg_desc) -> bool:
        try:
            buttons = self.btn_h.getAllButtons(dlg_desc)
            for i, btn in enumerate(buttons):
                if btn.get("text") == text:
                    return True
        except Exception as e:
            print("Fehler bei isButtonAvailableText: %s", e)
        return False

    def getCurrentButtons(self, dlg):
        # returns all buttons as list
        desc = dlg.descendants(control_type="Button")
        return self.btn_h.getAllButtons(desc)
