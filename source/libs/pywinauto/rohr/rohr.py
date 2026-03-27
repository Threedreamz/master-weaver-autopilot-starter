
#
##
#   Functions needed:
#       Röhre An / Aus
#       Check Röhrenstatus
#       CanStart? 
#           -> "Schnelles View" checkbox on?
#           -> is red error?
#               -> fix red error
#       IsProcessDone?
#           -> which state?
#               States:
#                       CT Preview
#                       LoadingWindow || ViewWindow
#
#
#
##
##

from libs.pywinauto.rohr.rohr_e import rohr_e
from libs.pywinauto.button.button import ButtonPresser
class rohr:
    r_e = None
    btnPr = None
    def __init__(self):
        self.r_e = rohr_e()
        self.btnPr = ButtonPresser()
        pass    

    def rohrAn(self, dlg):
        self.btnPr.press_by_automation_id(dlg, self.r_e.rohr["id"])