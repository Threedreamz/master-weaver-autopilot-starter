from libs.pseudo_pipe.pywin_pipe import pywin_pipe

from libs.pywinauto.process import winWerth_Process
pw = pywin_pipe()
winWerth = winWerth_Process()


b = False 

safety = False #False = safety on

#focus ->
# select voxel btn  
# select correct messen button
# select save btn + SafeFileDialog[path, speichern] -> file check -> wait till exists == true
#
#



def select_voxel():
    pw.selectVoxelBtn()
    print("[PIPE TEST] Voxel ausgewählt.")

def save_stl():
    pw.saveSTL()
    print("[PIPE TEST] STL gespeichert.")

def correct_messen():
    pw.correctMessen()
    print("[PIPE TEST] Messen korrigiert.")







if b:
    if not safety:
        exit("[PIPE TEST] Safety is OFF! Exiting...")
    else:
        try:
            winWerth.init()
            pw.openProfile(winWerth.dlg)


            pw.selectProfile("Size_110_L")

            pw.selectTabCT()
            pw.selectTabDrehen()
            pw.selectTabCT()
            pw.checkLiveBild()

            #### before scan
            #
            #
            #### pre scan
            #
            # -- drehen+get_min_points
            points = pw.preScanCheck()
            # -- pressPoints+Thrershold
            pw.createBox(points)
            #
            #
            #### [SCAN]
            #
            pw.startScan()
            pw.waitForScanToComplete()
            #
            #
            #### [EXPORT]
            sideB.selectStandard(dlg=winWerth.dlg)

            sideB.selectRaster(dlg=winWerth.dlg)


            
            #
            #
            pw.saveSTL()
            #
            #

        except Exception as e:
            print(f"[PIPE TEST] Fehler: {e}")