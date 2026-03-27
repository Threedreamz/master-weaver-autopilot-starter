from libs.pywinauto.topMenu.topMenu import topMenu
from libs.pywinauto.childWindow.SaveFileDialog.SaveFileDialog import SaveFileDialog
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.combobox.combobox import combobox
from libs.pywinauto.label.label import label    
from libs.pywinauto.childWindow.SaveFileDialog.btn_save.btn_save import btn_save
from libs.pywinauto.voxel.voxel import voxel

from os.path import isfile

def fileExists(path: str) -> bool:
    """Returns True if a file exists at the given path, otherwise False."""
    return isfile(path)

def saveSTL(filename):
    if filename == "":
        print("Empty .stl filename")
        return
    vxl = voxel()
    label_ = label()
    btn = btn_save()
    tM = topMenu()
    pr = winWerth_Process()
    combo = combobox()
    pr.init()
    vxl.selectENDFIL(pr.dlg)

    sfd = SaveFileDialog(dlg=pr.dlg)



    tM.pressGrafik3D(dlg=pr.dlg)  
    tM.pressSpeichernUnter(dlg=pr.dlg) 

    print(sfd.is_savefile_dialog_open())

    sfd_dlg = sfd.find_savefile_dialog()
    if sfd_dlg == None:
        return "sfd_dlg is none"

    ##
    #   SFD full control aquired
    #
    #
    #
    ###

   

    stl_path = f"C:\\Users\\K2000\\Desktop\\{filename}.stl"
    label_.setSFDpath(stl_path,dlg=sfd_dlg)
    combo.selectType(sfd_dlg, "stl")
    btn.pressSave(sfd_dlg)

    if fileExists(stl_path):
        return True
    else:
        return False

print(saveSTL("efas"))