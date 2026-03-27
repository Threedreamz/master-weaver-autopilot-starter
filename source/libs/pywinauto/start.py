from libs.pywinauto.process import winWerth_Process


def getTxtBox(dlg):
    if dlg is None:
        print("No dlg provided, creating new process connection.")
        return None
    # Finde alle Textboxen (Edit Controls)
    textboxes = dlg.descendants(control_type="Edit")

    # Schreibe in jede Textbox den Wert 360 (vorher Inhalt löschen)
    for idx, tb in enumerate(textboxes):
        try:
            if idx == 2:
                tb.set_focus()                      # optional: Textbox fokussieren
                tb.set_edit_text("360.0000")            # alten Inhalt löschen & 360 reinschreiben
                print(f"Textbox {idx} erfolgreich auf 360 gesetzt.")
        except Exception as e:
            print(f"Textbox {idx} konnte nicht beschrieben werden: {e}")
