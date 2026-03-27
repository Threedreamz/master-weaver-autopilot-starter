
from libs.pywinauto.childWindow.SaveFileDialog.txt_path.txt_path_h import txt_path_h


#   read_text
#   set_text


class txt_path:

    txt_h = txt_path_h()


    def read_text(self, dlg):
        return self.txt_h.read_text(dlg)
    
    def set_text(self, dlg):
        return self.txt_h.set_text(dlg, "")