from libs.pywinauto.voxel.voxel_h import voxel_h
from libs.pywinauto.process import winWerth_Process
winWerth = winWerth_Process()
winWerth.init()

vx = voxel_h()

vx.selectVoxel3(dlg=winWerth.dlg)
vx.selectVoxel3_dmis(dlg=winWerth.dlg)

