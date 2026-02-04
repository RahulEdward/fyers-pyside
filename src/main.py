"""Main application entry point for Fyers Trading System"""
import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt

# Add src to path so imports like 'database.token_db' work
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from src.database.connection import init_db, get_session
from src.services.broker_service import BrokerService
from src.services.trading_service import TradingService
from src.services.watchlist_service import WatchlistService
from src.services.websocket_service import WebSocketService
from src.services.encryption_service import EncryptionService
from src.services.master_contract_service import MasterContractService
from src.repositories.credential_repository import CredentialRepository
from src.ui.windows.login_window import LoginWindow
from src.ui.windows.dashboard_window import DashboardWindow
from src.ui.styles import MAIN_STYLESHEET

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingApp:
    """Main application controller"""
    
    def __init__(self):
        # Fix taskbar icon grouping on Windows
        if os.name == 'nt':
            try:
                import ctypes
                myappid = 'fyers.trading.desktop.app.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass
                
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Fyers Trading")
        
        # Set Application Icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')
            if os.path.exists(icon_path):
                self.app.setWindowIcon(QIcon(icon_path))
                logger.info(f"Loaded application icon from {icon_path}")
            else:
                logger.warning(f"Icon file not found at {icon_path}")
        except Exception as e:
            logger.error(f"Failed to set icon: {e}")
            
        self.app.setStyleSheet(MAIN_STYLESHEET)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Get database session
        self.db_session = get_session()
        
        # Initialize services
        self._init_services()
        
        # Current credentials
        self.current_credentials = None
        self.access_token = None
        
        # Windows
        self.login_window = None
        self.dashboard_window = None
        
        # Show login window
        self._show_login()
    
    def _init_services(self):
        """Initialize all services"""
        # Encryption key - in production, use environment variable
        encryption_key = b'fyers_trading_app_secret_key_2024'
        self.encryption_service = EncryptionService(encryption_key)
        
        # Credential repository
        self.cred_repo = CredentialRepository(self.db_session)
        
        # Broker service
        self.broker_service = BrokerService(self.cred_repo, self.encryption_service)
        
        # Watchlist service
        self.watchlist_service = WatchlistService(self.db_session)
        
        # Master contract service
        self.master_contract_service = MasterContractService(self.db_session)
        
        # Trading services - initialized after login
        self.trading_service = None
        self.websocket_service = None
    
    def _show_login(self):
        """Show login window"""
        if self.login_window is None:
            self.login_window = LoginWindow(
                broker_service=self.broker_service,
                encryption_service=self.encryption_service
            )
            self.login_window.login_successful.connect(self._on_login_success)
        
        self._hide_all_windows()
        self.login_window.clear_form()
        self.login_window.show()
    
    def _show_dashboard(self):
        """Show dashboard window"""
        if self.dashboard_window is None:
            self.dashboard_window = DashboardWindow(
                user=self.current_credentials,
                trading_service=self.trading_service,
                watchlist_service=self.watchlist_service,
                websocket_service=self.websocket_service,
                master_contract_service=self.master_contract_service
            )
            self.dashboard_window.logout_requested.connect(self._on_logout)
        else:
            self.dashboard_window.set_user(self.current_credentials)
            self.dashboard_window.set_services(
                trading_service=self.trading_service,
                watchlist_service=self.watchlist_service,
                websocket_service=self.websocket_service,
                master_contract_service=self.master_contract_service
            )
        
        self._hide_all_windows()
        self.dashboard_window.show()
        self.dashboard_window.refresh_all()
    
    def _hide_all_windows(self):
        """Hide all windows"""
        if self.login_window:
            self.login_window.hide()
        if self.dashboard_window:
            self.dashboard_window.hide()
    
    def _on_login_success(self, credentials: dict):
        """Handle successful login with broker credentials"""
        logger.info(f"Logged in as: {credentials.get('broker_username')}")
        self.current_credentials = credentials
        
        # Get access token from OAuth
        self.access_token = credentials.get('access_token')
        
        if self.access_token:
            logger.info("Access token received from Fyers OAuth")
            
            # Save tokens to database
            self.cred_repo.save_tokens(
                broker_username=credentials.get('broker_username'),
                access_token=self.access_token,
                feed_token=credentials.get('feed_token'),
                refresh_token=credentials.get('refresh_token')
            )
            
            # Initialize trading services with real access token
            self.trading_service = TradingService(self.access_token)
            self.websocket_service = WebSocketService(
                self.access_token, 
                credentials.get('broker_username', 'user')
            )
            
            # Check if symbols are downloaded
            symbol_count = self.master_contract_service.get_symbol_count()
            if symbol_count == 0:
                logger.info("No symbols found, downloading master contracts...")
                self._download_symbols()
        else:
            logger.warning("No access token - trading features will be limited")
            self.trading_service = TradingService("")
            self.websocket_service = None
        
        # Show dashboard
        self._show_dashboard()
    
    def _download_symbols(self):
        """Download master contract symbols in background"""
        try:
            success, msg = self.master_contract_service.download_master_contracts()
            if success:
                logger.info(f"Symbols downloaded: {msg}")
            else:
                logger.error(f"Symbol download failed: {msg}")
        except Exception as e:
            logger.error(f"Symbol download error: {e}")
    
    def _on_logout(self):
        """Handle logout"""
        logger.info("User logged out")
        
        # Disconnect websocket
        if self.websocket_service:
            self.websocket_service.disconnect()
            self.websocket_service = None
        
        # Clear data
        self.current_credentials = None
        self.access_token = None
        self.trading_service = None
        
        # Show login
        self._show_login()
    
    def run(self):
        """Run the application"""
        logger.info("Starting Fyers Trading application...")
        return self.app.exec()


def main():
    """Main entry point"""
    try:
        app = TradingApp()
        sys.exit(app.run())
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
