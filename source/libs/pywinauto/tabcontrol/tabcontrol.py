from libs.pywinauto.button.button import ButtonPresser

from libs.pywinauto.label.label_h import label_h
from libs.pywinauto.tabcontrol.tabcontrol_e import tabcontrol_e

class tabcontrol:
    btnP = ButtonPresser()
    label_h_ = label_h()
    tab_e = tabcontrol_e()

    def selectTab(self, id, dlg):
        self.btnP.press_by_automation_id(dlg,id)
    
    
    def checkTabDrehen_byLabel(self,A_Label_Drehen, dlg_):
        print("trying to check lable availability")
        return self.label_h_.isLabelAvailable(index=A_Label_Drehen["index"],dlg=dlg_)

    def selectTabDrehen(self, dlg):
        self.selectTab(self.tab_e.drehen_tab["id"], dlg)

    def selectTabXray(self, dlg):
        self.selectTab(self.tab_e.xray_tab["id"], dlg)

    def selectTabCT(self, dlg):
        self.selectTab(self.tab_e.ct_tab["id"], dlg)
