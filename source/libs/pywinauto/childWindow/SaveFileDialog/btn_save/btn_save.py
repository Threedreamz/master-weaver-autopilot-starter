from libs.pywinauto.childWindow.SaveFileDialog.btn_save.btn_save_h import btn_save_h
class btn_save:
    def __init__(self):
        self.btnh = btn_save_h()
    def pressSave(self, dlg):
        self.btnh.pressSpeichern(dlg)