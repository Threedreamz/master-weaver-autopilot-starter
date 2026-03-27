from libs.pywinauto.tooltip.tooltip_h import tooltip_h

#press any tooltip button
#
#
#   important:  Drehen->CheckingIfChecked
#               SpeichernUnter->..
#
#

class tooltip:
    
    tp_h = tooltip_h()

    def pressDatei(self, dlg):
        self.tp_h.pressDatei_h(dlg)

    def pressEinstellung(self, dlg):
        self.tp_h.pressEinstellung_h(dlg)

    def pressKoordinaten(self, dlg):
        self.tp_h.pressKoordinaten_h(dlg)

    def pressWerkzeug(self, dlg):
        self.tp_h.pressWerkzeug_h(dlg)
