###
#
#   isWindowOpen        - return if window can be found as child window of main window
#   displayIndex        - return index of display where window is shown
#   isWindowMaximized   - return window state
#   windowMaximize
#
#   selectScope         - selects scope to scan (green box)
#       -> rotate by 360, get min boundairy 
#       -> choose Voxel button
#       -> get rect
#       -> select green box     -> 
#
###

from pywinauto import Application


from libs.monitor.monitor import monitor
from libs.drehen.drehen import drehen
from libs.pywinauto.childWindow.scan_preview.scan_preview_h import scan_preview_h
from concurrent.futures import ThreadPoolExecutor

from libs.pywinauto.childWindow.scan_preview.scan_preview_h  import start_stream, end_stream, getMin, resetMin
from app.config import AppConfig
import time as _time
class scan_preview:

#
##
#
#   Window Name : Bildverarbeiter
#   Main Process Name : MoSeS
#
##
#


    sp = scan_preview_h()
    drehen = drehen()
    winWerth_Preview_scan_title = "Bildverarbeiter"
    dlg = None
    
    def clickPunktBildverarbeiter(self, punkte):
        if self.dlg == None:
            self.connect()
        self.sp.click_rect_points(punkte, self.dlg, False)
    def startStream(self, monitor_index):
        
        cfg = AppConfig(
            monitor_index=monitor_index,        # Index des Monitors (0 = Hauptmonitor)
            region=[554, 27, 813,1014],            # Optional: (x, y, width, height), falls nur ein Ausschnitt gestreamt werden soll
            fps=25,                 # Frames per second
            window_title="Stream",  # Titel des OpenCV-Fensters
        )
        start_stream(cfg=cfg)
        # -> Mit 'q' oder ESC beenden

    def endStream(self): # sauber stoppen
        end_stream() 

    def getMinimum(self):  # {'top': 12, 'bottom': 45, 'left': 23, 'right': 31} (Beispiel)
        return getMin() 

    def resetMinimum(self): # Session-Minima zurücksetzen
        resetMin()

    def drehen360(self):
        self.drehen.drehen(360)

    def selectScope(self, coords):
        return self.sp.get_rectangle_points(coords, 1.2)

    def connect(self):
        try:
            self.app = Application(backend="uia").connect(title_re=self.winWerth_Preview_scan_title)
            self.dlg = self.app.window(title_re=self.winWerth_Preview_scan_title)
            return self.dlg
        except Exception as exc:
            print(f"Error : {exc}")
            return False
        

    def displayIndex(self, dlg):
        mr = monitor(dlg=dlg)               # dlg direkt beim Erzeugen setzen
        info = mr.get_window_monitor()      # alternativ: mr.get_window_monitor(dlg)
        if info == None:
            print("ERROR: no monitors or window found.")
            return None
        return info['monitor_index']

    def wait_for_valid_minima(self, timeout=20.0):
        t0 = _time.time()
        while _time.time() - t0 < timeout:
            coords = getMin()
            if all(v is not None for v in coords.values()):
                return coords
            _time.sleep(0.5)
        return None

    def run_parallel(self, drehen360, getMin_, monitor_index):
#
#       
#       scanner on -> locate window
#       stream starten -> positionierung ganz klein oben links display==window_display
#
#   PARALLEL
#       drehen360
#       getMin 
#   Danach
#       close Stream, getRect
#       drawVoxel
#
#

        coords = []
        
        # getMin() -> resetMin() + Drehen360()
        #          -> if Drehen360() done -> drawVoxel()
        # Messen() 
        _time.sleep(3.5)
        self.startStream(monitor_index)
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            
            
            self.resetMinimum()
            drehen = executor.submit(drehen360)
            
        # Warten bis beide fertig sind
            drehen.result()
            coords = self.wait_for_valid_minima()
           
            #_time.sleep(100)
            self.endStream()
            
        if coords == None:
            print("ERROR: cant get coords for prescan stream")
            return None
        else:
            rect_points = self.selectScope(coords)
            return rect_points
     
        #self.drawvoxel(rect_points)
        #self.messen

        #wechsel zu scan process

    def startPreScan(self):
        dlg = self.connect()
        if dlg == False:
            print("ERROR: dlg ist None.")
            return None
        displayIndex = self.displayIndex(dlg=dlg)
        if (not dlg) or dlg == None:
            Exception("Cant find scan preview window")
            return None
        print(displayIndex)
        
        if displayIndex == None:
            Exception("Cant find monitor or open window (scan preview)")
            return None
        
        input("Press Enter when ready...")
        return self.run_parallel(drehen360=self.drehen360, getMin_=self.getMinimum, monitor_index=displayIndex)
