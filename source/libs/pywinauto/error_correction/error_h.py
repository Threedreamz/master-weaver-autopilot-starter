from libs.pywinauto.error_correction.error_e import error_e

from libs.pywinauto.label.label_h import label_h

class error_h:
    def __init__(self):
        self.er_e = error_e()
        self.lb_h = label_h()

    def isError(self, dlg):
        if self.getLeftError(dlg) or self.getRightError(dlg):

            
            #move +5%. move -5% ++ progression till 40%, else BREAK
            current_value = 5
            original_value = self.ReadLabelValue(dlg, self.er_e.error_left["id"])
            count = 0
            while self.getLeftError(dlg) or self.getRightError(dlg):
                if count == 8:
                    Exception("Error cant be corrected. error_h.py ->isError()")
                    return None
                current_value =((count*5)*0.1)
                if count%2 == 0:
                    current_value=-1*current_value
                current_value = current_value+original_value
                
                count += 1
                
    def getLeftError(self, dlg):
        tmp_value = self.lb_h.isLabelAvailable(self.er_e.error_left["id"])
        if tmp_value:
            if tmp_value < 0.9:
                return True
            else:
                return False
        else:
            Exception(f"ERROR: no label found with id {self.er_e.error_left["id"]} for Left ERROR-CHECK.")
    def getRightError(self, dlg):
        tmp_value = self.lb_h.isLabelAvailable(self.er_e.error_right["id"])
        if tmp_value:
            if tmp_value < 0.9:
                return True
            else:
                return False
        else:
            Exception(f"ERROR: no label found with id {self.er_e.error_left["id"]} for Left ERROR-CHECK.")
