from libs.pywinauto.checkbox.checkbox import checkbox
from libs.pywinauto.process import winWerth_Process

wp = winWerth_Process()

wp.init()

ee = checkbox()

print(ee.isLiveBild(wp.dlg))