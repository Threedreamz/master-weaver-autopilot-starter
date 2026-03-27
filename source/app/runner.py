from __future__ import annotations
import threading
from typing import Optional, Dict, Any

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


if __name__ == "__main__":
    run_app()
