"""
Konfiguration und Konstanten für die Anwendung
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

class Config:
    """Zentrale Konfigurationswerte"""
    
    # Fenster-Eigenschaften
    WINDOW_WIDTH = 320
    WINDOW_HEIGHT = 110
    WINDOW_FLAGS = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    
    # Button-Eigenschaften
    BUTTON_SIZE = 18
    BUTTON_MARGIN = 12
    BUTTON_MARGIN_TOP_LEFT = 18
    MAIN_BUTTON_WIDTH = 100
    MAIN_BUTTON_HEIGHT = 30
    
    # Timer-Intervalle (in Millisekunden)
    MOUSE_CHECK_INTERVAL = 50
    STATUS_TOGGLE_INTERVAL = 3000
    HIDE_DELAY = 1000
    QUICK_HIDE_DELAY = 500
    
    # Animation
    ANIMATION_DURATION = 200
    
    # Positionierung
    TOP_TRIGGER_ZONE = 5  # Pixel vom oberen Bildschirmrand
    WINDOW_HIDE_OFFSET = 7  # Pixel die sichtbar bleiben wenn versteckt

class Styles:
    """UI-Styling-Konstanten"""
    
    # Container Style
    CONTAINER_STYLE = """
        #Container {
            background: rgba(145, 145, 155, 22);
            border: 2px solid rgba(155, 155, 255, 30);
            border-radius: 22px;
        }
    """
    
    # Farben
    PI_STATUS_GREEN = QColor(50, 200, 50)
    PI_STATUS_RED = QColor(220, 60, 60)
    
    BUTTON_SETTINGS = QColor(80, 120, 200)
    BUTTON_START = QColor(160, 180, 75)
    BUTTON_STOP = QColor(220, 60, 60)
    BUTTON_RESET = QColor(255, 165, 0)
    
    CLOSE_BUTTON_NORMAL = QColor(160, 160, 160, 100)
    CLOSE_BUTTON_HOVER = QColor(220, 80, 80, 200)
    MINIMIZE_BUTTON_NORMAL = QColor(160, 160, 160, 100)
    MINIMIZE_BUTTON_HOVER = QColor(200, 160, 80, 200)
    
    TEXT_COLOR = QColor(220, 220, 220)
    TEXT_COLOR_BRIGHT = QColor(255, 255, 255, 240)
    BORDER_COLOR = QColor(255, 255, 255, 50)
    
    # Fonts
    DEFAULT_FONT = QFont("Segoe UI", 11, QFont.Weight.Medium)
    BUTTON_FONT = QFont("Segoe UI", 10, QFont.Weight.Medium)
    ICON_FONT = QFont("Segoe UI", 10)