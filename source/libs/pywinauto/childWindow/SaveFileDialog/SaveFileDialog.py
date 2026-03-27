from pywinauto.controls.uiawrapper import UIAWrapper


class SaveFileDialog:
    """Klasse zum Erkennen und Auslesen eines 'Speichern unter'-Dialogs über ein vorhandenes Hauptfenster (dlg)."""

    def __init__(self, dlg=None):
        self.dlg = dlg
        self.save_dlg = None

    def is_savefile_dialog_open(self) -> bool:
        """
        Prüft, ob innerhalb des übergebenen Dialogs ein 'Speichern unter' Fenster existiert.
        """
        if not self.dlg:
            print("[x] Kein Hauptdialog übergeben.")
            return False

        try:
            children = self.dlg.children()
            for child in children:
                title = child.window_text().lower()
                if "speichern unter" in title or "save as" in title:
                    print(f"[i] Savefile-Dialog erkannt: {child.window_text()}")
                    return True
            return False
        except Exception as e:
            print(f"[x] Fehler bei Prüfung auf Savefile-Dialog: {e}")
            return False

    def find_savefile_dialog(self) -> UIAWrapper | None:
        """
        Findet und speichert den 'Speichern unter'-Dialog innerhalb des übergebenen Hauptdialogs.
        Gibt das gefundene Dialogobjekt zurück oder None.
        """
        if not self.dlg:
            print("[x] Kein Hauptdialog übergeben.")
            return None

        try:
            children = self.dlg.children()
            for child in children:
                title = child.window_text().lower()
                if "speichern unter" in title or "save as" in title:
                    self.save_dlg = child
                    print(f"[i] Savefile-Dialog gefunden: {child.window_text()}")
                    return self.save_dlg
            print("[i] Kein Savefile-Dialog gefunden.")
            return None
        except Exception as e:
            print(f"[x] Fehler beim Finden des Savefile-Dialogs: {e}")
            return None

    def list_elements(self):
        """
        Listet alle anklickbaren sichtbaren Elemente des gespeicherten Savefile-Dialogs auf.
        Gibt Index, Typ, Text und AutomationId aus.
        """
        if not self.save_dlg:
            print("[x] Kein Savefile-Dialog gespeichert. Bitte erst find_savefile_dialog() ausführen.")
            return

        try:
            elements = self.save_dlg.descendants()
            print(f"[i] {len(elements)} Elemente im Dialog '{self.save_dlg.window_text()}':\n")

            for idx, elem in enumerate(elements):
                try:
                    if elem.is_visible() and elem.is_enabled():
                        ctrl_type = elem.friendly_class_name()
                        name = elem.window_text() or "(kein Text)"
                        auto_id = elem.element_info.automation_id or "(keine ID)"
                        print(f"[{idx}] Type='{ctrl_type}' | Text='{name}' | AutomationId='{auto_id}'")
                except Exception:
                    pass
        except Exception as e:
            print(f"[x] Fehler beim Auflisten der Elemente: {e}")


