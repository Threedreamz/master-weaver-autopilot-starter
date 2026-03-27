from libs.pywinauto.checkbox.checkbox import checkbox
from libs.pywinauto.process import winWerth_Process

wp = winWerth_Process()
wp.init()
ch = checkbox()

print(ch.isLiveBild(wp.dlg))