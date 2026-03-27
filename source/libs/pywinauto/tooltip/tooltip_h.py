from libs.pywinauto.tooltip.tooltip_e import tooltip_e
from libs.pywinauto.topMenu import tooltip_h
from libs.pywinauto.button.button import ButtonPresser

from typing import Optional



class tooltip_h:
    #NOTE
    #by text mostly, mostly id = "none"


    #basic pywinauto button-control functions
    bt = ButtonPresser()
    #element class
    t_e = tooltip_e()


    def pressDatei_h(self, dlg):
        self.bt.press(dlg, automation_id=self.t_e._Datei["text"])

    def pressEinstellung_h(self, dlg):
        self.bt.press(dlg, automation_id=self.t_e._Einstellungen["text"])

    def pressKoordinaten_h(self, dlg):
        self.bt.press(dlg, automation_id=self.t_e._Koordinatensystem["text"])

    def pressWerkzeug_h(self, dlg):
        self.bt.press(dlg, automation_id=self.t_e._Werkzeug["text"])

    def pressGrafik3D_h(self, dlg):
        self.tp.raw_click(dlg, automation_id=None, text=self.t_e._Grafik3D["text"])
