from libs.pywinauto.profile.profile_h import profile_h
from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu
class profile:
    pk = punkte_Menu()

    pr_helper = profile_h()


    def selectListBoxItemByText(self, dlg, text):
        return self.pr_helper.selectListBoxItemByText(dlg,text)
    
    def openProfileWindow(self, dlg):
        return self.pr_helper.openProfileWindow(dlg)

    def find_ct_sensor(self, dlg):
        return self.pr_helper.find_ct_sensor(dlg)

    def isWindowOpen(self, dlg, wait=False, timeout=10):
        return self.pr_helper.isWindowOpen(dlg)
    
    def showButtons(self, dlg_or_window):
        return self.pr_helper.showButtons(dlg_or_window)

    def showListBoxItems(self, dlg_or_window):
        return self.pr_helper.showListBoxItems(dlg_or_window)

    def getCTSensorDlg(self, dlg_or_window, wait=False, timeout=10):
        return self.pr_helper.getCTSensorDlg(dlg_or_window)
    
    def clickButtonByText(self, dlg, text):
        return self.pr_helper.clickButtonByText(dlg, text)
    
    def clickButtonById(self, dlg, text):
        return self.pr_helper.clickButtonById(dlg, text)
    
    def closeWindow(self, dgl_profile, dgl_win):
        if self.isWindowOpen(dgl_win):
            return self.pr_helper.clickButtonById(dgl_profile, "3573")
            print("Closed CT-Sensor")
        else:
            print("CT-Sensor window is not open.")
            return None

    def isWindowOpen(self, win_dlg):
        return self.pr_helper.find_ct_sensor(win_dlg)