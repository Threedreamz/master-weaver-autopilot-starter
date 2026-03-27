from libs.pywinauto.topMenu.topMenu import topMenu
from libs.pywinauto.childWindow.SaveFileDialog.SaveFileDialog import SaveFileDialog
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.combobox.combobox import combobox
from libs.pywinauto.label.label import label
from libs.pywinauto.childWindow.SaveFileDialog.btn_save.btn_save import btn_save
from libs.pywinauto.voxel.voxel import voxel
from libs.pywinauto.button.button import ButtonPresser
from libs.pywinauto.textbox.textBox import TextBox_method
from libs.pywinauto.button.button_h import button_h
from libs.pywinauto.label.label_h import label_h
from libs.pywinauto.tabcontrol.tabcontrol import tabcontrol
from libs.pywinauto.button.buttons_e import buttons
from libs.pywinauto.label.label_e import label_e
from libs.pywinauto.profile.profile import profile
from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu
from libs.pywinauto.rohr.rohr import rohr
from libs.pywinauto.error_correction.error_correction import error_correction
from libs.pywinauto.childWindow.scan_preview.scan_preview import scan_preview
from libs.pywinauto.checkbox.checkbox import checkbox
from os.path import isfile
from time import sleep


class pseudi_pipe_h:
    def __init__(self):
        # Core
        self.vxl = voxel()
        self.label_ = label()
        self.btn = btn_save()
        self.tM = topMenu()
        self.pr = winWerth_Process()
        self.combo = combobox()

        # Process
        self.winWerth = winWerth_Process()

        # Elements
        self.label_element = label_e()
        self.button_element = buttons()

        # Element handlers
        self.btn_press = ButtonPresser()
        self.label = label()
        self.tbm = TextBox_method()
        self.check = checkbox()
        self.tabcontrol = tabcontrol()
        self.sc_pre = scan_preview()
        self.prf = profile()
        self.pr_menu = punkte_Menu()
        self.rh = rohr()
        self.err_corr = error_correction()

    def fileExists(self, path: str) -> bool:
        """Returns True if a file exists at the given path, otherwise False."""
        return isfile(path)

    def saveSTL(self, filename: str):
        if filename == "":
            print("Empty .stl filename")
            return False
##
#
#
#      tab->Messen
#      punkt->popkorn
#      
    def prepare(self, filename: str):
        if filename == "":
            print("Empty .stl filename")
            return False
#      tab->Messen
#
###
        
        
        
        self.pr.init()
        self.vxl.selectENDFIL(self.pr.dlg)

        sfd = SaveFileDialog(dlg=self.pr.dlg)
        self.tM.pressGrafik3D(dlg=self.pr.dlg)
        self.tM.pressSpeichernUnter(dlg=self.pr.dlg)

        print(sfd.is_savefile_dialog_open())

        sfd_dlg = sfd.find_savefile_dialog()
        if sfd_dlg is None:
            return "sfd_dlg is None"

        current_Location = f"C:\\Users\\K2000\\Desktop\\"

        stl_path = f"{current_Location}{filename}.stl"
        self.label_.setSFDpath(stl_path, dlg=sfd_dlg)
        self.combo.selectType(sfd_dlg, "stl")
        self.btn.pressSave(sfd_dlg)
        sleep(2)
        return self.fileExists(stl_path)

    def selectVoxelBtn(self):
        self.btn_press.press_by_automation_id(self.winWerth.dlg, "3403")

    def correctMessen(self):
        self.btn_press.press_by_automation_id(self.winWerth.dlg, "3398")

    def saveSTL_btn(self):
        self.btn_press.press_by_automation_id(self.winWerth.dlg, "3405")

    def openProfile(self, dlg):
        self.prf.openProfileWindow(dlg)

    def selectProfile(self, dlg, profile_name: str):
        ct_window = self.prf.getCTSensorDlg(dlg, True, 5)
        if not self.prf.isWindowOpen(ct_window):
            self.prf.openProfileWindow(ct_window)
        self.prf.selectListBoxItemByText(ct_window, profile_name)
        self.prf.closeWindow(self.prf.getCTSensorDlg(dlg),dlg)

    def choose_profile(self, dlg, profile_name):
        self.openProfile(dlg)
        self.selectProfile(dlg, profile_name)

    def selectTabDrehen(self):
        self.tabcontrol.selectTabDrehen(self.winWerth.dlg)

    def selectTabCT(self):
        self.tabcontrol.selectTabCT(self.winWerth.dlg)

    def rohrAn(self):
        self.selectTabCT()
        self.rh.rohrAn(self.winWerth.dlg)

    def checkLiveBild(self):
        self.tabcontrol.selectTabCT(self.winWerth.dlg)
        self.check.checkLiveBild(self.winWerth.dlg)

    def errorCheck_Correction(self):
        self.err_corr.correctErrors(self.winWerth.dlg)

    def setup(self):
        self.checkLiveBild()
        self.rohrAn()
        self.errorCheck_Correction()

    def getValueBox(self, dlg):
        self.rohrAn()
        return self.sc_pre.startPreScan()

    def preScanCheck(self):
        return self.sc_pre.startPreScan()

    def createBox(self, points):
        self.btn_press.press_by_text(self.winWerth.dlg, "Punkt")
        self.sc_pre.clickPunktBildverarbeiter(points)

    def startScan(self):
        return self.pressMessen_STL()

    def pressAuto(self):
        return self.btn_press.press_by_automation_id(self.winWerth.dlg, "3399")

    def selectBtnConfig(self):
        if self.btn_press.press_by_automation_id(self.winWerth.dlg, ""):
            return self.btn_press.press_by_automation_id(self.winWerth.dlg, "")
        return False

    def isRohrAn(self):
        return self.label.isLabelAvailable(15, self.winWerth.dlg)

    def waitForScanToComplete(self):
        count = 0
        while self.isRohrAn():
            sleep(2)
            count += 1
            if count >= 2000:   #60 minutes = 1000*2s 
                print("Scan timed out after 60 minutes.")
                return False
        return True 
    
    
    def pressR_Kont_3(self):
        pass

    def scanRoutine(self):
        self.pressAuto()
        self.selectBtnConfig()
        self.waitForScanToComplete()
        self.pressR_Kont_3()
        self.tabcontrol.selectTabRechnen()
        self.startScan()

