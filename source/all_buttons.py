# all_buttons.py

import logging
import os
import json
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu


    #1,172
    #38,335


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

    def list_elements_in_rectangle(self, dlg):
        """
        Gibt alle UI-Elemente im definierten Rechteck aus (egal welcher Typ),
        und speichert sie als JSON.
        """

        if dlg is None:
            print("Fehler: Dialog (dlg) ist None.")
            return

        # 🔲 Dein Rechteck
        x1, y1 = 3058, 92
        x2, y2 = 3095, 127

        # 🔥 ALLE Elemente holen (wichtig!)
        elements = dlg.descendants()

        if not elements:
            print("Keine Elemente gefunden.")
            return

        print(f"Gefundene Elemente (gesamt): {len(elements)}\n")

        filtered = []

        for idx, el in enumerate(elements):
            try:
                rect = el.rectangle()
            except Exception:
                continue

            # Mittelpunkt
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2

            # 🔍 Filter nach deinem Bereich
            if rect.right > x1 and rect.left < x2 and rect.bottom > y1 and rect.top < y2:

                info = el.element_info

                name = getattr(info, "name", "None")
                auto_id = getattr(info, "automation_id", "None")
                class_name = getattr(info, "class_name", "None")
                control_type = getattr(info, "control_type", "None")

                print(f"[{idx}] TREFFER")
                print(f"    Name: '{name}'")
                print(f"    AutomationID: '{auto_id}'")
                print(f"    ClassName: '{class_name}'")
                print(f"    ControlType: '{control_type}'")
                print(f"    Center: ({cx}, {cy})\n")

                filtered.append({
                    "index": idx,
                    "name": name,
                    "automation_id": auto_id,
                    "class_name": class_name,
                    "control_type": control_type,
                    "center_x": cx,
                    "center_y": cy
                })

        if not filtered:
            print("❌ Keine Elemente im Rechteck gefunden.")
            return

        # speichern
        filename = self._get_unique_filename("elements_in_rect.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(filtered, f, ensure_ascii=False, indent=4)

        print(f"\n✅ Elemente wurden gespeichert in: {filename}")


if __name__ == "__main__":
    allb = AllButtons()
    wp = winWerth_Process()
    wp.init()
    ab = AllButtons()
    ab.list_elements_in_rectangle(wp.dlg)
   

    # Buttons extrahieren
    # allb.list_all_buttons(wp.dlg)
