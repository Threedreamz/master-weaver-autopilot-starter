from libs.pywinauto.button.button_h import button_h
from libs.pywinauto.textbox.textbox_h import texbox_h
 

from libs.pywinauto.textbox.textboxs_e import textboxs_e

class TextBox_method:
    tb = textboxs_e()
    tb_h = texbox_h()
    def setAValue(self, val, dlg=None):
        if dlg is None:
            print("No dlg provided, creating new process connection.")
            return False
        self.tb_h.set_text(dlg, self.tb.A_textbox["id"], float(str(val)+".0000"))
        return True
    
    def getA_State_Value(self, dlg):
        if dlg is None:
            print("No dlg provided, creating new process connection.")
            return None
        return self.tb_h.get_text(dlg,automation_id=self.tb.A_textbox_State["id"])


