


from libs.pywinauto.button.button import ButtonPresser

from libs.pywinauto.childWindow.SaveFileDialog.btn_save.btn_save_e import btn_save_e



# pressSpeichern


class btn_save_h:
    btn_e = btn_save_e()
    btnPr = ButtonPresser()

    def pressSpeichern(self, dlg):
        self.btnPr.press(dlg, text=self.btn_e.btn_save["text"])
