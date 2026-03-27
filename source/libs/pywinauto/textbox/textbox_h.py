import logging
from typing import Optional

class texbox_h:
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    def find_edit_by_automation_id(self, dlg, automation_id: str) -> Optional[object]:
        """
        Findet ein Edit-Control durch einfaches Durchsuchen aller Edit-Felder per automation_id.
        Kein Wrapper, kein child_window.
        """
        if dlg is None:
            self.logger.error("Dialog ist None.")
            return None

        for idx, edit in enumerate(dlg.descendants(control_type="Edit")):
            auto_id = getattr(edit.element_info, "automation_id", "")
            if str(auto_id) == str(automation_id):
                return edit  # direktes Control-Objekt zurückgeben

        self.logger.warning("Keine Editbox mit automation_id '%s' gefunden.", automation_id)
        return None

    def set_text(self, dlg, automation_id: str, text: str) -> bool:
        """
        Setzt Text in ein Textfeld mit passender automation_id.
        """
        edit = self.find_edit_by_automation_id(dlg, automation_id)
        if not edit:
            self.logger.error("Textbox mit AutomationId %s nicht gefunden.", automation_id)
            return False

        try:
            edit.set_focus()

            try:
                edit.set_edit_text(text)
            except Exception:
                # Fallback falls set_edit_text nicht geht
                edit.select()
                edit.type_keys(text, with_spaces=True, set_foreground=True)

            return True
        except Exception as e:
            self.logger.exception("Fehler beim Setzen des Textes für %s: %s", automation_id, e)
            return False

    def get_text(self, dlg, automation_id: str) -> Optional[str]:
        """
        Liest den Text einer Editbox anhand automation_id.
        """
        edit = self.find_edit_by_automation_id(dlg, automation_id)
        if not edit:
            self.logger.error("Textbox mit AutomationId %s nicht gefunden.", automation_id)
            return None

        try:
            try:
                return edit.get_value()
            except Exception:
                return edit.window_text()
        except Exception as e:
            self.logger.exception("Fehler beim Lesen des Textes für %s: %s", automation_id, e)
            return None
