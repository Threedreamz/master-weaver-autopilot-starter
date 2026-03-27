from libs.pywinauto.voxel.voxel_e import voxel_e
from libs.pywinauto.voxel.voxel_h import voxel_h    
class voxel:

    def __init__(self):
        self.voxl_e = voxel_e()
        self.voxl_h = voxel_h()
    def selectVoxel(self,dlg):
        self.voxl_h.selectENDFIL(dlg)
    def selectENDFIL(self,dlg):
        self.voxl_h.selectENDFIL(dlg)
        