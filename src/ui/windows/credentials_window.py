"""Credentials window for broker API authentication"""
import webbrowser
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QTimer

from src.ui.styles import COLORS, LABELS, SPACING, MAIN_STYLESHEET
from src.ui.utils import ErrorLabel, SuccessLabel, LoadingOverlay, StatusIndicator


class CredentialsWindow(QMainWindow):
    """Window for entering broker API credentials and OAuth authentication"""
    
    # Signals
    authentication_successful = Signal(str)  # Emits access token on success
    skip_requested = Signal()                 # Emits when user wants to skip
    
    def __init__(self, broker_service=None, user_id: int = None):
        super().__init__()
        self.broker_service = broker_service
        self.user_id = user_id
        self.oauth_url = None
        self.setup_ui()
        self.setStyleSheet(MAIN_STYLESHEET)
    
    def setup_ui(self):
        self.setWindowTitle("Fyers Trading - Broker Authentication")
        self.setFixedSize(500, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        layout.setSpacing(SPACING['md'])
        
        # Title
        title = QLabel("Broker Authentication")
        title.setProperty("type", "header")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Connect your Fyers account")
        subtitle.setProperty("type", "title")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(subtitle)
        
        # Status indicator
        self.status = StatusIndicator()
        layout.addWidget(self.status, alignment=Qt.AlignCenter)
        
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
        form_layout.setSpacing(SPACING['md'])
        
        # API Key field
        api_key_label = QLabel(LABELS['api_key'])
        form_layout.addWidget(api_key_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your Fyers API Key")
        form_layout.addWidget(self.api_key_input)
        
        # API Secret field
        api_secret_label = QLabel(LABELS['api_secret'])
        form_layout.addWidget(api_secret_label)
        
        self.api_secret_input = QLineEdit()
        self.api_secret_input.setPlaceholderText("Enter your Fyers API Secret")
        self.api_secret_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.api_secret_input)
        
        # Error/Success labels
        self.error_label = ErrorLabel()
        form_layout.addWidget(self.error_label)
        
        self.success_label = SuccessLabel()
        form_layout.addWidget(self.success_label)
        
        form_layout.addSpacing(SPACING['sm'])
        
        # Save credentials button
        self.save_btn = QPushButton("Save Credentials")
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setCursor(Qt.PointingHandCursor)
        form_layout.addWidget(self.save_btn)
        
        # Authenticate button
        self.auth_btn = QPushButton(LABELS['authenticate'])
        self.auth_btn.setProperty("type", "success")
        self.auth_btn.clicked.connect(self._on_authenticate_clicked)
        self.auth_btn.setCursor(Qt.PointingHandCursor)
        self.auth_btn.setEnabled(False)
        form_layout.addWidget(self.auth_btn)
        
        layout.addWidget(form)
        
        # Auth code section (shown after OAuth redirect)
        self.auth_code_frame = QFrame()
        self.auth_code_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: {SPACING['md']}px;
            }}
        """)
        auth_code_layout = QVBoxLayout(self.auth_code_frame)
        
        auth_code_label = QLabel("Enter Authorization Code")
        auth_code_label.setStyleSheet("font-weight: bold;")
        auth_code_layout.addWidget(auth_code_label)
        
        auth_code_help = QLabel("After authenticating in browser, paste the auth code here:")
        auth_code_help.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        auth_code_help.setWordWrap(True)
        auth_code_layout.addWidget(auth_code_help)
        
        self.auth_code_input = QLineEdit()
        self.auth_code_input.setPlaceholderText("Paste authorization code here")
        auth_code_layout.addWidget(self.auth_code_input)
        
        self.verify_btn = QPushButton("Verify & Connect")
        self.verify_btn.setProperty("type", "success")
        self.verify_btn.clicked.connect(self._on_verify_clicked)
        self.verify_btn.setCursor(Qt.PointingHandCursor)
        auth_code_layout.addWidget(self.verify_btn)
        
        layout.addWidget(self.auth_code_frame)
        self.auth_code_frame.hide()
        
        # Skip button
        skip_layout = QHBoxLayout()
        skip_layout.setAlignment(Qt.AlignCenter)
        
        self.skip_btn = QPushButton("Skip for now")
        self.skip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
            }}
            QPushButton:hover {{
                color: {COLORS['primary']};
            }}
        """)
        self.skip_btn.setCursor(Qt.PointingHandCursor)
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        skip_layout.addWidget(self.skip_btn)
        
        layout.addLayout(skip_layout)
        
        layout.addStretch()
        
        # Loading overlay
        self.loading = LoadingOverlay(central)
        
        # Check for existing credentials
        self._check_existing_credentials()
    
    def _check_existing_credentials(self):
        """Check if credentials already exist"""
        if self.broker_service and self.user_id:
            try:
                if self.broker_service.has_credentials(self.user_id):
                    self.auth_btn.setEnabled(True)
                    self.success_label.show_success("Credentials found. Click Authenticate to connect.")
            except Exception:
                pass
    
    def _on_save_clicked(self):
        """Handle save credentials button click"""
        self.error_label.clear_error()
        self.success_label.clear_message()
        
        api_key = self.api_key_input.text().strip()
        api_secret = self.api_secret_input.text().strip()
        
        # Validate inputs
        if not api_key:
            self.error_label.show_error("API Key is required")
            return
        
        if not api_secret:
            self.error_label.show_error("API Secret is required")
            return
        
        # Save credentials
        if self.broker_service and self.user_id:
            self.loading.show_loading("Saving credentials...")
            self.save_btn.setEnabled(False)
            
            try:
                from src.models.result import Ok, Err
                result = self.broker_service.save_credentials(
                    self.user_id, api_key, api_secret
                )
                
                if isinstance(result, Ok):
                    self.success_label.show_success("Credentials saved successfully!")
                    self.auth_btn.setEnabled(True)
                else:
                    self.error_label.show_error(result.error)
            except Exception as e:
                self.error_label.show_error(f"Failed to save: {str(e)}")
            finally:
                self.loading.hide_loading()
                self.save_btn.setEnabled(True)
        else:
            # No broker service - just enable auth button
            self.auth_btn.setEnabled(True)
            self.success_label.show_success("Credentials saved (test mode)")
    
    def _on_authenticate_clicked(self):
        """Handle authenticate button click"""
        self.error_label.clear_error()
        
        if self.broker_service and self.user_id:
            self.loading.show_loading("Generating OAuth URL...")
            
            try:
                from src.models.result import Ok, Err
                result = self.broker_service.generate_oauth_url(self.user_id)
                
                if isinstance(result, Ok):
                    self.oauth_url = result.value
                    # Open browser for OAuth
                    webbrowser.open(self.oauth_url)
                    # Show auth code input
                    self.auth_code_frame.show()
                    self.success_label.show_success("Browser opened. Complete authentication and paste the code.")
                else:
                    self.error_label.show_error(result.error)
            except Exception as e:
                self.error_label.show_error(f"Failed to authenticate: {str(e)}")
            finally:
                self.loading.hide_loading()
        else:
            # Test mode - show auth code input
            self.auth_code_frame.show()
    
    def _on_verify_clicked(self):
        """Handle verify auth code button click"""
        self.error_label.clear_error()
        
        auth_code = self.auth_code_input.text().strip()
        
        if not auth_code:
            self.error_label.show_error("Authorization code is required")
            return
        
        if self.broker_service and self.user_id:
            self.loading.show_loading("Verifying authorization...")
            self.verify_btn.setEnabled(False)
            
            try:
                from src.models.result import Ok, Err
                result = self.broker_service.authenticate_broker(self.user_id, auth_code)
                
                if isinstance(result, Ok):
                    access_token = result.value
                    self.status.set_connected()
                    self.success_label.show_success("Successfully connected to Fyers!")
                    # Emit success signal after short delay
                    QTimer.singleShot(1000, lambda: self.authentication_successful.emit(access_token))
                else:
                    self.error_label.show_error(result.error)
            except Exception as e:
                self.error_label.show_error(f"Verification failed: {str(e)}")
            finally:
                self.loading.hide_loading()
                self.verify_btn.setEnabled(True)
        else:
            # Test mode - emit success
            self.status.set_connected()
            self.authentication_successful.emit("test_access_token")
    
    def _on_skip_clicked(self):
        """Handle skip button click"""
        self.skip_requested.emit()
    
    def set_broker_service(self, broker_service):
        """Set the broker service"""
        self.broker_service = broker_service
        self._check_existing_credentials()
    
    def set_user_id(self, user_id: int):
        """Set the user ID"""
        self.user_id = user_id
        self._check_existing_credentials()
