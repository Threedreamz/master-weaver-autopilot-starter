from libs.pywinauto.combobox.combobox_e import combobox_e
from libs.pywinauto.combobox.combobox_h import combobox_h

class combobox:

    def __init__(self):
        self.cbh = combobox_h()
        self.cbe = combobox_e()
        

    def selectType(self, dlg, text) -> bool:
        if text=="stl":
            #self.cbh.list_combobox_items(dlg,self.cbe.SFD_type["id"] )
            self.cbh.select_combobox_item(dlg, self.cbe.SFD_type_ITEM_STL["text"],  self.cbe.SFD_type_ITEM_STL["text"])
        else:
            print("dsf")