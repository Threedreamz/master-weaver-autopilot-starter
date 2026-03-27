# all_buttons.py

import logging
import os
import json
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu


    #1,172
    #35,335


class AllButtons:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)

    def _get_unique_filename(self, base_name="json_TEST.json", folder="exports"):
        """
        Gibt einen einzigartigen Dateinamen im angegebenen Ordner zurück.
        """
        os.makedirs(folder, exist_ok=True)
        base_path = os.path.join(folder, base_name)

        if not os.path.exists(base_path):
            return base_path

        name, ext = os.path.splitext(base_name)
        counter = 1
        while True:
            new_name = os.path.join(folder, f"{name}_{counter}{ext}")
            if not os.path.exists(new_name):
                return new_name
            counter += 1

    def list_all_buttons(self, dlg):
        """
        Gibt alle Buttons im Dialog aus mit Index, AutomationId, Text, ClassName und FoundIndex,
        und speichert sie als JSON.
        """
        if dlg is None:
            print("Fehler: Dialog (dlg) ist None.")
            return

        buttons = dlg.descendants(control_type="Button")

        if not buttons:
            print("Keine Buttons im Dialog gefunden.")
            return

        print(f"Gefundene Buttons: {len(buttons)}\n")

        button_list = []
        for idx, btn in enumerate(buttons):
            auto_id = getattr(btn.element_info, "automation_id", "None")
            name = getattr(btn.element_info, "name", "None")
            class_name = getattr(btn.element_info, "class_name", "None")

            print(f"[{idx}] AutomationID: '{auto_id}' | Text: '{name}' | ClassName: '{class_name}' | FoundIndex: {idx}")
            button_list.append({
                "index": idx,
                "automation_id": auto_id,
                "text": name,
                "class_name": class_name,
                "found_index": idx
            })

        # Datei speichern
        filename = self._get_unique_filename("json_TEST.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(button_list, f, ensure_ascii=False, indent=4)

        print(f"\nButtons wurden in '{filename}' gespeichert.")


if __name__ == "__main__":
    allb = AllButtons()
    wp = winWerth_Process()
    wp.init()
    ab = AllButtons()
    ab.list_all_buttons(wp.dlg)
   

    # Buttons extrahieren
    # allb.list_all_buttons(wp.dlg)
