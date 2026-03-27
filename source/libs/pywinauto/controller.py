

###
#       This file is part of pywinauto library and controls sertain functionallities, bundled up to create whole functional tasks
#
#
#
###
from libs.pywinauto.label.label_h import label_h
from libs.pywinauto.button.button import ButtonPresser
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.profile.profile import profile
from libs.pywinauto.rohr.rohr import rohr
from libs.pywinauto.pywinconfig import PyWinConfig

from libs.pywinauto.tabcontrol.tabcontrol import tabcontrol
from libs.pywinauto.voxel.voxel import voxel

from libs.pywinauto.tooltip.tooltip import tooltip
from libs.pywinauto.combobox.combobox import combobox
from libs.pywinauto.punkte_Menu.punkte_Menu import punkte_Menu

class controller:

    #PHASES
    #   1 - Choose Profile
    #   2 - Check Life Bild
    #   3 - Check for Errors -> ajdust settings if needed
    #   4 - Röhre An
    #   5 - Find ScanWindow
    #   6 - PREP SCAN
    #   6.1 - Start Scan
    #   7 - Detect Finished Scan
    #   8 - Post Scan
    #   9 - Save Scan
    #   10 - End

    wpr = winWerth_Process()

    pb = ButtonPresser()
    lh = label_h()
    pr = profile()
    pc = punkte_Menu()
    rc = rohr()
    pyc = PyWinConfig()
    tb = tabcontrol()
    vb = voxel()

    dlg = None

    def __init__(self):
        self.wpr.init()
        dlg = self.wpr.dlg
        pass

    def openProfile(self, dlg):
        i=0
    def profileChooser(self, size : str, dlg):
        # 1 = xs
        # 2 = s
        # 3 = m
        # 4 = l
        # 5 = xl
        ff =  self.pr.find_ct_sensor(dlg)
        print(ff)
        if ff == None:
            print("Cant find CT Sensor profile window")
        else:
            print("found CT Sensor window")
            window = self.pr.getCTSensorDlg(dlg)
            
 
            er = self.pr.selectListBoxItemByText(window, "Size_110_L")
            
            print(f"rsultat: {er}")
            self.pr.closeWindow(window, dlg)
               #            
            print(self.pr.showButtons(window))
        print(f"THE DETECTION SAIYS : {self.pc.detectMenu(dlg=dlg)}")
        
    
    
    def lifeBildON(self):
        pass

    def RohrOn(self):
        pass

    def ScanWindow(self):
        pass

    def PreScan(self):
        pass

    def StartScan(self):
        pass