import logging
from typing import Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ButtonPresser:

    def press(self, dlg, automation_id: Optional[str] = None,text: Optional[str] = None, index: Optional[int] = None) -> bool:
        """
        Drückt einen Button entweder anhand des automation_id oder des Indexes.
        """
        if automation_id is not None:
            return self.press_by_automation_id(dlg, automation_id)

        if index is not None:
            return self.press_by_index(dlg, index)

        if text is not None:
            return self.press_by_text(dlg, text)

        logger.error("Weder automation_id noch index angegeben.")
        return False

    def press_by_automation_id(self, dlg, automation_id: str) -> bool:
        logger.info("Suche Button mit automation_id: %s", automation_id)

        try:
            buttons = dlg.descendants(control_type="Button")
            for i, btn in enumerate(buttons):
                btn_auto_id = getattr(btn.element_info, "automation_id", "None")
               
                if btn_auto_id == automation_id:
                    logger.info("Button #%d mit automation_id '%s' gefunden, klicke...", i, automation_id)
                    btn.click_input()
                    return True

            logger.warning("Kein Button mit automation_id '%s' gefunden.", automation_id)
        except Exception as e:
            logger.exception("Fehler beim Suchen nach Buttons: %s", e)

        return False

    def press_by_index(self, dlg, index: int) -> bool:
        logger.info("Drücke Button mit Index: %d", index)

        try:
            buttons = dlg.descendants(control_type="Button")
            if 0 <= index < len(buttons):
                logger.info("Button #%d gefunden, klicke...", index)
                buttons[index].click_input()
                return True
            else:
                logger.error("Index %d außerhalb der Button-Liste (Anzahl: %d)", index, len(buttons))
        except Exception as e:
            logger.exception("Fehler beim Zugriff auf Button per Index: %s", e)

        return False
    
    def press_by_text(self, dlg, text: str) -> bool:
        logger.info("Suche Button mit text: %s", text)

        try:
            buttons = dlg.descendants(control_type="Button")
            for i, btn in enumerate(buttons):
                btn_auto_id = getattr(btn.element_info, "name", "None")
                
                if btn_auto_id == text:
                    logger.info("Button #%d mit text '%s' gefunden, klicke...", i, text)
                    btn.click_input()
                    return True

            logger.warning("Kein Button mit text '%s' gefunden.", text)
        except Exception as e:
            logger.exception("Fehler beim Suchen nach Buttons: %s", e)

        return False


