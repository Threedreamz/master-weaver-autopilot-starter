from libs.pywinauto.button.button import ButtonPresser
from libs.pywinauto.topMenu.topMenu_e import topMenu_e
from libs.pywinauto.topMenu.topMenu_h import topMenu_h

class topMenu:
    def __init__(self):
        self.btn = ButtonPresser()
        self.toph = topMenu_h()
        self.tope = topMenu_e()
    def pressSpeichernUnter(self, dlg):
        self.toph.press(dlg=dlg,automation_id=self.tope._Speichern_unter["id"])
    def pressGrafik3D(self, dlg):
        return self.toph.raw_click(dlg=dlg, text="Grafik3D")