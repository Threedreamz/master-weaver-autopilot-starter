"""
Window-Behavior Manager für Auto-Hide/Show Funktionalität
"""
from PySide6.QtCore import QObject, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QApplication
from gui.config import Config

class WindowBehavior(QObject):
    """Verwaltet das Verhalten des Fensters (Auto-Hide/Show, Animationen)"""
    
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.window = parent_window
        
        # Window position and state
        self.is_hidden = True
        self.x_pos = 0
        self.drag_position = QPoint()
        
        # Timers
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_window)
        
        # Animation
        self.animation = None
        
        # Screen dimensions
        self._update_screen_dimensions()
        
    def initialize(self):
        """Initialisiert das Fenster-Verhalten"""
        self._position_window_initially()
        self._start_mouse_monitoring()
        
    def _update_screen_dimensions(self):
        """Aktualisiert die Bildschirm-Dimensionen"""
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.x_pos = (self.screen_width - self.window.width()) // 2
        
    def _position_window_initially(self):
        """Positioniert das Fenster initial (versteckt)"""
        self.window.move(self.x_pos, -self.window.height() + Config.WINDOW_HIDE_OFFSET)
        
    def _start_mouse_monitoring(self):
        """Startet das Mouse-Monitoring"""
        self.mouse_timer.start(Config.MOUSE_CHECK_INTERVAL)
        
    def stop_monitoring(self):
        """Stoppt das Mouse-Monitoring"""
        self.mouse_timer.stop()
        self.hide_timer.stop()
        
    def check_mouse_position(self):
        """Prüft die Mausposition für Auto-Show/Hide"""
        cursor_pos = QCursor.pos()
        
        # Maus am oberen Bildschirmrand?
        if cursor_pos.y() <= Config.TOP_TRIGGER_ZONE:
            if self.is_hidden:
                self.show_window()
        else:
            # Maus nicht am oberen Rand und Fenster wird nicht gehovered
            if not self.is_hidden and not self.window.geometry().contains(cursor_pos):
                if not self.hide_timer.isActive():
                    self.hide_timer.start(Config.QUICK_HIDE_DELAY)
    
    def show_window(self):
        """Zeigt das Fenster mit Animation"""
        if self.is_hidden and self.window.isVisible():
            self._create_show_animation()
            self.is_hidden = False
            self.hide_timer.stop()
    
    def hide_window(self):
        """Versteckt das Fenster mit Animation"""
        if not self.is_hidden:
            cursor_pos = QCursor.pos()
            if cursor_pos.y() > Config.TOP_TRIGGER_ZONE and not self.window.geometry().contains(cursor_pos):
                self._create_hide_animation()
                self.is_hidden = True
    
    def _create_show_animation(self):
        """Erstellt Animation zum Zeigen des Fensters"""
        if self.animation:
            self.animation.stop()
            
        self.animation = QPropertyAnimation(self.window, b"pos")
        self.animation.setDuration(Config.ANIMATION_DURATION)
        self.animation.setStartValue(QPoint(self.x_pos, -self.window.height() + Config.WINDOW_HIDE_OFFSET))
        self.animation.setEndValue(QPoint(self.x_pos, 0))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
    
    def _create_hide_animation(self):
        """Erstellt Animation zum Verstecken des Fensters"""
        if self.animation:
            self.animation.stop()
            
    

        self.animation = QPropertyAnimation(self.window, b"pos")
        self.animation.setDuration(Config.ANIMATION_DURATION)
        self.animation.setStartValue(QPoint(self.x_pos, 0))
        self.animation.setEndValue(QPoint(self.x_pos, -self.window.height() + Config.WINDOW_HIDE_OFFSET))
        self.animation.setEasingCurve(QEasingCurve.InCubic)
        self.animation.start()
    
    def start_drag(self, global_pos):
        """Startet das Fenster-Verschieben"""
        self.drag_position = global_pos - self.window.frameGeometry().topLeft()
    
    def handle_drag(self, global_pos):
        """Behandelt das Fenster-Verschieben"""
        if not self.drag_position.isNull():
            new_pos = global_pos - self.drag_position
            self.window.move(new_pos)
            # Update x_pos für zukünftige Animationen
            #self.x_pos = new_pos.x()
    
    def stop_drag(self):
        """Stoppt das Fenster-Verschieben"""
        self.drag_position = QPoint()
    
    def on_mouse_enter(self):
        """Wird aufgerufen wenn die Maus das Fenster betritt"""
        self.hide_timer.stop()
    
    def on_mouse_leave(self):
        """Wird aufgerufen wenn die Maus das Fenster verlässt"""
        if not self.is_hidden:
            self.hide_timer.start(Config.HIDE_DELAY)
    
    def force_show(self):
        """Zeigt das Fenster sofort ohne Animation"""
        self.window.move(self.x_pos, 0)
        self.is_hidden = False
        
    def force_hide(self):
        """Versteckt das Fenster sofort ohne Animation"""
        self.window.move(self.x_pos, -self.window.height() + Config.WINDOW_HIDE_OFFSET)
        self.is_hidden = True