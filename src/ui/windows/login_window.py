"""Login window for broker authentication - Fyers OAuth flow"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer

from src.ui.styles import COLORS
from src.ui.utils import ErrorLabel, LoadingOverlay


class OAuthWorker(QThread):
    """Worker thread for OAuth authentication"""
    success = Signal(str)
    error = Signal(str)
    
    def __init__(self, api_key: str, api_secret: str):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
    
    def run(self):
        try:
            from src.services.fyers_oauth_service import FyersOAuthService
            oauth = FyersOAuthService(self.api_key, self.api_secret)
            access_token = oauth.authenticate()
            if access_token:
                self.success.emit(access_token)
            else:
                self.error.emit("Authentication failed or timed out")
        except Exception as e:
            self.error.emit(str(e))


class LoginWindow(QMainWindow):
    """Login window for Fyers broker authentication with OAuth"""
    
    login_successful = Signal(object)
    
    def __init__(self, broker_service=None, encryption_service=None):
        super().__init__()
        self.broker_service = broker_service
        self.encryption_service = encryption_service
        self.oauth_worker = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Fyers Trading - Login")
        self.setFixedSize(500, 780)
        self.setStyleSheet(f"background-color: {COLORS['background']};")
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(5)
        
        # Logo
        title = QLabel("🚀 Fyers Trading")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {COLORS['primary']};")
        main_layout.addWidget(title)
        
        subtitle = QLabel("Connect your Fyers account to start trading")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 14px; color: {COLORS['text_secondary']}; margin-bottom: 15px;")
        main_layout.addWidget(subtitle)
        
        # Form Card
        form_card = QFrame()
        form_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(5)
        
        # ========== Field 1: Client ID ==========
        lbl1 = QLabel("Fyers Client ID")
        lbl1.setStyleSheet(self._label_style())
        form_layout.addWidget(lbl1)
        
        self.client_id_input = QLineEdit()
        self.client_id_input.setPlaceholderText("e.g., XY12345")
        self.client_id_input.setStyleSheet(self._input_style())
        self.client_id_input.setMinimumHeight(45)
        form_layout.addWidget(self.client_id_input)
        
        form_layout.addSpacing(10)
        
        # ========== Field 2: API Key ==========
        lbl2 = QLabel("API Key (App ID)")
        lbl2.setStyleSheet(self._label_style())
        form_layout.addWidget(lbl2)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("e.g., XXXXXXXX-100")
        self.api_key_input.setStyleSheet(self._input_style())
        self.api_key_input.setMinimumHeight(45)
        form_layout.addWidget(self.api_key_input)
        
        form_layout.addSpacing(10)
        
        # ========== Field 3: API Secret ==========
        lbl3 = QLabel("API Secret")
        lbl3.setStyleSheet(self._label_style())
        form_layout.addWidget(lbl3)
        
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("Enter your API Secret Key")
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        self.api_secret_input.setStyleSheet(self._input_style())
        self.api_secret_input.setMinimumHeight(45)
        form_layout.addWidget(self.api_secret_input)
        
        # Show secret checkbox
        self.show_secret_cb = QCheckBox("Show API Secret")
        self.show_secret_cb.setStyleSheet(self._checkbox_style())
        self.show_secret_cb.toggled.connect(self._toggle_secret_visibility)
        form_layout.addWidget(self.show_secret_cb)
        
        form_layout.addSpacing(5)
        
        # Remember credentials
        self.remember_cb = QCheckBox("Remember credentials")
        self.remember_cb.setStyleSheet(self._checkbox_style())
        self.remember_cb.setChecked(True)
        form_layout.addWidget(self.remember_cb)
        
        # Error label
        self.error_label = ErrorLabel()
        form_layout.addWidget(self.error_label)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        form_layout.addWidget(self.status_label)
        
        form_layout.addSpacing(10)
        
        # Login button
        self.login_btn = QPushButton("🔐  Connect with Fyers")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: #000000;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {COLORS['surface_light']};
                color: {COLORS['text_disabled']};
            }}
        """)
        self.login_btn.clicked.connect(self._on_login_clicked)
        form_layout.addWidget(self.login_btn)
        
        main_layout.addWidget(form_card)
        
        # Info section
        main_layout.addSpacing(10)
        
        info_box = QFrame()
        info_box.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
        """)
        info_layout = QVBoxLayout(info_box)
        info_layout.setContentsMargins(15, 12, 15, 12)
        info_layout.setSpacing(6)
        
        info_title = QLabel("📋 How to get API credentials:")
        info_title.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 600; font-size: 13px;")
        info_layout.addWidget(info_title)
        
        steps = [
            "1. Go to myapi.fyers.in/dashboard",
            "2. Create app with redirect URL:",
            "   http://127.0.0.1:8765/callback",
            "3. Copy App ID and Secret Key",
            "4. Click Connect - browser will open automatically"
        ]
        
        for step in steps:
            step_lbl = QLabel(step)
            step_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; margin-left: 8px;")
            info_layout.addWidget(step_lbl)
        
        main_layout.addWidget(info_box)
        main_layout.addStretch()
        
        # Loading overlay
        self.loading = LoadingOverlay(central)
    
    def _label_style(self) -> str:
        return f"""
            QLabel {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding: 0px;
                margin: 0px;
            }}
        """
    
    def _input_style(self) -> str:
        return f"""
            QLineEdit {{
                background-color: {COLORS['background']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['primary']};
            }}
            QLineEdit::placeholder {{
                color: {COLORS['text_disabled']};
            }}
        """
    
    def _checkbox_style(self) -> str:
        return f"""
            QCheckBox {{
                color: {COLORS['text_secondary']};
                font-size: 12px;
                spacing: 8px;
                background: transparent;
                padding: 5px 0px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 2px solid {COLORS['border']};
                background-color: transparent;
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['primary']};
                border-color: {COLORS['primary']};
            }}
        """
    
    def _toggle_secret_visibility(self, checked: bool):
        if checked:
            self.api_secret_input.setEchoMode(QLineEdit.Normal)
        else:
            self.api_secret_input.setEchoMode(QLineEdit.Password)
    
    def _on_login_clicked(self):
        self.error_label.clear_error()
        
        client_id = self.client_id_input.text().strip().upper()
        api_key = self.api_key_input.text().strip()
        api_secret = self.api_secret_input.text().strip()
        
        if not client_id:
            self.error_label.show_error("Client ID is required")
            self.client_id_input.setFocus()
            return
        
        if not api_key:
            self.error_label.show_error("API Key is required")
            self.api_key_input.setFocus()
            return
        
        if not api_secret:
            self.error_label.show_error("API Secret is required")
            self.api_secret_input.setFocus()
            return
        
        # Save credentials
        if self.broker_service and self.remember_cb.isChecked():
            try:
                self.broker_service.save_broker_credentials(
                    broker_username=client_id,
                    api_key=api_key,
                    api_secret=api_secret
                )
            except:
                pass
        
        # Start OAuth
        self.login_btn.setEnabled(False)
        self.status_label.setText("Opening browser for Fyers login...")
        self.status_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: 12px;")
        
        self._pending_credentials = {
            'client_id': client_id,
            'api_key': api_key,
            'api_secret': api_secret
        }
        
        self.oauth_worker = OAuthWorker(api_key, api_secret)
        self.oauth_worker.success.connect(self._on_oauth_success)
        self.oauth_worker.error.connect(self._on_oauth_error)
        self.oauth_worker.start()
    
    def _on_oauth_success(self, access_token: str):
        self.login_btn.setEnabled(True)
        self.status_label.setText("✅ Connected successfully!")
        self.status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px;")
        
        credentials = {
            'broker_username': self._pending_credentials['client_id'],
            'api_key': self._pending_credentials['api_key'],
            'api_secret': self._pending_credentials['api_secret'],
            'access_token': access_token
        }
        
        QTimer.singleShot(500, lambda: self.login_successful.emit(credentials))
    
    def _on_oauth_error(self, error_msg: str):
        self.login_btn.setEnabled(True)
        self.status_label.setText("")
        self.error_label.show_error(f"Authentication failed: {error_msg}")
    
    def clear_form(self):
        self.client_id_input.clear()
        self.api_key_input.clear()
        self.api_secret_input.clear()
        self.error_label.clear_error()
        self.status_label.setText("")
    
    def set_broker_service(self, broker_service):
        self.broker_service = broker_service
    
    def set_encryption_service(self, encryption_service):
        self.encryption_service = encryption_service
