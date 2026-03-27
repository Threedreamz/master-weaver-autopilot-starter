"""
Haupt-Fenster der Anwendung – mit Expand-Button & Checkboxes unten
"""
from PySide6.QtWidgets import QWidget, QPushButton, QCheckBox
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPainter
from BlurWindow.blurWindow import blur

from gui.config import Config, Styles
from gui.ui.btn_management import ButtonManager
from gui.ui.status import StatusManager
from gui.ui.window_behavior import WindowBehavior
from gui.handlers.event_handler import EventHandlers
from PySide6.QtGui import QRegion, QPainterPath

class MainWindow(QWidget):
    """Hauptfenster der Anwendung mit expand/collapse Button unten + Checkboxes"""
    
    def __init__(self):
        super().__init__()
        
        self.expanded = False
        self.animation = None
        self.default_height = Config.WINDOW_HEIGHT
        self.expanded_height = Config.WINDOW_HEIGHT + 180
        
        self._setup_window()
        self._initialize_managers()
        self._connect_signals()
        self._create_expand_button()
        self._create_expand_content()
        self._start_functionality()
    

    def _setup_window(self):
        self.setWindowFlags(Config.WINDOW_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)

        self.container = QWidget(self)
        self.container.setObjectName("Container")
        self.container.resize(self.size())
        self.container.setStyleSheet(Styles.CONTAINER_STYLE)

        # Enable real blur on window
        blur(self.winId())

        # Apply initial round mask to clip the blur visually
        self._apply_rounded_mask()

    def _apply_rounded_mask(self):
        """Setzt eine runde Maske, damit der Blur nicht über die Ecken hinaus 'bleedet'."""
        radius = 11  # 20 default Passe das an deinen Styles.CONTAINER_STYLE border-radius an
        path = QPainterPath()
        path.addRoundedRect(self.rect(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
    def _create_expand_button(self):
        """Fügt den Expand-/Collapse-Button unten hinzu"""
        self.expand_btn = QPushButton("▾", self)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(255,255,255,0.6);
                font-size: 14px;
            }
            QPushButton:hover {
                color: rgba(255,255,255,0.9);
            }
            QPushButton:pressed {
                color: rgba(0,180,255,0.9);
            }
        """)
        # Slightly larger width for better click area
        self.expand_btn.setFixedSize(48, 24)
        self._reposition_expand_button()
        self.expand_btn.clicked.connect(self._toggle_expand)
    
    def _create_expand_content(self):
        """Erstellt Checkboxes für den erweiterten Bereich"""
        self.checkbox_topmost = QCheckBox("TopMost", self)
        self.checkbox_autohide = QCheckBox("AutoHide", self)

        checkbox_style = """
        QCheckBox {
            color: rgba(255,255,255,0.85);
            font-size: 18px;
            spacing: 6px;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 3px;
            border: 1px solid rgba(255,255,255,0.25);
            background-color: rgba(255,255,255,0.05);
        }
        QCheckBox::indicator:checked {
            background-color: rgba(0,180,255,0.6);
            border: 1px solid rgba(0,180,255,0.9);
        }
        """
        self.checkbox_topmost.setStyleSheet(checkbox_style)
        self.checkbox_autohide.setStyleSheet(checkbox_style)

        # Adjusted positioning — centered horizontally, evenly spaced vertically
        box_width = 400
        spacing_y = 30
        base_y = self.default_height + 40
        center_x = (self.width() - box_width) // 2

        self.checkbox_topmost.setGeometry(center_x, base_y, box_width, 20)
        self.checkbox_autohide.setGeometry(center_x, base_y + spacing_y, box_width, 20)

        self.checkbox_topmost.hide()
        self.checkbox_autohide.hide()

        self.checkbox_topmost.stateChanged.connect(self._handle_topmost_toggle)

    def _handle_topmost_toggle(self, state):
        pass
        
    def _reposition_expand_button(self):
        """Platziert den Button immer unten mittig"""
        btn_width = self.expand_btn.width()
        btn_x = (self.width() - btn_width) // 2
        btn_y = self.height() - self.expand_btn.height() - 6
        self.expand_btn.setGeometry(btn_x, btn_y, btn_width, self.expand_btn.height())

    def _toggle_expand(self):
        """Fährt die Form ein oder aus (Animation)"""
        if self.animation and self.animation.state() == QPropertyAnimation.Running:
            return
  
        start_h = self.height()
        end_h = self.expanded_height if not self.expanded else self.default_height
        
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(350)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        rect = self.geometry()
        self.animation.setStartValue(QRect(rect.x(), rect.y(), rect.width(), start_h))
        self.animation.setEndValue(QRect(rect.x(), rect.y(), rect.width(), end_h))
        self.animation.start()
        self.animation.finished.connect(lambda: self.container.resize(self.size()))

        
        if not self.expanded:
            self.checkbox_topmost.show()
            self.checkbox_autohide.show()
            self.expand_btn.setText("▲")
        else:
            self.checkbox_topmost.hide()
            self.checkbox_autohide.hide()
            self.expand_btn.setText("▾")

        self.expanded = not self.expanded
    
    def _initialize_managers(self):
        self.button_manager = ButtonManager(self)
        self.status_manager = StatusManager(self)
        self.window_behavior = WindowBehavior(self)
        self.event_handlers = EventHandlers(self)
    
    def _connect_signals(self):
        bm = self.button_manager
        eh = self.event_handlers

        bm.close_clicked.connect(eh.handle_close_button)
        bm.minimize_clicked.connect(eh.handle_minimize_button)
        bm.settings_clicked.connect(eh.handle_settings_button)
        bm.start_clicked.connect(eh.handle_start_button)
        bm.stop_clicked.connect(eh.handle_stop_button)
        bm.reset_clicked.connect(eh.handle_reset_button)

        eh.status_update_requested.connect(self._handle_status_update)
    
    def _start_functionality(self):
        self.window_behavior.initialize()
        self.status_manager.start_demo_mode()
    
    def _handle_status_update(self, message):
        print(f"Status-Update: {message}")
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'container'):
            self.container.resize(self.size())
            self._apply_rounded_mask()  # <--- hier wird die Maske beim Expand aktualisiert
        if hasattr(self, 'expand_btn'):
            self._reposition_expand_button()
        if hasattr(self, 'checkbox_topmost') and self.expanded:
            # Recenter checkboxes if resized
            box_width = 140
            spacing_y = 30
            base_y = self.default_height + 40
            center_x = (self.width() - box_width) // 2
            self.checkbox_topmost.setGeometry(center_x, base_y, box_width, 20)
            self.checkbox_autohide.setGeometry(center_x, base_y + spacing_y, box_width, 20)
        super().resizeEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if hasattr(self, 'status_manager'):
            self.status_manager.draw_pi_status(painter)
        if hasattr(self, 'button_manager'):
            self.button_manager.draw_close_button(painter)
            self.button_manager.draw_minimize_button(painter)
            self.button_manager.draw_settings_button(painter)
            self.button_manager.draw_main_button(painter, 'start')
            self.button_manager.draw_main_button(painter, 'stop')
            self.button_manager.draw_main_button(painter, 'reset')
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if hasattr(self, 'button_manager'):
                if self.button_manager.handle_click(event.pos()):
                    return
            if hasattr(self, 'window_behavior'):
                self.window_behavior.start_drag(event.globalPosition().toPoint())
            event.accept()
    
    def mouseMoveEvent(self, event):
        if hasattr(self, 'button_manager'):
            self.button_manager.update_hover_states(event.pos())
            self.setCursor(Qt.PointingHandCursor if self.button_manager.is_any_button_hovered() else Qt.ArrowCursor)
        if event.buttons() == Qt.LeftButton and hasattr(self, 'window_behavior'):
            self.window_behavior.handle_drag(event.globalPosition().toPoint())
        self.update()
        event.accept()
    
    def mouseReleaseEvent(self, event):
        if hasattr(self, 'window_behavior'):
            self.window_behavior.stop_drag()
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        if hasattr(self, 'window_behavior'):
            self.window_behavior.on_mouse_enter()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if hasattr(self, 'button_manager'):
            self.button_manager.reset_hover_states()
            self.setCursor(Qt.ArrowCursor)
        if hasattr(self, 'window_behavior'):
            self.window_behavior.on_mouse_leave()
        self.update()
        super().leaveEvent(event)
    
    def closeEvent(self, event):
        if hasattr(self, 'window_behavior'):
            self.window_behavior.stop_monitoring()
        if hasattr(self, 'status_manager'):
            self.status_manager.stop_demo_mode()
        super().closeEvent(event)
