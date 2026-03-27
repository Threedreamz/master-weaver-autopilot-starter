"""
Button-Management für die Hauptanwendung
"""
from PySide6.QtCore import QRect, QObject, Signal
from PySide6.QtGui import QPainter, QBrush, QPen, QColor
from PySide6.QtCore import Qt
from gui.config import Config, Styles

class ButtonManager(QObject):
    """Verwaltet alle Buttons und deren Zustände"""
    
    # Signals für Button-Klicks
    close_clicked = Signal()
    minimize_clicked = Signal()
    settings_clicked = Signal()
    start_clicked = Signal()
    stop_clicked = Signal()
    reset_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        
        # Hover-Zustände
        self.hover_states = {
            'close': False,
            'minimize': False,
            'settings': False,
            'start': False,
            'stop': False,
            'reset': False
        }
    
    def get_close_button_rect(self):
        """Rechteck für den Schließen-Button"""
        return QRect(
            self.parent_widget.width() - Config.BUTTON_SIZE - Config.BUTTON_MARGIN - Config.BUTTON_MARGIN_TOP_LEFT,
            Config.BUTTON_MARGIN, 
            Config.BUTTON_SIZE, 
            Config.BUTTON_SIZE
        )
    
    def get_minimize_button_rect(self):
        """Rechteck für den Minimieren-Button"""
        return QRect(
            self.parent_widget.width() - 2 * Config.BUTTON_SIZE - Config.BUTTON_MARGIN -  8 - Config.BUTTON_MARGIN_TOP_LEFT,
            Config.BUTTON_MARGIN, 
            Config.BUTTON_SIZE, 
            Config.BUTTON_SIZE
        )
    
    def get_settings_button_rect(self):
        """Rechteck für den Einstellungen-Button"""
        return QRect(
            self.parent_widget.width() - 3 * Config.BUTTON_SIZE - Config.BUTTON_MARGIN - 16 - Config.BUTTON_MARGIN_TOP_LEFT,
            Config.BUTTON_MARGIN, 
            Config.BUTTON_SIZE, 
            Config.BUTTON_SIZE
        )
    X_BOX_BUTTONS = 20
    Y_BOX_BUTTONS = 44
    def get_start_button_rect(self):
        """Rechteck für den Start-Button"""
        return QRect(self.X_BOX_BUTTONS + 30, self.Y_BOX_BUTTONS + 10, Config.MAIN_BUTTON_WIDTH, Config.MAIN_BUTTON_HEIGHT)
    
    def get_stop_button_rect(self):
        """Rechteck für den Stop-Button"""
        return QRect(self.X_BOX_BUTTONS + 100, self.Y_BOX_BUTTONS + 10, Config.MAIN_BUTTON_WIDTH, Config.MAIN_BUTTON_HEIGHT)
    
    def get_reset_button_rect(self):
        """Rechteck für den Reset-Button"""
        return QRect(self.X_BOX_BUTTONS + 170, self.Y_BOX_BUTTONS + 10, Config.MAIN_BUTTON_WIDTH, Config.MAIN_BUTTON_HEIGHT)
    
    def update_hover_states(self, mouse_pos):
        """Aktualisiert die Hover-Zustände basierend auf der Mausposition"""
        self.hover_states['close'] = self.get_close_button_rect().contains(mouse_pos)
        self.hover_states['minimize'] = self.get_minimize_button_rect().contains(mouse_pos)
        self.hover_states['settings'] = self.get_settings_button_rect().contains(mouse_pos)
        self.hover_states['start'] = self.get_start_button_rect().contains(mouse_pos)
        self.hover_states['stop'] = self.get_stop_button_rect().contains(mouse_pos)
        self.hover_states['reset'] = self.get_reset_button_rect().contains(mouse_pos)
    
    def is_any_button_hovered(self):
        """Prüft ob ein Button gehovered wird"""
        return any(self.hover_states.values())
    
    def reset_hover_states(self):
        """Setzt alle Hover-Zustände zurück"""
        for key in self.hover_states:
            self.hover_states[key] = False
    
    def handle_click(self, pos):
        """Behandelt Button-Klicks basierend auf Position"""
        if self.get_close_button_rect().contains(pos):
            self.close_clicked.emit()
            print("Close button clicked!")
            return True
        elif self.get_minimize_button_rect().contains(pos):
            self.minimize_clicked.emit()
            return True
        elif self.get_settings_button_rect().contains(pos):
            self.settings_clicked.emit()
            return True
        elif self.get_start_button_rect().contains(pos):
            self.start_clicked.emit()
            return True
        elif self.get_stop_button_rect().contains(pos):
            self.stop_clicked.emit()
            return True
        elif self.get_reset_button_rect().contains(pos):
            self.reset_clicked.emit()
            return True
        
        return False
    
    def draw_close_button(self, painter):
        """Zeichnet den Schließen-Button"""
        rect = self.get_close_button_rect()
        
        # Background
        bg_color = Styles.CLOSE_BUTTON_HOVER if self.hover_states['close'] else Styles.CLOSE_BUTTON_NORMAL
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Styles.BORDER_COLOR, 1))
        painter.drawRoundedRect(rect, 4, 4)
        
        # X Symbol
        painter.setPen(QPen(QColor(255, 255, 255, 220), 2, Qt.SolidLine, Qt.RoundCap))
        center = rect.center()
        offset = 4
        painter.drawLine(center.x() - offset, center.y() - offset, center.x() + offset, center.y() + offset)
        painter.drawLine(center.x() + offset, center.y() - offset, center.x() - offset, center.y() + offset)
    
    def draw_minimize_button(self, painter):
        """Zeichnet den Minimieren-Button"""
        rect = self.get_minimize_button_rect()
        
        # Background
        bg_color = Styles.MINIMIZE_BUTTON_HOVER if self.hover_states['minimize'] else Styles.MINIMIZE_BUTTON_NORMAL
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Styles.BORDER_COLOR, 1))
        painter.drawRoundedRect(rect, 4, 4)
        
        # Minimize Symbol
        painter.setPen(QPen(QColor(255, 255, 255, 220), 2, Qt.SolidLine, Qt.RoundCap))
        center = rect.center()
        painter.drawLine(center.x() - 5, center.y(), center.x() + 5, center.y())
    
    def draw_settings_button(self, painter):
        """Zeichnet den Einstellungen-Button"""
        rect = self.get_settings_button_rect()
        self._draw_icon_button(painter, rect, "⚙", self.hover_states['settings'], Styles.BUTTON_SETTINGS)
    
    def draw_main_button(self, painter, button_type):
        """Zeichnet einen Haupt-Button"""
        button_config = {
            'start': (self.get_start_button_rect(), "Check Ready", self.hover_states['start'], Styles.BUTTON_START),
            'stop': (self.get_stop_button_rect(), "Profile Select", self.hover_states['stop'], Styles.BUTTON_STOP),
            'reset': (self.get_reset_button_rect(), "Draw Green Box", self.hover_states['reset'], Styles.BUTTON_RESET)
        }
        
        if button_type in button_config:
            rect, text, is_hover, base_color = button_config[button_type]
            self._draw_solid_button(painter, rect, text, is_hover, base_color)
    
    def _draw_icon_button(self, painter, rect, icon, is_hover, base_color):
        """Zeichnet einen Icon-Button"""
        bg_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 200) if is_hover else Styles.CLOSE_BUTTON_NORMAL
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(Styles.BORDER_COLOR, 1))
        painter.drawRoundedRect(rect, 4, 4)
        
        # Icon
        painter.setPen(QPen(QColor(255, 255, 255, 220), 1))
        painter.setFont(Styles.ICON_FONT)
        painter.drawText(rect, Qt.AlignCenter, icon)
    
    def _draw_solid_button(self, painter, rect, text, is_hover, base_color):
        """Zeichnet einen soliden Button"""
        if is_hover:
            bg_color = QColor(
                min(255, base_color.red() + 30), 
                min(255, base_color.green() + 30), 
                min(255, base_color.blue() + 30), 
                255
            )
        else:
            bg_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 255)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.drawRoundedRect(rect, 8, 8)
        
        # Text
        painter.setPen(QPen(Styles.TEXT_COLOR_BRIGHT, 1))
        painter.setFont(Styles.BUTTON_FONT)
        painter.drawText(rect, Qt.AlignCenter, text)
        
        # Shadow-Effekt
        if not is_hover:
            shadow_rect = QRect(rect.x() + 1, rect.y() + 1, rect.width(), rect.height())
            painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(shadow_rect, 8, 8)