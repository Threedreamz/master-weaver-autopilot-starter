from libs.pywinauto.error_correction.error_e import error_e
from libs.pywinauto.error_correction.error_h import error_h

class error_correction:

    def __init__(self):
        self.er_h = error_h()
        self.er_e = error_e()

    def getErrorValues(self, dlg):
        i=0 #place_holder
        #getvaluesfromTextBoxesbyID
        #checkIfValueBox = red
    def correctErrors(self, dlg):
    
        if self.getErrorValues():
            self.fixError()
