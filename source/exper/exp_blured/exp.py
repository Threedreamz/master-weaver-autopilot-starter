# gta_pause_overlay.py
import sys, time
from PyQt5 import QtWidgets, QtCore, QtGui
import mss
import numpy as np
import cv2

def grab_blurred_grayscale_overlay(darken=0.25, blur_ksize=31):
    # Monitor 0 = gesamter virtueller Desktop (alle Monitore)
    with mss.mss() as sct:
        mon = sct.monitors[0]
        shot = sct.grab(mon)
        img = np.array(shot)  # BGRA
    # nach BGR (drop alpha)
    bgr = img[:, :, :3]
    # Graustufen
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    # Gaussian Blur (muss ungerade sein)
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    # leicht abdunkeln
    blurred = cv2.convertScaleAbs(blurred, alpha=1.0 - darken, beta=0)
    # wieder nach RGB für Qt
    rgb = cv2.cvtColor(blurred, cv2.COLOR_GRAY2RGB)
    return rgb, (mon["width"], mon["height"])

class Overlay(QtWidgets.QWidget):
    def __init__(self, pixmap):
        super().__init__(None, QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        # Vollbild auf gesamten virtuellen Desktop
        desktop = QtWidgets.QApplication.desktop().availableGeometry()
        self.setGeometry(desktop)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
        self.setCursor(QtCore.Qt.BlankCursor)

        # Inhalt
        self.label = QtWidgets.QLabel(self)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)
        self.label.setGeometry(self.rect())

        # Opacity-Animation (sanftes “Atmen” beim Ein-/Ausblenden)
        self.effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QtCore.QPropertyAnimation(self.effect, b"opacity", self)
        self.anim.setDuration(280)  # ms
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self.anim.finished.connect(self._maybe_quit)
        self._closing = False

    def showEvent(self, e):
        # auf volle Fläche skalieren
        self.label.setGeometry(self.rect())
        self.anim.setDirection(QtCore.QAbstractAnimation.Forward)
        self.anim.start()
        super().showEvent(e)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close_with_fade()
        else:
            super().keyPressEvent(e)

    def mousePressEvent(self, e):
        # optional: Klick schließt
        self.close_with_fade()

    def close_with_fade(self):
        if self._closing:
            return
        self._closing = True
        self.anim.setDirection(QtCore.QAbstractAnimation.Backward)
        self.anim.start()

    def _maybe_quit(self):
        if self._closing:
            self.close()

def main():
    app = QtWidgets.QApplication(sys.argv)
    # Screenshot -> Blur+Grau
    rgb, (w, h) = grab_blurred_grayscale_overlay(darken=0.28, blur_ksize=35)

    # Numpy -> QImage -> QPixmap
    qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
    pix = QtGui.QPixmap.fromImage(qimg)

    # Overlay anzeigen
    ov = Overlay(pix)
    ov.showFullScreen()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
