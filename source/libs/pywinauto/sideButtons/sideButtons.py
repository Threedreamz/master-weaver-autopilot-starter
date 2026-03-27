from libs.pywinauto.voxel.voxel_e import voxel_e

from libs.pywinauto.button.button import ButtonPresser

from libs.pywinauto.treeview.treeview_item.treeview_item_h import treeview_item_h
from libs.pywinauto.treeview.treeview_item.treeview_item_e import treeview_item_e


from typing import Optional

from libs.pywinauto.sideButtons.sideButtons_e import sideButtons_e

class sideButtons:

    side_e = sideButtons_e()
    #select voxel treeview item


    # CT TAB + CT-Sensor[top right menue]

    def selectRaster(self, dlg):
        self.presser(dlg, index=self.side_e.item_STLVoxelV["index"])

    def selectPunktLeftTop(self, dlg):
        self.presser(dlg, index=self.side_e.punkt_leftTop_item["index"])


    # CT TAB + Rechner[top right menue a+b]


    def selectStandard(self, dlg):
  
        self.presser(dlg, index=self.side_e.item_Standard["index"])

    def selectSTLVoxelV(self, dlg):
  
        self.presser(dlg, index=self.side_e.item_Standard["index"])


    def presser(self, dlg, automation_id=None, name=None, index=None):
        """
        Drückt einen Button anhand von automation_id, name oder index.
        """
        if dlg is None:
            print("Fehler: Dialog (dlg) ist None.")
            return

        elements = dlg.descendants()

        if not elements:
            print("Keine Elemente gefunden.")
            return

        # --- Nach Index ---
        if index is not None:
            try:
                el = elements[index]
                el.click_input()
                print(f"✅ Element mit Index [{index}] geklickt.")
                return
            except Exception as e:
                print(f"❌ Fehler beim Klicken per Index [{index}]: {e}")
                return

        # --- Nach automation_id oder name ---
        for idx, el in enumerate(elements):
            try:
                info = el.element_info
                el_auto_id = getattr(info, "automation_id", "") or ""
                el_name    = getattr(info, "name", "")            or ""

                match_id   = automation_id is not None and el_auto_id == automation_id
                match_name = name          is not None and el_name    == name

                if match_id or match_name:
                    el.click_input()
                    print(f"✅ Element [{idx}] geklickt → AutoID='{el_auto_id}' | Name='{el_name}'")
                    return

            except Exception as e:
                print(f"⚠️ Element [{idx}] übersprungen: {e}")
                continue

        print("❌ Kein passendes Element gefunden.")

    #select voxel menu
    def menuVoxel3(self, dlg):
        self.bt.press(dlg, self.t_e._Datei["id"])


    #export voxel to stl
    def exportVoxel3(self, dlg):
        self.bt.press(dlg, self.t_e._Datei["id"])
