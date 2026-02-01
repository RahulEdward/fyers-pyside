"""Registration window for new user signup"""
import re
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, MAIN_STYLESHEET
from src.ui.utils import ErrorLabel, LoadingOverlay


class RegisterWindow(QMainWindow):
    """Registration window for new user signup"""
    
    # Signals
    registration_successful = Signal(object)  # Emits user object on success
    login_requested = Signal()                 # Emits when user wants to login
    
    def __init__(self, auth_service=None):
        super().__init__()
        self.auth_service = auth_service
        self.setup_ui()
        self.setStyleSheet(MAIN_STYLESHEET)
    
    def setup_ui(self):
        self.setWindowTitle("Fyers Trading - Register")
        self.setFixedSize(400, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        layout.setSpacing(SPACING['md'])
        
        # Title
        title = QLabel("Fyers Trading")
        title.setProperty("type", "header")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(LABELS['register'])
        subtitle.setProperty("type", "title")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle)
        
        layout.addSpacing(SPACING['md'])
        
        # Form container
        form = QFrame()
        form.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: {SPACING['md']}px;
            }}
        """)
        form_layout = QVBoxLayout(form)
        form_layout.setSpacing(SPACING['sm'])
        
        # Username field
        username_label = QLabel(LABELS['username'])
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        form_layout.addWidget(self.username_input)
        
        self.username_error = ErrorLabel()
        form_layout.addWidget(self.username_error)
        
        # Email field
        email_label = QLabel(LABELS['email'])
        form_layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        form_layout.addWidget(self.email_input)
        
        self.email_error = ErrorLabel()
        form_layout.addWidget(self.email_error)
        
        # Password field
        password_label = QLabel(LABELS['password'])
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_input)
        
        self.password_error = ErrorLabel()
        form_layout.addWidget(self.password_error)
        
        # Confirm password field
        confirm_label = QLabel(LABELS['confirm_password'])
        form_layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm your password")
        self.confirm_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.returnPressed.connect(self._on_register_clicked)
        form_layout.addWidget(self.confirm_input)
        
        self.confirm_error = ErrorLabel()
        form_layout.addWidget(self.confirm_error)
        
        # General error label
        self.error_label = ErrorLabel()
        form_layout.addWidget(self.error_label)
        
        form_layout.addSpacing(SPACING['sm'])
        
        # Register button
        self.register_btn = QPushButton(LABELS['register'])
        self.register_btn.clicked.connect(self._on_register_clicked)
        self.register_btn.setCursor(Qt.PointingHandCursor)
        form_layout.addWidget(self.register_btn)
        
        layout.addWidget(form)
        
        # Login link
        login_layout = QHBoxLayout()
        login_layout.setAlignment(Qt.AlignCenter)
        
        login_text = QLabel("Already have an account?")
        login_text.setStyleSheet(f"color: {COLORS['text_secondary']};")
        login_layout.addWidget(login_text)
        
        self.login_link = QPushButton(LABELS['login'])
        self.login_link.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['primary']};
                border: none;
                text-decoration: underline;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {COLORS['primary_dark']};
            }}
        """)
        self.login_link.setCursor(Qt.PointingHandCursor)
        self.login_link.clicked.connect(self._on_login_clicked)
        login_layout.addWidget(self.login_link)
        
        layout.addLayout(login_layout)
        
        layout.addStretch()
        
        # Loading overlay
        self.loading = LoadingOverlay(central)
    
    def _clear_errors(self):
        """Clear all error labels"""
        self.username_error.clear_error()
        self.email_error.clear_error()
        self.password_error.clear_error()
        self.confirm_error.clear_error()
        self.error_label.clear_error()
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _on_register_clicked(self):
        """Handle register button click"""
        self._clear_errors()
        
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        # Validate inputs
        has_error = False
        
        if not username:
            self.username_error.show_error("Username is required")
            has_error = True
        elif len(username) < 3:
            self.username_error.show_error("Username must be at least 3 characters")
            has_error = True
        
        if not email:
            self.email_error.show_error("Email is required")
            has_error = True
        elif not self._validate_email(email):
            self.email_error.show_error("Invalid email format")
            has_error = True
        
        if not password:
            self.password_error.show_error("Password is required")
            has_error = True
        elif len(password) < 6:
            self.password_error.show_error("Password must be at least 6 characters")
            has_error = True
        
        if not confirm:
            self.confirm_error.show_error("Please confirm your password")
            has_error = True
        elif password != confirm:
            self.confirm_error.show_error("Passwords do not match")
            has_error = True
        
        if has_error:
            return
        
        # Attempt registration
        if self.auth_service:
            self.loading.show_loading("Creating account...")
            self.register_btn.setEnabled(False)
            
            try:
                from src.models.result import Ok, Err
                result = self.auth_service.register(username, password, email)
                
                if isinstance(result, Ok):
                    self.registration_successful.emit(result.value)
                else:
                    self.error_label.show_error(result.error)
            except Exception as e:
                self.error_label.show_error(f"Registration failed: {str(e)}")
            finally:
                self.loading.hide_loading()
                self.register_btn.setEnabled(True)
        else:
            # No auth service - emit signal for testing
            self.registration_successful.emit({"username": username, "email": email})
    
    def _on_login_clicked(self):
        """Handle login link click"""
        self.login_requested.emit()
    
    def clear_form(self):
        """Clear all form fields"""
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
        self._clear_errors()
    
    def set_auth_service(self, auth_service):
        """Set the authentication service"""
        self.auth_service = auth_service
