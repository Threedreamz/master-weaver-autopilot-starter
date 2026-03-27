"""
Status-Manager für PI-Status und andere Anzeigen
"""
from PySide6.QtCore import QObject, QTimer, QRect, Signal
from PySide6.QtGui import QPainter, QBrush, QPen, QColor
from PySide6.QtCore import Qt
from gui.config import Config, Styles

class StatusManager(QObject):
    """Verwaltet Status-Anzeigen und LED-Indikatoren"""
    
    # Signal für Status-Änderungen
    status_changed = Signal(bool)  # True = online, False = offline
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # PI Status
        self.pi_status = False  # False = offline/rot, True = online/grün
        
        # Timer für Demo-Status-Wechsel
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.toggle_pi_status)
        
    def start_demo_mode(self):
        """Startet den Demo-Modus (Status wechselt automatisch)"""
        self.status_timer.start(Config.STATUS_TOGGLE_INTERVAL)
    
    def stop_demo_mode(self):
        """Stoppt den Demo-Modus"""
        self.status_timer.stop()
    
    def set_pi_status(self, online):
        """Setzt den PI-Status manuell"""
        if self.pi_status != online:
            self.pi_status = online
            self.status_changed.emit(online)
            if self.parent_widget:
                self.parent_widget.update()
    
    def toggle_pi_status(self):
        """Wechselt den PI-Status (für Demo)"""
        self.set_pi_status(not self.pi_status)
    
    def get_pi_status_rect(self):
        """Rechteck für die PI-Status-Anzeige"""
        return QRect(15, 25, 80, 30)
    
    def get_led_rect(self):
        """Rechteck für die Status-LED"""
        return QRect(45, 30, 12, 12)
    
    def draw_pi_status(self, painter):
        """Zeichnet die PI-Status-Anzeige"""
        # PI Label
        painter.setPen(QPen(Styles.TEXT_COLOR, 1))
        painter.setFont(Styles.DEFAULT_FONT)
        painter.drawText(25, 40, "PI:")
        
        # Status LED
        self._draw_status_led(painter)
    
    def _draw_status_led(self, painter):
        """Zeichnet die Status-LED mit Glow-Effekt"""
        led_rect = self.get_led_rect()
        led_color = Styles.PI_STATUS_GREEN if self.pi_status else Styles.PI_STATUS_RED
        
        # LED Glow Effect
        glow_rect = QRect(
            led_rect.x() - 2, 
            led_rect.y() - 2, 
            led_rect.width() + 4, 
            led_rect.height() + 4
        )
        glow_color = QColor(led_color.red(), led_color.green(), led_color.blue(), 80)
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(glow_rect)
        
        # LED Kern
        painter.setBrush(QBrush(led_color))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1))
        painter.drawEllipse(led_rect)
        
        # LED Highlight für 3D-Effekt
        highlight_rect = QRect(led_rect.x() + 2, led_rect.y() + 2, 4, 4)
        painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(highlight_rect)
    
    def get_status_text(self):
        """Gibt den aktuellen Status als Text zurück"""
        return "Online" if self.pi_status else "Offline"
    
    def is_online(self):
        """Prüft ob der Status online ist"""
        return self.pi_status