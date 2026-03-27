from libs.pywinauto.voxel.voxel_h import voxel_h
from libs.pywinauto.sideButtons.sideButtons import sideButtons
from libs.pywinauto.process import winWerth_Process
from libs.pywinauto.button.button import ButtonPresser


from libs.pseudo_pipe.pywin_pipe import pywin_pipe
pw = pywin_pipe()
winWerth = winWerth_Process()
winWerth.init()
btn = ButtonPresser()
sideB = sideButtons()
#vx = voxel_h()

#vx.selectRaster(dlg=winWerth.dlg)
#vx.selectPunktLeftTop(dlg=winWerth.dlg)
#vx.selectVxVol_2(dlg=winWerth.dlg)

pw.choose_profile(winWerth.dlg,"Size_110_L")

#sideB.selectStandard(dlg=winWerth.dlg)

#sideB.selectRaster(dlg=winWerth.dlg)


