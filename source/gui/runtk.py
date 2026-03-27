import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from BlurWindow.blurWindow import blur

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
       
        # Frameless window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(300, 80)
       
        # Create container widget for styling
        self.container = QWidget(self)
        self.container.setObjectName("Container")
        self.container.resize(self.size())
        
        # Style the container with rounded corners and background
        self.container.setStyleSheet("""
            #Container {
                background: rgba(255, 255, 255, 50);
                border: 3px solid rgba(255, 255, 255, 10);
                border-radius: 25px;
            }
        """)
       
        # Positioniere das Fenster immer oben im Bildschirm (initial versteckt)
        screen = QApplication.primaryScreen().geometry()
        self.screen_width = screen.width()
        self.screen_height = screen.height()
        self.x_pos = (self.screen_width - self.width()) // 2
        self.move(self.x_pos, -self.height() + 5)  # Versteckt am oberen Rand
       
        # Blur effect
        blur(self.winId())
       
        # Variables für das Verschieben des Fensters
        self.drag_position = QPoint()
        
        # Auto-hide/show functionality
        self.is_hidden = True
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.check_mouse_position)
        self.mouse_timer.start(50)  # Check every 50ms
        
        # Hide timer (delay before hiding)
        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide_window)
        
        # Button properties
        self.button_size = 20
        self.button_margin = 10
        
    def resizeEvent(self, event):
        # Keep container same size as main window
        if hasattr(self, 'container'):
            self.container.resize(self.size())
        super().resizeEvent(event)
        
    def paintEvent(self, event):
        # Custom paint event für Buttons (container handles the rounded background)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Close button (X)
        close_rect = self.get_close_button_rect()
        painter.setBrush(QBrush(QColor(255, 100, 100, 150)))
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
        painter.drawEllipse(close_rect)
        
        # X symbol
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        margin = 5
        painter.drawLine(close_rect.left() + margin, close_rect.top() + margin,
                        close_rect.right() - margin, close_rect.bottom() - margin)
        painter.drawLine(close_rect.right() - margin, close_rect.top() + margin,
                        close_rect.left() + margin, close_rect.bottom() - margin)
        
        # Minimize button (-)
        minimize_rect = self.get_minimize_button_rect()
        painter.setBrush(QBrush(QColor(255, 200, 100, 150)))
        painter.setPen(QPen(QColor(255, 255, 255, 200), 2))
        painter.drawEllipse(minimize_rect)
        
        # - symbol
        painter.setPen(QPen(QColor(255, 255, 255), 3))
        y_center = minimize_rect.center().y()
        painter.drawLine(minimize_rect.left() + margin, y_center,
                        minimize_rect.right() - margin, y_center)
    
    def get_close_button_rect(self):
        return QRect(self.width() - self.button_size - self.button_margin,
                    self.button_margin, self.button_size, self.button_size)
    
    def get_minimize_button_rect(self):
        return QRect(self.width() - 2 * self.button_size - 2 * self.button_margin,
                    self.button_margin, self.button_size, self.button_size)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Check if clicked on close button
            if self.get_close_button_rect().contains(event.pos()):
                self.close()
                return
            
            # Check if clicked on minimize button
            if self.get_minimize_button_rect().contains(event.pos()):
                self.showMinimized()
                return
            
            # Normal window dragging
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
           
    def mouseMoveEvent(self, event):
        # Fenster verschieben
        if event.buttons() == Qt.LeftButton and not self.drag_position.isNull():
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def enterEvent(self, event):
        # Stop hide timer when mouse enters window
        self.hide_timer.stop()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        # Start hide timer when mouse leaves window
        self.hide_timer.start(1000)  # Hide after 1 second
        super().leaveEvent(event)
    
    def check_mouse_position(self):
        # Get current mouse position
        cursor_pos = QCursor.pos()
        
        # Check if mouse is at the top of the screen (within 5 pixels)
        if cursor_pos.y() <= 5:
            if self.is_hidden:
                self.show_window()
        else:
            # If mouse is not at top and window is not being hovered
            if not self.is_hidden and not self.geometry().contains(cursor_pos):
                # Start hide timer if not already started
                if not self.hide_timer.isActive():
                    self.hide_timer.start(500)  # Hide after 500ms
    
    def show_window(self):
        if self.is_hidden:
            # Animate window sliding down
            self.animation = QPropertyAnimation(self, b"pos")
            self.animation.setDuration(200)
            self.animation.setStartValue(QPoint(self.x_pos, -self.height() + 5))
            self.animation.setEndValue(QPoint(self.x_pos, 0))
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.start()
            self.is_hidden = False
            self.hide_timer.stop()
    
    def hide_window(self):
        if not self.is_hidden:
            # Check if mouse is still not at top of screen
            cursor_pos = QCursor.pos()
            if cursor_pos.y() > 5 and not self.geometry().contains(cursor_pos):
                # Animate window sliding up
                self.animation = QPropertyAnimation(self, b"pos")
                self.animation.setDuration(200)
                self.animation.setStartValue(QPoint(self.x_pos, 0))
                self.animation.setEndValue(QPoint(self.x_pos, -self.height() + 5))
                self.animation.setEasingCurve(QEasingCurve.InCubic)
                self.animation.start()
                self.is_hidden = True

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())