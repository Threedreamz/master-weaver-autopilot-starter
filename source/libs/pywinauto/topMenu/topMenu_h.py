from typing import Optional
from pywinauto.controls.uia_controls import MenuWrapper, MenuItemWrapper
class topMenu_h:
    def press_menu_item(self, dlg, text: str | None = None, automation_id: str | None = None) -> bool:
        """
        Klickt ein Menü-Item im übergebenen Dialog `dlg` anhand von Text ODER AutomationId.
        Gibt True zurück, wenn erfolgreich.
        """
        try:
            # Menü im Dialog suchen
            menus = dlg.descendants(control_type="Menu")
            if not menus:
                print("[x] Kein Menü im Dialog gefunden.")
                return False

            menu = menus[0]  # falls mehrere vorhanden sind, ggf. anpassen

            # Alle MenuItems abrufen
            items = menu.descendants(control_type="MenuItem")

            for item in items:
                name = item.window_text()
                auto_id = item.automation_id()

                if (text and name.strip() == text.strip()) or (automation_id and auto_id == automation_id):
                    item.click_input()
                    print(f"[OK] Menüpunkt '{name}' (ID='{auto_id}') angeklickt.")
                    return True

            print(f"[x] Kein Menüeintrag gefunden für text='{text}' oder id='{automation_id}'.")
            return False

        except Exception as e:
            print(f"[x] Fehler beim Klicken auf Menüeintrag: {e}")
            return False

    # Optionaler Convenience-Wrapper:
    def press_menu_by_text(self, dlg, text: str) -> bool:
        return self.press_menu_item(dlg, text=text)

    def press_menu_by_id(self, dlg, automation_id: str) -> bool:
        return self.press_menu_item(dlg, automation_id=automation_id)
    
    def press(self, dlg, automation_id: Optional[str] = None,text: Optional[str] = None, index: Optional[int] = None) -> bool:
        if text is not None:
            return self.press_menu_by_text(dlg, text)
        if automation_id is not None:
            return self.press_menu_by_id(dlg, automation_id)

      

        return False 
    def raw_click(self,dlg, text: str):
        """
        Klickt auf ein MenuItem innerhalb eines Menüs, das den gegebenen Text enthält.
        
        Parameter:
            dlg  : das pywinauto Dialogobjekt (z. B. Application().connect(...).window(...))
            text : der sichtbare Text des Menüelements, z. B. "Datei"
        """
        try:
            # alle Menu-Elemente rekursiv durchsuchen
            all_items = dlg.descendants(control_type="MenuItem")
        except Exception as e:
            print(f"[x] Fehler beim Auflisten der MenuItems: {e}")
            return False

        target = None
        for item in all_items:
            try:
                if isinstance(item, MenuItemWrapper):
                    if item.window_text().strip().lower() == text.strip().lower():
                        target = item
                        break
            except Exception:
                continue

        if not target:
            print(f"[x] Kein Menüeintrag mit Text '{text}' gefunden.")
            return False

        try:
            target.click_input()  # oder target.click_input(), falls select() nicht funktioniert
            print(f"[✓] Menüeintrag '{text}' wurde geklickt.")
            return True
        except Exception as e:
            print(f"[x] Fehler beim Klicken von '{text}': {e}")
            return False