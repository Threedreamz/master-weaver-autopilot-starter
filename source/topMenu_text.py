from libs.pywinauto.topMenu.topMenu import topMenu
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.childWindow.SaveFileDialog.SaveFileDialog import SaveFileDialog
from libs.pywinauto.button.button import ButtonPresser
from libs.pywinauto.childWindow.SaveFileDialog.txt_path.txt_path_e import txt_path_e
from libs.pywinauto.childWindow.SaveFileDialog.btn_save.btn_save_e import btn_save_e


from time import sleep
winWerth = winWerth_Process()
winWerth.init()

tp = topMenu()
sfd = SaveFileDialog(winWerth.dlg)
btn = ButtonPresser()
txte = txt_path_e()
btne = btn_save_e()
sleep(0.1)

#GOAL : saveSTL(filename) -> open3d->sfd->checkfile->loop?->return
#3dgrafik
#if tp.pressGrafik3D(winWerth.dlg):

    #3dgragik -> speichern unter

    #tp.pressSpeichernUnter(winWerth.dlg)
print(sfd.is_savefile_dialog_open())
dlg_ = sfd.find_savefile_dialog()



btn.press(dlg_,text=btne.btn_close["text"] )
print(sfd.is_savefile_dialog_open())
if sfd.is_savefile_dialog_open():
    btn.press(dlg_,text=btne.btn_close["text"] )
print(sfd.is_savefile_dialog_open())