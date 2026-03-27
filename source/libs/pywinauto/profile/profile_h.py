from pywinauto import Desktop
import time

from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu

class profile_h:
    pk:punkte_Menu
    def __init__(self):
        self.pk = punkte_Menu()



    def clickButtonById(self, dlg, text):
        """
        Sucht alle Buttons im dlg und klickt den Button, dessen Name == automation_id.
        - dlg: CT-Sensor WindowWrapper
        - text: string, exakter Vergleich
        Rückgabe: True wenn geklickt, False wenn nicht gefunden
        """
        if dlg is None:
            print("Fehler: dlg ist None")
            return False

        buttons = dlg.descendants(control_type="Button")
        if not buttons:
            print("Keine Buttons im Fenster gefunden.")
            return False
        
        for btn in buttons:
            try:
                btn_name = getattr(btn.element_info, "automation_id", "")
                if btn_name == text:
                    btn.click_input()  # click_input() = realer Klick
                    return True
            except Exception:
                continue

        return False
    def clickButtonByText(self, dlg, text):
        """
        Sucht alle Buttons im dlg und klickt den Button, dessen Name == text.
        - dlg: CT-Sensor WindowWrapper
        - text: string, exakter Vergleich
        Rückgabe: True wenn geklickt, False wenn nicht gefunden
        """
        if dlg is None:
            print("Fehler: dlg ist None")
            return False

        buttons = dlg.descendants(control_type="Button")
        if not buttons:
            print("Keine Buttons im Fenster gefunden.")
            return False

        for btn in buttons:
            try:
                btn_name = getattr(btn.element_info, "name", "")
                if btn_name == text:
                    btn.click_input()  # click_input() = realer Klick
                    return True
            except Exception:
                continue

        return False
    
    def selectListBoxItemByText(self, dlg, text):
        """
        Sucht alle ListBoxItems im dlg und wählt das Item aus, dessen Name == text.
        - dlg: CT-Sensor WindowWrapper
        - text: string, exakter Vergleich
        Rückgabe: True wenn ausgewählt, False wenn nicht gefunden
        """
        if dlg is None:
            print("Fehler: dlg ist None")
            return False

        items = dlg.descendants(control_type="ListItem")
        if not items:
            # falls keine direkten ListItems, gehe über List Controls
            lists = dlg.descendants(control_type="List")
            for lst in lists:
                for item in lst.children():
                    try:
                        item_name = getattr(item.element_info, "name", "")
                        if item_name == text:
                            item.select()
                            return True
                    except Exception:
                        continue
            return False

        # direkte ListItems prüfen
        for item in items:
            try:
                item_name = getattr(item.element_info, "name", "")
                if item_name == text:
                    item.select()
                    return True
            except Exception:
                continue

        return False
    def openProfileWindow(self, dlg):
        """
        Wechselt zum CT-Tab im Hauptdialog und öffnet ggf. den Profilbereich.
        """
        currentTab = self.pk.detectMenu(dlg)
        print("was men detected")
        print(f"Current tab: {currentTab}")
        if currentTab != "CT":
            self.pk.selectMenuByIndex(self.pk.btnIndexByTab("CT", currentTab), dlg)
            currentTab = self.pk.detectMenu(dlg)
        self.pk.selectMenuByIndex(self.pk.btnIndexByTab("CT", currentTab), dlg)

    def isWindowOpen(self, dlg, wait=False, timeout=10):
        """
        Prüft, ob das CT-Sensor Fenster offen ist.
        - wait=True: wartet bis Fenster erscheint oder timeout erreicht
        - Rückgabe: UIAWrapper wenn offen, sonst None
        """
        t0 = time.time()
        while True:
            ct_win = self.find_ct_sensor(dlg)
            if ct_win:
                if ct_win.is_visible() and ct_win.is_enabled():
                    return ct_win
            if not wait or (time.time() - t0) > timeout:
                return None
            time.sleep(0.3)

    def showButtons(self, dlg_or_window):
        """
        Liefert eine Liste aller Buttons im CT-Sensor Fenster.
        Rückgabe: list von dicts mit index, automation_id, name, class_name, control_type, rect
        """
        ct_win = dlg_or_window if getattr(dlg_or_window, "element_info", None) else None
        if not ct_win:
            ct_win = self.find_ct_sensor(dlg_or_window)
            if not ct_win:
                print("CT-Sensor Fenster nicht gefunden.")
                return []

        buttons = ct_win.descendants(control_type="Button")
        out = []
        for idx, b in enumerate(buttons):
            ei = b.element_info
            try:
                rect = getattr(ei, "rectangle", (0,0,0,0))
                rect_tuple = (rect.left, rect.top, rect.right, rect.bottom) if hasattr(rect, "left") else tuple(rect)
            except Exception:
                rect_tuple = (0,0,0,0)

            out.append({
                "index": idx,
                "automation_id": getattr(ei, "automation_id", None),
                "name": getattr(ei, "name", None),
                "class_name": getattr(ei, "class_name", None),
                "control_type": getattr(ei, "control_type", None),
                "rect": rect_tuple
            })

        return out

    def showListBoxItems(self, dlg_or_window):
        """
        Liefert alle ListBox-Items im CT-Sensor Fenster.
        Rückgabe: list von dicts mit index, automation_id, name, class_name, control_type
        """
        ct_win = dlg_or_window if getattr(dlg_or_window, "element_info", None) else None
        if not ct_win:
            ct_win = self.find_ct_sensor(dlg_or_window)
            if not ct_win:
                print("CT-Sensor Fenster nicht gefunden.")
                return []

        items = ct_win.descendants(control_type="ListItem")
        result = []
        if not items:
            # Falls keine ListItems, suche List-Controls und deren Children
            lists = ct_win.descendants(control_type="List")
            for lst in lists:
                try:
                    for it in lst.children():
                        ei = it.element_info
                        result.append({
                            "index": len(result),
                            "automation_id": getattr(ei, "automation_id", None),
                            "name": getattr(ei, "name", None),
                            "class_name": getattr(ei, "class_name", None),
                            "control_type": getattr(ei, "control_type", None)
                        })
                except Exception:
                    pass
        else:
            for idx, it in enumerate(items):
                ei = it.element_info
                result.append({
                    "index": idx,
                    "automation_id": getattr(ei, "automation_id", None),
                    "name": getattr(ei, "name", None),
                    "class_name": getattr(ei, "class_name", None),
                    "control_type": getattr(ei, "control_type", None)
                })

        return result

    def find_ct_sensor(self, dlg_or_app):
        """
        Sucht das CT-Sensor Fenster.
        - dlg_or_app: Hauptdialog oder Application-Objekt
        Gibt UIAWrapper zurück oder None, falls nicht gefunden.
        """
        # 1️⃣ Erst innerhalb des Dialogs (Child-Fenster)
        try:
            for w in dlg_or_app.descendants(control_type="Window"):
                name = getattr(w.element_info, "name", "")
                if "CT-Sensor" in name:
                    return w
        except Exception:
            pass

        # 2️⃣ Falls nicht gefunden, als Top-Level-Fenster über Desktop suchen
        try:
            for win in Desktop(backend="uia").windows():
                name = getattr(win.element_info, "name", "")
                if "CT-Sensor" in name:
                    return win
        except Exception:
            pass

        return None


    def getCTSensorDlg(self, dlg_or_main, wait=False, timeout=10):
        """
        Liefert das UIAWrapper-Objekt (dlg) des CT-Sensor Fensters, wenn gefunden.
        - dlg_or_main: Hauptfenster oder Application-Objekt
        - wait=True: wartet bis timeout, bis Fenster erscheint
        - Rückgabe: UIAWrapper oder None
        """
        t0 = time.time()
        while True:
            ct_win = self.find_ct_sensor(dlg_or_main)
            if ct_win and ct_win.is_visible() and ct_win.is_enabled():
                print("[+] CT-Sensor Fenster gefunden:", getattr(ct_win.element_info, "name", ""))
                try:
                    ct_win.set_focus()
                except Exception:
                    pass
                return ct_win

            if not wait or (time.time() - t0) > timeout:
                print("[!] Kein CT-Sensor Fenster gefunden.")
                return None

            time.sleep(0.3)
