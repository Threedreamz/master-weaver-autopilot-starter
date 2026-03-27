# ui_helpers.py
from pywinauto import timings
from pywinauto.controls.uiawrapper import UIAWrapper


class button_h:
    def getAllButtons(self, dlg_desc):
        """
        Gibt eine Liste mit allen Buttons im Dialog zurück.
        Jeder Eintrag enthält Text (Name) und automation_id.
        """
        buttons_list = []
        try:
            buttons = dlg_desc
            for i, btn in enumerate(buttons):
                btn_text = getattr(btn.element_info, "name", "")
                btn_auto_id = getattr(btn.element_info, "automation_id", "")
                if not (btn_text == '' and btn_auto_id == ''):  
                    buttons_list.append({
                        "text": btn_text,
                        "automation_id": btn_auto_id
                    })
        except Exception as e:
            print("ERROR")
        return buttons_list