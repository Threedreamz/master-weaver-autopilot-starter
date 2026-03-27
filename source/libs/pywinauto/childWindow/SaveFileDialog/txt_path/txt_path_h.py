# -*- coding: utf-8 -*-
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.controls.uiawrapper import UIAWrapper

from libs.pywinauto.childWindow.SaveFileDialog.txt_path.txt_path_e import txt_path_e


class txt_path_h:

    txt_e = txt_path_e()

    """
    Liest/setzt Text in einer Textbox, die ausschließlich über ihr automation_id-Attribut
    (autoids.path) gefunden wird. Erwartet UIA-Backend und einen verbundenen dlg.
    """

    def _get_by_automation_id(self, dlg, timeout=10) -> UIAWrapper:
        """
        Sucht unter allen Descendants von dlg nach einem Control, dessen
        element_info.automation_id == autoids.path ist. Liefert einen UIAWrapper.
        """
        # optionales Warten, damit der Dialog vollständig aufgebaut ist
        dlg.wait("exists ready", timeout=timeout)

        target_id = self.txt_e.txt_path["id"]
        candidate = None

        # direkte, strikt Attribut-basierte Suche
        for ctrl in dlg.descendants():
            try:
                if getattr(ctrl.element_info, "automation_id", None) == target_id:
                    candidate = ctrl
                    break
            except Exception:
                continue

        if candidate is None:
            raise ElementNotFoundError(
                f"Control mit automation_id '{target_id}' nicht gefunden."
            )

        return UIAWrapper(candidate.element_info)

    def read_text(self, dlg, timeout=10) -> str:
        """
        Liest den aktuellen Textinhalt der gefundenen Textbox.
        """
        edit = self._get_by_automation_id(dlg, timeout=timeout)

        # bevorzugt UIA Value-Pattern
        try:
            val = edit.get_value()
            if val is not None:
                return str(val)
        except Exception:
            pass

        # Fallback
        try:
            return edit.window_text()
        except Exception as e:
            raise RuntimeError(
                f"Text konnte nicht gelesen werden (automation_id='{self.txt_e.txt_path["id"]}'): {e}"
            ) from e

    def set_text(self, dlg, text, timeout=10, clear_first=True) -> None:
        """
        Setzt den Textinhalt der gefundenen Textbox.
        """
        edit = self._get_by_automation_id(dlg, timeout=timeout)

        # Fokus setzen (robuster für Type-Keys-Fallback)
        try:
            edit.set_focus()
        except Exception:
            pass

        # 1) Bevorzugt: direkt via Edit-API
        try:
            if clear_first:
                try:
                    edit.select()  # select-all, wenn unterstützt
                except Exception:
                    pass
            edit.set_edit_text(str(text))

            # Verifizieren
            if self.read_text(dlg, timeout=timeout) == str(text):
                return
        except Exception:
            # weiter zum Fallback
            pass

        # 2) Fallback: Hotkeys/Tippen
        try:
            if clear_first:
                edit.type_keys("^a{BACKSPACE}", set_foreground=True, with_spaces=True)
            if text:
                edit.type_keys(str(text), with_spaces=True, set_foreground=True)
        except Exception as e:
            raise RuntimeError(
                f"Tippen fehlgeschlagen (automation_id='{self.txt_e.txt_path["id"]}'): {e}"
            ) from e

        # End-Check
        final = self.read_text(dlg, timeout=timeout)
        if final != str(text):
            raise RuntimeError(
                f"Verifikation fehlgeschlagen (automation_id='{self.txt_e.txt_path["id"]}'): "
                f"erwartet '{text}', erhalten '{final}'"
            )


# --- Beispielnutzung ---
# txt = txt_path_h()
# current = txt.read_text(dlg)
# txt.set_text(dlg, "Hallo Welt")
