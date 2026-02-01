"""UI utility functions and helper widgets"""
from typing import Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QMovie

from src.ui.styles import COLORS, LABELS, SPACING


class LoadingIndicator(QWidget):
    """Loading indicator widget with spinner and optional message"""
    
    def __init__(self, message: str = None, parent: QWidget = None):
        super().__init__(parent)
        self.setup_ui(message or LABELS['loading'])
    
    def setup_ui(self, message: str):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        # Progress bar (indeterminate)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # Indeterminate mode
        self.progress.setFixedWidth(200)
        layout.addWidget(self.progress, alignment=Qt.AlignCenter)
        
        # Message label
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(self.label)
    
    def set_message(self, message: str):
        """Update the loading message"""
        self.label.setText(message)


class LoadingOverlay(QWidget):
    """Semi-transparent loading overlay for widgets"""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setup_ui()
        self.hide()
    
    def setup_ui(self):
        self.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 0.8);
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.indicator = LoadingIndicator()
        layout.addWidget(self.indicator)
    
    def show_loading(self, message: str = None):
        """Show the loading overlay"""
        if message:
            self.indicator.set_message(message)
        self.raise_()
        self.show()
    
    def hide_loading(self):
        """Hide the loading overlay"""
        self.hide()
    
    def resizeEvent(self, event):
        """Resize overlay to match parent"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)


class ErrorLabel(QLabel):
    """Label for displaying error messages"""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setProperty("type", "error")
        self.setWordWrap(True)
        self.hide()
    
    def show_error(self, message: str):
        """Show error message"""
        self.setText(message)
        self.show()
    
    def clear_error(self):
        """Clear and hide error message"""
        self.setText("")
        self.hide()


class SuccessLabel(QLabel):
    """Label for displaying success messages"""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setProperty("type", "success")
        self.setWordWrap(True)
        self.hide()
    
    def show_success(self, message: str, auto_hide: int = 3000):
        """Show success message with optional auto-hide"""
        self.setText(message)
        self.show()
        
        if auto_hide > 0:
            QTimer.singleShot(auto_hide, self.hide)
    
    def clear_message(self):
        """Clear and hide message"""
        self.setText("")
        self.hide()


class StatusIndicator(QFrame):
    """Connection status indicator widget"""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setup_ui()
        self.set_disconnected()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING['sm'], SPACING['xs'], SPACING['sm'], SPACING['xs'])
        layout.setSpacing(SPACING['sm'])
        
        # Status dot
        self.dot = QLabel("●")
        self.dot.setFixedWidth(16)
        layout.addWidget(self.dot)
        
        # Status text
        self.text = QLabel()
        layout.addWidget(self.text)
    
    def set_connected(self, message: str = None):
        """Set connected status"""
        self.dot.setStyleSheet(f"color: {COLORS['success']};")
        self.text.setText(message or LABELS['connected'])
        self.text.setStyleSheet(f"color: {COLORS['success']};")
    
    def set_disconnected(self, message: str = None):
        """Set disconnected status"""
        self.dot.setStyleSheet(f"color: {COLORS['error']};")
        self.text.setText(message or LABELS['disconnected'])
        self.text.setStyleSheet(f"color: {COLORS['error']};")
    
    def set_connecting(self, message: str = None):
        """Set connecting status"""
        self.dot.setStyleSheet(f"color: {COLORS['warning']};")
        self.text.setText(message or "Connecting...")
        self.text.setStyleSheet(f"color: {COLORS['warning']};")


def show_error_dialog(parent: QWidget, title: str, message: str):
    """Show error dialog"""
    QMessageBox.critical(parent, title, message)


def show_warning_dialog(parent: QWidget, title: str, message: str):
    """Show warning dialog"""
    QMessageBox.warning(parent, title, message)


def show_info_dialog(parent: QWidget, title: str, message: str):
    """Show info dialog"""
    QMessageBox.information(parent, title, message)


def show_confirm_dialog(parent: QWidget, title: str, message: str) -> bool:
    """Show confirmation dialog, returns True if confirmed"""
    result = QMessageBox.question(
        parent, title, message,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )
    return result == QMessageBox.Yes


def format_currency(value: float, symbol: str = "₹") -> str:
    """Format value as currency"""
    if value >= 0:
        return f"{symbol}{value:,.2f}"
    return f"-{symbol}{abs(value):,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.2f}%"


def format_quantity(value: int) -> str:
    """Format quantity with commas"""
    return f"{value:,}"


def create_horizontal_line() -> QFrame:
    """Create a horizontal separator line"""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {COLORS['border']};")
    return line


def create_vertical_line() -> QFrame:
    """Create a vertical separator line"""
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {COLORS['border']};")
    return line


class DelayedCallback:
    """Helper class for delayed/debounced callbacks"""
    
    def __init__(self, callback: Callable, delay_ms: int = 300):
        self.callback = callback
        self.delay_ms = delay_ms
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._execute)
        self._args = ()
        self._kwargs = {}
    
    def call(self, *args, **kwargs):
        """Schedule the callback with debouncing"""
        self._args = args
        self._kwargs = kwargs
        self.timer.stop()
        self.timer.start(self.delay_ms)
    
    def _execute(self):
        """Execute the callback"""
        self.callback(*self._args, **self._kwargs)
    
    def cancel(self):
        """Cancel pending callback"""
        self.timer.stop()
