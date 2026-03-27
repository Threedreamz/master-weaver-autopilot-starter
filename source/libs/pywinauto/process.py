from pywinauto import Application

class winWerth_Process:
    winWerth_path = ""

    winWerth_title = ""

    # Verbinde dich mit dem richtigen WinWerth-Fenster
    #app = Application(backend="uia").connect(title_re=r"WinWerth - \[\]")
    #dlg = app.window(title_re=r"WinWerth - \[\]")
    
    def init(self, proc_type="uia"):
        self.winWerth_path = r"C:\Program Files (x86)\WinWerth\WinWerth 2023\WinWerth.exe"
        self.winWerth_title = r"WinWerth - \[\]"
        self.app = Application(backend=proc_type).connect(title_re=self.winWerth_title)
        self.dlg = self.app.window(title_re=self.winWerth_title)

    def connect(self):
        self.app = Application(backend="uia").connect(title_re=self.winWerth_title)
        self.dlg = self.app.window(title_re=self.winWerth_title)

    def getApp(self):
        return self.app

    def getDlg(self):
        return self.dlg

