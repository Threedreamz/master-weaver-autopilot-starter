from libs.pywinauto.voxel.voxel_e import voxel_e

from libs.pywinauto.button.button import ButtonPresser

from libs.pywinauto.treeview.treeview_item.treeview_item_h import treeview_item_h
from libs.pywinauto.treeview.treeview_item.treeview_item_e import treeview_item_e


from typing import Optional



class voxel_h:
    #NOTE
    #by text mostly, mostly id = "none"


    #basic pywinauto button-control functions
    bt = ButtonPresser()
    #element class
    t_e = voxel_e()
    th = treeview_item_h()
    th_e = treeview_item_e()
    #select voxel treeview item
    def selectENDFIL(self, dlg):
        self.th.click_tree_item(dlg, self.th_e.item_ENDFIL["text"])
    def selectVxVol_2(self, dlg):
        self.th.click_tree_item(dlg, self.th_e.item_VxVol_2["text"])

    #select voxel menu
    def menuVoxel3(self, dlg):
        self.bt.press(dlg, self.t_e._Datei["id"])


    #export voxel to stl
    def exportVoxel3(self, dlg):
        self.bt.press(dlg, self.t_e._Datei["id"])
