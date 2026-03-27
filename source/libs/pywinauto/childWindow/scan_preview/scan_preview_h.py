
from __future__ import annotations
import threading
from typing import Optional, Dict, Any

import pyautogui
import time


import cv2
import numpy as np

from app.config import AppConfig, parse_args
from app.state import RecordState
from libs.stream_screen import iterate_screen
from libs.optical_Interface.bg_whiten import whiten_bg_array
from libs.optical_Interface.stream.detect_borders import detect_outer_outline_no_holes_array
from libs.optical_Interface.stream.overlays import draw_margin_overlays


class _StreamRunner:
    """
    Kapselt die Streaming-Schleife und stellt eine kleine API bereit.

    - start(block: bool = False): startet den Stream (optional blockierend)
    - stop(): beendet den Stream und schließt Fenster
    - get_minima(): liest die bisherigen Minimum-Werte (T/B/L/R)
    - reset_minima(): setzt die Rekorde zurück

    Nutzung als Singleton über die Modul-Helper-Funktionen:
        start_stream(...), end_stream(), getMin(), resetMin()
    """
    def __init__(self, cfg: Optional[AppConfig] = None) -> None:
        self.cfg: AppConfig = cfg if cfg is not None else parse_args()
        self.record: RecordState = RecordState()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()  # schützt Zugriff auf self.record

    # ---------------------- Öffentliche Methoden ----------------------
    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, *, block: bool = False) -> None:
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="screen_stream_loop", daemon=True)
        self._thread.start()
        if block:
            self._thread.join()

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop.set()
        # kurz warten, bis Thread sauber beendet
        self._thread.join(timeout=3.0)
        self._thread = None
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    def get_minima(self) -> Dict[str, Optional[int]]:
        """Gibt die bisherigen Minimalabstände der Session zurück."""
        with self._lock:
            return {
                "top": self.record.min_t,
                "bottom": self.record.min_b,
                "left": self.record.min_l,
                "right": self.record.min_r,
            }

    def reset_minima(self) -> None:
        with self._lock:
            self.record.reset()

    # ---------------------- Interne Streaming-Schleife ----------------------
    def _loop(self) -> None:
        cfg = self.cfg
        cv2.namedWindow(cfg.window_title, cv2.WINDOW_NORMAL)

        # Haupt-Stream-Schleife
        for frame_bgr in iterate_screen(region=cfg.region, monitor_index=cfg.monitor_index, fps=cfg.fps):
            if self._stop.is_set():
                break

            # Vorverarbeitung
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            white_bg_gray, _ = whiten_bg_array(
                gray,
                feather_sigma=1.5,
                morph_open=3,
                offset=0,
            )
            white_bg_bgr = cv2.cvtColor(white_bg_gray, cv2.COLOR_GRAY2BGR)

            # Kontur-Detektion + Overlays
            try:
                cnt, overlay, _mask = detect_outer_outline_no_holes_array(
                    white_bg_bgr,
                    blur_sigma=1.0,
                    morph_close=3,
                    min_area=500
                )
                with self._lock:
                    draw_margin_overlays(overlay, cnt, self.record)
                view = overlay
            except Exception as e:
                view = white_bg_bgr.copy()
                cv2.putText(view, str(e), (12, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)

            hint = "REC (Session): rosa Linien MIN T/B/L/R. 'r' = reset, 'q' = quit."
            cv2.putText(view, hint, (12, view.shape[0]-12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(view, hint, (12, view.shape[0]-12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

            cv2.imshow(cfg.window_title, view)
            k = cv2.waitKey(1) & 0xFF
            if k in (27, ord('q')):
                # Benutzer beendet mit ESC oder 'q'
                self._stop.set()
                break
            elif k in (ord('r'), ord('R')):
                with self._lock:
                    self.record.reset()

        cv2.destroyAllWindows()


# ---------------------- Modulweite Singleton-Instanz ----------------------
_runner_singleton: Optional[_StreamRunner] = None


def _get_or_create_runner(cfg: Optional[AppConfig] = None) -> _StreamRunner:
    global _runner_singleton
    if _runner_singleton is None:
        _runner_singleton = _StreamRunner(cfg)
    return _runner_singleton


# ---------------------- Öffentliche API-Funktionen ----------------------
def start_stream(cfg: Optional[AppConfig] = None, *, block: bool = False) -> None:
    """
    Startet den Bild-Stream. Falls bereits laufend, passiert nichts.
    - cfg: Optional eigene AppConfig (sonst parse_args())
    - block: Wenn True, kehrt die Funktion erst nach Ende des Streams zurück.
    """
    r = _get_or_create_runner(cfg)
    r.start(block=block)


def end_stream() -> None:
    """Beendet den Stream (falls aktiv) und schließt das Fenster."""
    if _runner_singleton is not None:
        _runner_singleton.stop()


def getMin() -> Dict[str, Optional[int]]:
    """
    Liefert die Minimalabstände dieser Session als Dict:
    {'top': int|None, 'bottom': int|None, 'left': int|None, 'right': int|None}
    """
    r = _get_or_create_runner()
    return r.get_minima()


def resetMin() -> None:
    """Setzt die Minimalabstände/Record-Linien der laufenden Session zurück."""
    r = _get_or_create_runner()
    r.reset_minima()


# ---------------------- CLI-Kompatibilität ----------------------
def run_app() -> None:
    """
    Bewahrt Abwärtskompatibilität zur bisherigen CLI-Nutzung.
    Entspricht: start_stream(block=True)
    """
    start_stream(block=True)

class scan_preview_h:
   
    def get_rectangle_points(self, coords: dict, scale_factor: float = 1.0):
        """
        Berechnet zwei globale Punkte (oben-links und unten-rechts) 
        aus den minimalen Abständen innerhalb einer gestreamten Region.

        Ermöglicht prozentuale Vergrößerung oder Verkleinerung des Rechtecks über scale_factor.

        region = [x, y, width, height]
        coords = {'top': int, 'bottom': int, 'left': int, 'right': int}
        scale_factor = 1.0  -> unverändert
                    1.1  -> 10% größer
                    0.9  -> 10% kleiner
        """
        # Region (x_start, y_start, width, height)
        region = [554, 27, 813, 1014]
        x_start, y_start, width, height = region

        if not coords or any(v is None for v in coords.values()):
            raise ValueError(f"Ungültige Koordinaten übergeben: {coords}")

        left_border   = int(coords["left"])
        right_border  = int(coords["right"])
        top_border    = int(coords["top"])
        bottom_border = int(coords["bottom"])

        # Lokale Koordinaten (innerhalb des Stream-Ausschnitts)
        x1_local = left_border
        y1_local = top_border
        x2_local = width - right_border
        y2_local = height - bottom_border

        # Mittelpunkt und Größe berechnen
        rect_width = x2_local - x1_local
        rect_height = y2_local - y1_local

        cx = x1_local + rect_width / 2
        cy = y1_local + rect_height / 2

        # Skalieren (symmetrisch vom Mittelpunkt aus)
        new_width = rect_width * scale_factor
        new_height = rect_height * scale_factor

        x1_local = cx - new_width / 2
        y1_local = cy - new_height / 2
        x2_local = cx + new_width / 2
        y2_local = cy + new_height / 2

        # In globale Bildschirmkoordinaten umrechnen
        x1_global = x_start + int(x1_local)
        y1_global = y_start + int(y1_local)
        x2_global = x_start + int(x2_local)
        y2_global = y_start + int(y2_local)

        return (x1_global, y1_global), (x2_global, y2_global)



    def click_rect_points(self, rect_points, dlg, drag=False):
        """
        Führt Mausklicks (oder Drag) auf den beiden Punkten in rect_points aus,
        bezogen auf das Fenster mit dem Namen 'Bildverarbeiter'.

        Parameter:
        - rect_points: ((x1, y1), (x2, y2)) -> obere linke und untere rechte Ecke
        - window_title: Fenstertitel oder Regex (Standard: 'Bildverarbeiter')
        - drag: Wenn True, wird zwischen den Punkten gezogen (drag); sonst zwei Klicks
        """
        print(rect_points)
        if not rect_points or rect_points == None:
            print("⚠️ Ungültige rect_points:", rect_points)
            return False

        (x1, y1), (x2, y2) = rect_points

        try:
            rect = dlg.rectangle()
        except Exception as e:
            print(f"❌ Fenster '{"Bildverarbeiter"}' nicht gefunden: {e}")
            return False

        win_left, win_top, win_right, win_bottom = rect.left, rect.top, rect.right, rect.bottom

        # Prüfen, ob die Punkte im Fenster liegen (Warnung, kein Abbruch)
        for (x, y) in [(x1, y1), (x2, y2)]:
            if not (win_left <= x <= win_right and win_top <= y <= win_bottom):
                print(f"⚠️ Punkt ({x}, {y}) liegt außerhalb des Fenstersbereichs ({win_left},{win_top},{win_right},{win_bottom}).")

        # Ausführung
        if drag:
            print(f"🟢 Ziehe von {rect_points[0]} nach {rect_points[1]}")
            pyautogui.moveTo(x1, y1)
            pyautogui.mouseDown()
            pyautogui.moveTo(x2, y2, duration=0.4)
            pyautogui.mouseUp()
        else:
            print(f"🟢 Klicke auf obere linke Ecke {rect_points[0]}")
            pyautogui.moveTo(x1, y1)
            pyautogui.mouseDown()
            time.sleep(0.1)
            pyautogui.mouseUp()

            time.sleep(0.25)

            print(f"🟢 Klicke auf untere rechte Ecke {rect_points[1]}")
            pyautogui.moveTo(x2, y2)
            pyautogui.mouseDown()
            time.sleep(0.1)
            pyautogui.mouseUp()

        print("✅ Klick-Aktion abgeschlossen.")
        return True

