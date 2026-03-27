from libs.pywinauto.label.label_e import label_e

class label_h:
    # Label 6: 'A (°)'
    # Label 7: 'B (°)'
    # Label 8: 'C (°)'



    lables = label_e()

    def isLabelAvailable(self, index, dlg):
        if dlg is None:
            print("Error: dlg is None, availability can't be checked for labels.")
            return None

        labels = dlg.descendants(control_type="Text")
        if not labels:
            print("Error: No labels found.")
            return False

        for idx, label in enumerate(labels):
            label_text = label.window_text()  # oder: label.element_info.name
            #print(f"index : {idx}\t\ttext:{label_text}")
            #print(f"to match: {index} index and text {self.lables.A_Label_Drehen["text"]}")
            if idx == index and label_text in (self.lables.A_Label_Drehen["text"]) :
                return True
        print("Error: No labels found.")
        return False
    def is_label_available_by_id(self, dlg, automation_id):
        """
        Prüft, ob ein Label (Text-Control) mit der angegebenen Automation ID existiert.
        Gibt True oder False zurück.
        """
        if dlg is None:
            print("Error: dlg is None, availability can't be checked for labels.")
            return False

        try:
            # Alle Text-Elemente (Labels) durchsuchen
            labels = dlg.descendants(control_type="Text")

            for label in labels:
                auto_id = getattr(label.element_info, "automation_id", "")
                if str(auto_id) == str(automation_id):
                    return True

            return False

        except Exception as e:
            print(f"Error during label check: {e}")
            return False


    def get_label_text_by_id(self, dlg, automation_id):
        """
        Gibt den Text (name-Attribut) eines Labels mit der angegebenen Automation ID zurück.
        Falls nicht gefunden, wird None zurückgegeben.
        """
        if dlg is None:
            print("Error: dlg is None, can't read label text.")
            return None

        try:
            labels = dlg.descendants(control_type="Text")

            for label in labels:
                auto_id = getattr(label.element_info, "automation_id", "")
                if str(auto_id) == str(automation_id):
                    # Name / Text-Inhalt abrufen
                    return getattr(label.element_info, "name", "") or label.window_text()

            return None

        except Exception as e:
            print(f"Error during label text read: {e}")
            return None
        
    def isLabelTextEqualByID(self, id, expected_text, dlg):
            if dlg is None:
                print("Error: dlg is None, availability can't be checked for labels.")
                return None
            if expected_text == self.get_label_text_by_id(dlg, id,):
                return True
            return False        
    def isRohrAn(self): 
        self.labelState = self.isLabelAvailable(15, self.winWerth.dlg)
        return self.labelState
    

    def set_edit_text(self, dlg, identifier, text: str) -> bool:
        """
        Setzt den Text einer Edit-Textbox im gegebenen Dialog über descendants().

        Parameter:
            dlg: Das Dialogfenster (z. B. von pywinauto Application().window()).
            identifier: AutomationId (int/str) oder sichtbarer Text.
            text: Der einzutragende Text.

        Rückgabe:
            True, wenn erfolgreich, sonst False.
        """
        if dlg is None:
            print("[x] Fehler: dlg ist None, kann kein Edit-Feld finden.")
            return False

        try:
            edits = dlg.descendants(control_type="Edit")
            target_edit = None

            for edit in edits:
                auto_id = getattr(edit.element_info, "automation_id", "")
                name = getattr(edit.element_info, "name", "")

                if str(auto_id) == str(identifier) or str(name).strip() == str(identifier).strip():
                    target_edit = edit
                    break

            if not target_edit:
                raise RuntimeError(f"Edit-Feld mit ID/Text '{identifier}' wurde nicht gefunden.")

            target_edit.set_edit_text(text)
            return True

        except Exception as e:
            print(f"[x] Fehler beim Setzen des Textes: {e}")
            return False


    def get_edit_text(self, dlg, identifier) -> str:
        """
        Liest den Text aus einer Edit-Textbox im gegebenen Dialog.

        Parameter:
            dlg: Das Dialogfenster (z. B. von pywinauto Application().window()).
            identifier: AutomationId (int/str) oder sichtbarer Text.

        Rückgabe:
            Aktueller Textinhalt der Edit-Textbox, oder leerer String bei Fehler.
        """
        try:
            if isinstance(identifier, int) or str(identifier).isdigit():
                edit = dlg.child_window(auto_id=str(identifier), control_type="Edit")
            else:
                edit = dlg.child_window(title=identifier, control_type="Edit")

            if not edit.exists():
                raise RuntimeError(f"Edit-Feld '{identifier}' wurde nicht gefunden.")

            return edit.get_value()
        except Exception as e:
            print(f"[x] Fehler beim Lesen des Textes: {e}")
            return ""





