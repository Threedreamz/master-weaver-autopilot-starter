#!/usr/bin/env python3
import traceback
from time import sleep

from libs.pseudo_pipe_h import pseudi_pipe_h


class pseudo_pipe:
    def __init__(self):
        self.pipe = pseudi_pipe_h()
        print("[PIPE] Initialized pseudo_pipe")

    # -------------------------------------------------------
    # Helper
    # -------------------------------------------------------
    def _safe(self, action_name, fn, *args, **kwargs):
        """
        Führt Funktionen sicher aus und gibt bei Error False zurück.
        """
        print(f"[PIPE] → {action_name} ...")
        try:
            result = fn(*args, **kwargs)
            print(f"[PIPE] ✔ {action_name} → {result}")
            return result
        except Exception as e:
            print(f"[PIPE] ✘ Fehler bei {action_name}: {e}")
            traceback.print_exc()
            return False

    # -------------------------------------------------------
    # High-level API
    # -------------------------------------------------------

    def setup(self):
        """ Livebild / Rohr an / Error Corrections """
        return self._safe("setup()", self.pipe.setup)

    def save_stl(self, filename: str):
        """ Speichert STL """
        return self._safe(f"saveSTL({filename})", self.pipe.saveSTL, filename)

    def get_box_values(self):
        """ Holt Werte aus der PreScan-Box """
        return self._safe("getValueBox()", self.pipe.getValueBox, self.pipe.winWerth.dlg)

    def create_box(self, points: list):
        """ Erstellt Box über eine Punkteliste """
        return self._safe("createBox()", self.pipe.createBox, points)

    def pre_scan(self):
        """ Führt einen PreScan aus """
        return self._safe("preScan()", self.pipe.preScanCheck)

    def start_scan(self):
        """ Startet den finalen Scan """
        return self._safe("startScan()", self.pipe.startScan)

    def wait_scan_complete(self):
        """ Wartet, bis Scan abgeschlossen ist """
        return self._safe("waitForScanToComplete()", self.pipe.waitForScanToComplete)

    def select_profile(self, name: str):
        """ Wählt ein Profil """
        return self._safe(f"selectProfile({name})", self.pipe.selectProfile, name)

    def rohr_an(self):
        """ Aktiviert das Rohr """
        return self._safe("rohrAn()", self.pipe.rohrAn)

    def livebild(self):
        """ Kontrolliert/aktiviert Livebild """
        return self._safe("checkLiveBild()", self.pipe.checkLiveBild)

    # -------------------------------------------------------
    # Full Routine
    # -------------------------------------------------------
    def full_auto(self, box_points: list, profile_name: str, stl_name: str):
        """
        Führt eine kompletten Scanablauf aus.
        1. Setup
        2. Profil wählen
        3. PreScan → Box
        4. Scan
        5. STL speichern
        """

        print("\n===================")
        print("  FULL AUTO START  ")
        print("===================\n")

        if not self.setup():
            return "setup_failed"

        sleep(1)

        if not self.select_profile(profile_name):
            return "profile_failed"

        sleep(1)

        if not self.pre_scan():
            return "prescan_failed"

        if not self.create_box(box_points):
            return "box_failed"

        if not self.start_scan():
            return "scan_start_failed"

        if not self.wait_scan_complete():
            return "scan_timeout"

        if not self.save_stl(stl_name):
            return "save_failed"

        print("\n===================")
        print(" FULL AUTO SUCCESS ")
        print("===================\n")

        return "success"
