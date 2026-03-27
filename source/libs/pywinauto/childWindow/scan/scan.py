
from pywinauto import Application
class scan:

##
#
#       get scan window, check for stage [wait till done]
#
#
##

    def getScanWindow(self):
        self.app = Application(backend="uia").connect(title_re=self.winWerth_title)
        self.dlg = self.app.window(title_re=self.winWerth_title)

    def isWindowOpen(self):


    def iswindowClosed(self):
        return not self.isWindowOpen()
    
    def isScanDone(self):
        return 