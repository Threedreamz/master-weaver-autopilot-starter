class combobox_h:    



    def list_combobox_items(self, dlg, automation_id: str):
        """
        Listet alle Items einer ComboBox (per AutomationId) auf.

        Parameter:
            dlg: Das Dialogfenster (z. B. von pywinauto Application().window()).
            automation_id: Die AutomationId der ComboBox als String oder Zahl.

        Rückgabe:
            Liste von Dictionaries mit 'automation_id' und 'text'.
            Gibt None zurück, wenn nichts gefunden wurde.
        """
        if dlg is None:
            print("[x] Fehler: dlg ist None, kann keine ComboBox durchsuchen.")
            return None

        try:
            # passende ComboBox über descendants finden
            combos = dlg.descendants(control_type="ComboBox")
            target_combo = None

            for combo in combos:
                auto_id = getattr(combo.element_info, "automation_id", "")
                if str(auto_id) == str(automation_id):
                    target_combo = combo
                    break

            if not target_combo:
                print(f"[x] Keine ComboBox mit AutomationId '{automation_id}' gefunden.")
                return None

            # Dropdown öffnen (manche UIs benötigen das, um Items zu laden)
            try:
                target_combo.expand()
            except Exception:
                pass  # falls expand() nicht unterstützt wird

            # ListItems auslesen
            items = target_combo.descendants(control_type="ListItem")
            result = []

            for item in items:
                item_id = getattr(item.element_info, "automation_id", "")
                item_text = getattr(item.element_info, "name", "") or item.window_text()
                result.append({"automation_id": item_id, "text": item_text})
                #print(f"- ID: {item_id!r} | Text: {item_text!r}")

            if not result:
                print(f"[i] Keine ListItems in ComboBox '{automation_id}' gefunden.")
                return []

            return result

        except Exception as e:
            print(f"[x] Fehler beim Auflisten der ComboBox-Items: {e}")
            return None
        
          
    def select_combobox_item(self, dlg, text: str, search_text: str) -> bool:
        """
        Wählt in einer ComboBox (über AutomationId) den Eintrag aus, der den Suchtext enthält.
        """
        if dlg is None:
            print("[x] Fehler: dlg ist None, kann keine ComboBox finden.")
            return False

        try:
            # ComboBox über AutomationId finden
            combos = dlg.descendants(control_type="ComboBox")
            target_combo = None
            for combo in combos:
                auto_id = getattr(combo.element_info, "name", "")
                if str(auto_id) == str(text):
                    target_combo = combo
                    break

            if not target_combo:
                print(f"[x] Keine ComboBox mit text '{text}' gefunden.")
                return False

            # ComboBox aufklappen (damit ListItems sichtbar werden)
            try:
                target_combo.expand()
            except Exception:
                pass  # manche UI-Frameworks brauchen das nicht

            # ListItems auslesen
            items = target_combo.descendants(control_type="ListItem")
            if not items:
                print("[x] Keine ListItems gefunden – eventuell nicht sichtbar oder virtualisiert.")
                return False

            # Eintrag mit passendem Text suchen (case-insensitive)
            match_item = None
            for item in items:
                text = getattr(item.element_info, "name", "") or item.window_text()
                if search_text.lower() in text.lower():
                    match_item = item
                    break

            if not match_item:
                print(f"[x] Kein Eintrag mit Text '{search_text}' gefunden.")
                return False

            # Auswahl treffen – meist funktioniert .click_input() zuverlässiger als .select()
            try:
                match_item.click_input()
            except Exception:
                try:
                    match_item.select()
                except Exception as e:
                    print(f"[x] Fehler beim Selektieren: {e}")
                    return False

            print(f"[✓] ComboBox-Eintrag '{search_text}' wurde erfolgreich ausgewählt.")
            return True

        except Exception as e:
            print(f"[x] Fehler beim Auswählen des ComboBox-Eintrags: {e}")
            return False
