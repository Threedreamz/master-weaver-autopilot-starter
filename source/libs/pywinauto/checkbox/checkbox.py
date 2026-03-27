

from libs.pywinauto.checkbox.checkbox_h import checkbox_h

class checkbox:
    def __init__(self):
        self.ck_h = checkbox_h()

    def checkLiveBild(self, dlg):
        if not self.isLiveBild(dlg):
            print("setting schnellesLiveBild to true.")
            self.ck_h.setLiveBildChecked(dlg)
        print("schnellesLivebild is already checked/true.")

    def isLiveBild(self, dlg):
        return self.ck_h.isLiveBildChecked(dlg)
