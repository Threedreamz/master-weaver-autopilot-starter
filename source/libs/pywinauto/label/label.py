from libs.pywinauto.label.label_h import label_h
from libs.pywinauto.label.label_e import label_e


class label:
    label_handler = label_h()
    label_e = label_e()
    def isLableAvailable(self, index, dlg):
        return self.label_handler.isLabelAvailable(index, dlg)
    
    def isRohrAn(self, dlg): 
        return self.label_handler.isLabelAvailable(15, dlg)
    
    def isLabelTextEqualByID(self, id, expected_text, dlg):
        return self.label_handler.isLabelTextEqualByID(id, expected_text, dlg)

    def isRohrAn(self, dlg):
        state = self.isLabelTextEqualByID(self.label_e.A_Label_Anzeige, "Rohr an", dlg)
        return state
    
    def isRohrAus(self, dlg):
        state = self.isLabelTextEqualByID(self.label_e.A_Label_Anzeige, "Rohr aus", dlg)
        return state
    
    def getSFDpath(self, dlg):
        path = self.label_handler.get_label_text_by_id(dlg, self.label_e.SFD_txt_path["text"])
        return path
    def setSFDpath(self, path, dlg):
        self.label_handler.set_edit_text(dlg, self.label_e.SFD_txt_path["text"], path)
