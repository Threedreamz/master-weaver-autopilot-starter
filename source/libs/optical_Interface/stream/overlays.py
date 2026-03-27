from __future__ import annotations
import cv2
import numpy as np
from typing import Tuple
from app.state import RecordState

RED  = (0, 0, 255)
PINK = (180, 105, 255)  # BGR

def _mean_int(arr: np.ndarray) -> int:
    return int(round(float(arr.mean()))) if arr.size > 0 else 0

def _draw_record_line(img: np.ndarray, p0, p1, label: str):
    if p0 is None or p1 is None:
        return
    cv2.line(img, p0, p1, PINK, 2, cv2.LINE_AA)
    tx = min(max(min(p0[0], p1[0]) + 6, 6), img.shape[1]-6)
    ty = min(max(min(p0[1], p1[1]) - 6, 20), img.shape[0]-6)
    cv2.putText(img, label, (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 3, cv2.LINE_AA)
    cv2.putText(img, label, (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, PINK, 1, cv2.LINE_AA)

def draw_margin_overlays(img: np.ndarray, contour: np.ndarray, record: RecordState) -> RecordState:
    """
    Zeichnet aktuelle Abstände (rot) + Rekorde (rosa) und aktualisiert den RecordState.
    """
    h, w = img.shape[:2]
    pts = contour.reshape(-1, 2)
    xs = pts[:, 0]
    ys = pts[:, 1]

    x_min = int(xs.min())
    x_max = int(xs.max())
    y_min = int(ys.min())
    y_max = int(ys.max())

    y_at_xmin = _mean_int(ys[xs == x_min])
    y_at_xmax = _mean_int(ys[xs == x_max])
    x_at_ymin = _mean_int(xs[ys == y_min])
    x_at_ymax = _mean_int(xs[ys == y_max])

    d_left   = x_min
    d_right  = (w - 1) - x_max
    d_top    = y_min
    d_bottom = (h - 1) - y_max

    # Aktuelle rote Linien
    p0_left,   p1_left   = (x_min,    y_at_xmin), (0,      y_at_xmin)
    p0_right,  p1_right  = (x_max,    y_at_xmax), (w - 1,  y_at_xmax)
    p0_top,    p1_top    = (x_at_ymin, y_min),    (x_at_ymin, 0)
    p0_bottom, p1_bottom = (x_at_ymax, y_max),    (x_at_ymax, h - 1)

    cv2.line(img, p0_left,   p1_left,   RED, 2, cv2.LINE_AA)
    cv2.line(img, p0_right,  p1_right,  RED, 2, cv2.LINE_AA)
    cv2.line(img, p0_top,    p1_top,    RED, 2, cv2.LINE_AA)
    cv2.line(img, p0_bottom, p1_bottom, RED, 2, cv2.LINE_AA)

    # Labels oben links
    lines = [
        f"L: {int(d_left)} px",
        f"R: {int(d_right)} px",
        f"T: {int(d_top)} px",
        f"B: {int(d_bottom)} px",
    ]
    base_x, base_y = 12, 24
    for i, s in enumerate(lines):
        cv2.putText(img, s, (base_x, base_y + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 3, cv2.LINE_AA)
    for i, s in enumerate(lines):
        cv2.putText(img, s, (base_x, base_y + i * 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, RED, 1, cv2.LINE_AA)

    # Rekorde aktualisieren (alle vier Seiten)
    if record.min_t is None or d_top < record.min_t or record.min_t < 3:
        record.min_t = int(d_top)
        record.line_t = (p0_top, p1_top)

    if record.min_b is None or d_bottom < record.min_b or record.min_b < 3:
        record.min_b = int(d_bottom)
        record.line_b = (p0_bottom, p1_bottom)

    if record.min_l is None or d_left < record.min_l or record.min_l < 3:
        record.min_l = int(d_left)
        record.line_l = (p0_left, p1_left)

    if record.min_r is None or d_right < record.min_r or record.min_r < 3:
        record.min_r = int(d_right)
        record.line_r = (p0_right, p1_right)

    # Rosa Rekord-Linien zeichnen
    if record.line_t:
        _draw_record_line(img, record.line_t[0], record.line_t[1], f"MIN T: {record.min_t} px")
    if record.line_b:
        _draw_record_line(img, record.line_b[0], record.line_b[1], f"MIN B: {record.min_b} px")
    if record.line_r:
        _draw_record_line(img, record.line_r[0], record.line_r[1], f"MIN R: {record.min_r} px")
    if record.line_l:
        _draw_record_line(img, record.line_l[0], record.line_l[1], f"MIN L: {record.min_l} px")

    return record