"""Dashboard window - main trading interface"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QFrame
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, MAIN_STYLESHEET
from src.ui.widgets.funds_widget import FundsWidget
from src.ui.widgets.positions_widget import PositionsWidget
from src.ui.widgets.holdings_widget import HoldingsWidget
from src.ui.widgets.order_book_widget import OrderBookWidget
from src.ui.widgets.order_form_widget import OrderFormWidget
from src.ui.widgets.watchlist_widget import WatchlistWidget


class DashboardWindow(QMainWindow):
    """Main dashboard window with tabbed interface"""
    
    logout_requested = Signal()
    
    def __init__(
        self,
        user=None,
        trading_service=None,
        watchlist_service=None,
        websocket_service=None,
        master_contract_service=None
    ):
        super().__init__()
        self.user = user
        self.trading_service = trading_service
        self.watchlist_service = watchlist_service
        self.websocket_service = websocket_service
        self.master_contract_service = master_contract_service
        self.setup_ui()
        self.setStyleSheet(MAIN_STYLESHEET)
    
    def setup_ui(self):
        self.setWindowTitle("Fyers Trading Dashboard")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Content area with tabs
        content = QHBoxLayout()
        content.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        content.setSpacing(SPACING['md'])
        
        # Left side - Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                background-color: {COLORS['surface']};
            }}
        """)
        
        # Create tab widgets
        self.funds_widget = FundsWidget(self.trading_service)
        self.positions_widget = PositionsWidget(self.trading_service)
        self.holdings_widget = HoldingsWidget(self.trading_service)
        self.orders_widget = OrderBookWidget(self.trading_service)
        self.watchlist_widget = WatchlistWidget(self.watchlist_service, self.websocket_service)
        
        # Set user ID for watchlist
        if self.user:
            user_id = self.user.id if hasattr(self.user, 'id') else self.user.get('id')
            if user_id:
                self.watchlist_widget.set_user_id(user_id)
        
        # Add tabs
        self.tabs.addTab(self.funds_widget, LABELS['funds'])
        self.tabs.addTab(self.positions_widget, LABELS['positions'])
        self.tabs.addTab(self.holdings_widget, LABELS['holdings'])
        self.tabs.addTab(self.orders_widget, LABELS['orders'])
        self.tabs.addTab(self.watchlist_widget, LABELS['watchlist'])
        
        # Connect tab change to refresh data
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        content.addWidget(self.tabs, stretch=2)
        
        # Right side - Order form
        self.order_form = OrderFormWidget(self.trading_service, self.master_contract_service)
        self.order_form.setMaximumWidth(350)
        self.order_form.order_submitted.connect(self._on_order_submitted)
        content.addWidget(self.order_form)
        
        # Connect watchlist trade signal to order form
        self.watchlist_widget.trade_symbol_requested.connect(self._on_trade_from_watchlist)
        
        layout.addLayout(content)
    
    def _create_header(self) -> QFrame:
        """Create the header bar"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['primary']};
                padding: {SPACING['sm']}px {SPACING['md']}px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        header.setFixedHeight(60)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACING['md'], 0, SPACING['md'], 0)
        
        # Logo/Title
        title = QLabel("Fyers Trading")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search symbols...")
        self.search_input.setFixedWidth(250)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                color: white;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.7);
            }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        # User info
        username = "User"
        if self.user:
            username = self.user.get('broker_username', self.user.get('username', 'User')) if isinstance(self.user, dict) else getattr(self.user, 'broker_username', getattr(self.user, 'username', 'User'))
        
        user_label = QLabel(f"👤 {username}")
        user_label.setStyleSheet("color: white; margin-right: 16px;")
        layout.addWidget(user_label)
        
        # Logout button
        logout_btn = QPushButton(LABELS['logout'])
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
            }}
        """)
        logout_btn.clicked.connect(self._on_logout)
        logout_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(logout_btn)
        
        return header
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh data for the selected tab"""
        widget = self.tabs.widget(index)
        
        if isinstance(widget, FundsWidget):
            widget.load_funds()
        elif isinstance(widget, PositionsWidget):
            widget.load_positions()
        elif isinstance(widget, HoldingsWidget):
            widget.load_holdings()
        elif isinstance(widget, OrderBookWidget):
            widget.load_orders()
        elif isinstance(widget, WatchlistWidget):
            widget.load_watchlist()
    
    def _on_search(self):
        """Handle search input - search symbols from master contract"""
        query = self.search_input.text().strip()
        if query and self.master_contract_service:
            results = self.master_contract_service.search_symbols(query, limit=10)
            if results:
                # Use first result
                first = results[0]
                self.order_form.set_symbol(first['symbol'], first['exchange'])
            else:
                self.order_form.set_symbol(query.upper())
    
    def _on_trade_from_watchlist(self, symbol: str, exchange: str):
        """Handle trade request from watchlist"""
        self.order_form.set_symbol(symbol, exchange)
    
    def _on_order_submitted(self, order_data: dict):
        """Handle order submission - refresh orders"""
        self.orders_widget.load_orders()
        self.positions_widget.load_positions()
        self.funds_widget.load_funds()
    
    def _on_logout(self):
        """Handle logout button click"""
        self.logout_requested.emit()
    
    def set_user(self, user):
        """Set the current user"""
        self.user = user
        if user:
            user_id = user.id if hasattr(user, 'id') else user.get('id')
            if user_id:
                self.watchlist_widget.set_user_id(user_id)
    
    def set_services(self, trading_service=None, watchlist_service=None, websocket_service=None, master_contract_service=None):
        """Set all services"""
        if trading_service:
            self.trading_service = trading_service
            self.funds_widget.set_trading_service(trading_service)
            self.positions_widget.set_trading_service(trading_service)
            self.holdings_widget.set_trading_service(trading_service)
            self.orders_widget.set_trading_service(trading_service)
            self.order_form.set_trading_service(trading_service)
        
        if watchlist_service:
            self.watchlist_service = watchlist_service
            self.watchlist_widget.set_watchlist_service(watchlist_service)
        
        if websocket_service:
            self.websocket_service = websocket_service
            self.watchlist_widget.set_websocket_service(websocket_service)
        
        if master_contract_service:
            self.master_contract_service = master_contract_service
            self.order_form.set_master_contract_service(master_contract_service)
    
    def refresh_all(self):
        """Refresh all data"""
        self.funds_widget.load_funds()
        self.positions_widget.load_positions()
        self.holdings_widget.load_holdings()
        self.orders_widget.load_orders()
        self.watchlist_widget.load_watchlist()
