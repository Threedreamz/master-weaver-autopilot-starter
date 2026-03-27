import sys
import time
import math
import numpy as np
import cv2
from mss import mss
from PyQt5 import QtWidgets, QtGui, QtCore
import win32con
import win32gui
import win32api

# Config
FPS = 20
BLUR = 7
CANNY_LOW = 50
CANNY_HIGH = 150
DILATE_ITER = 2
APPROX_EPSILON = 8  # contour simplification
SWEEP_SPEED = 0.8  # radians per second
SWEEP_WIDTH = math.radians(30)  # angular width of the sweep (radians)
SWEEP_RADIUS_THICKNESS = 80  # thickness in pixels of radial band

class OverlayWindow(QtWidgets.QWidget):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.sct = mss()

        # Window flags: always on top, no frame, transparent background
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint |
                            QtCore.Qt.FramelessWindowHint |
                            QtCore.Qt.Tool)  # Tool -> kein Taskbar-Eintrag
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Vollbild über den Monitor
        self.setGeometry(monitor["left"], monitor["top"],
                         monitor["width"], monitor["height"])

        # Timer fürs Update
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(int(1000 / FPS))
        self.start_time = time.time()

        # Konturen-Speicher
        self.hulls = []

        # Fenster erstellen lassen, bevor wir WinAPI Flags ändern
        self.winId()
        hwnd = int(self.winId())

        exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        # Click-through + kein Fokus + Toolwindow
        new_exstyle = (exstyle |
                       win32con.WS_EX_TRANSPARENT |  # Klicks gehen durch
                       win32con.WS_EX_TOOLWINDOW |   # kein Taskbar-Eintrag
                       win32con.WS_EX_NOACTIVATE)    # stiehlt keinen Fokus

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_exstyle)

    def update_frame(self):
        # 1. Capture screen region (monitor)
        img = np.array(self.sct.grab(self.monitor))
        # mss returns BGRA
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        # 2. Preprocess and edge detect
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (BLUR, BLUR), 0)
        edges = cv2.Canny(blur, CANNY_LOW, CANNY_HIGH)
        # 3. Morphology to remove internal details, keep outer silhouettes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))  # larger kernel merges fine details
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        closed = cv2.dilate(closed, kernel, iterations=DILATE_ITER)
        # 4. Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hulls = []
        simplified = []
        for cnt in contours:
            if cv2.contourArea(cnt) < 500:  # ignore tiny stuff
                continue
            # optional: convex hull to get outermost shape
            hull = cv2.convexHull(cnt)
            # optional: approximate polygon to reduce vertices
            approx = cv2.approxPolyDP(hull, APPROX_EPSILON, True)
            hulls.append(approx)
            simplified.append(approx)
        self.hulls = hulls
        self.update()  # trigger paintEvent

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing)
        # Clear transparent background
        qp.fillRect(self.rect(), QtCore.Qt.transparent)
        # Time for sweep
        t = time.time() - self.start_time
        sweep_angle = (t * SWEEP_SPEED) % (2 * math.pi)
        # Draw a subtle dimming layer (so sweep effect shows better)
        dim_color = QtGui.QColor(0, 0, 0, 80)  # semi transparent dark
        qp.fillRect(self.rect(), dim_color)
        # For each hull draw only the portion inside the sweep band
        pen = QtGui.QPen(QtGui.QColor(0, 255, 150, 230))
        pen.setWidth(3)
        qp.setPen(pen)
        brush = QtGui.QBrush(QtGui.QColor(0, 255, 150, 30))
        qp.setBrush(QtCore.Qt.NoBrush)
        center_x = self.width() // 2
        center_y = self.height() // 2
        # optional: use center of screen as radar center or use mouse pos
        # draw hulls clipped by sweep band
        for hull in self.hulls:
            # Convert contour points to list of QPointF
            pts = [(int(p[0][0]), int(p[0][1])) for p in hull]
            # Draw only segments whose midpoint angle is within sweep band
            n = len(pts)
            if n < 2:
                continue
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                mx = (x1 + x2) / 2.0
                my = (y1 + y2) / 2.0
                # angle relative to center
                angle = math.atan2(my - center_y, mx - center_x)
                # normalize angles to [0, 2pi)
                a = angle % (2 * math.pi)
                sa = sweep_angle % (2 * math.pi)
                # compute smallest angular difference
                diff = min((a - sa) % (2*math.pi), (sa - a) % (2*math.pi))
                # compute radial distance to center
                r = math.hypot(mx - center_x, my - center_y)
                # Only draw if within angular width and radius threshold (creates a sweeping ring)
                if diff <= SWEEP_WIDTH/2 and abs(r - (0.35 * min(self.width(), self.height()))) < SWEEP_RADIUS_THICKNESS:
                    qp.drawLine(x1, y1, x2, y2)
        # draw a faint circular radar ring where sweep passes
        ring_radius = int(0.35 * min(self.width(), self.height()))
        qp.setPen(QtGui.QPen(QtGui.QColor(0,255,150,80), 1, QtCore.Qt.DashLine))
        qp.drawEllipse(center_x - ring_radius, center_y - ring_radius, ring_radius*2, ring_radius*2)
        qp.end()

def choose_primary_monitor():
    with mss() as s:
        monitors = s.monitors  # monitors[0] is all monitors, monitors[1] primary
        # pick primary
        return monitors[1]

def main():
    app = QtWidgets.QApplication(sys.argv)
    monitor = choose_primary_monitor()
    win = OverlayWindow(monitor)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
