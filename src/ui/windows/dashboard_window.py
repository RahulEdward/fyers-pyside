"""Dashboard window - main trading interface with modern design"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QLineEdit, QFrame,
    QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from src.ui.styles import COLORS, LABELS, SPACING, MAIN_STYLESHEET
from src.ui.widgets.funds_widget import FundsWidget
from src.ui.widgets.positions_widget import PositionsWidget
from src.ui.widgets.holdings_widget import HoldingsWidget
from src.ui.widgets.order_book_widget import OrderBookWidget
from src.ui.widgets.order_form_widget import OrderFormWidget
from src.ui.widgets.watchlist_widget import WatchlistWidget
from src.ui.widgets.live_market_widget import LiveMarketWidget
from src.ui.widgets.analytics_widget import AnalyticsWidget
from src.ui.widgets.auto_trading_widget import AutoTradingWidget


class DashboardWindow(QMainWindow):
    """Main dashboard window with modern tabbed interface"""
    
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
        self.setMinimumSize(1400, 900)
        
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
        
        # Content area
        content = QHBoxLayout()
        content.setContentsMargins(SPACING['lg'], SPACING['lg'], SPACING['lg'], SPACING['lg'])
        content.setSpacing(SPACING['lg'])
        
        # Main area with tabs
        main_area = QVBoxLayout()
        main_area.setSpacing(0)
        
        # Modern Tab Bar
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabWidget::tab-bar {{
                alignment: left;
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background-color: transparent;
                padding: 14px 28px;
                margin-right: 4px;
                border: none;
                border-bottom: 3px solid transparent;
                color: {COLORS['text_secondary']};
                font-weight: 600;
                font-size: 13px;
            }}
            QTabBar::tab:selected {{
                color: {COLORS['primary']};
                border-bottom: 3px solid {COLORS['primary']};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {COLORS['primary']}15, stop:1 transparent);
            }}
            QTabBar::tab:hover:!selected {{
                color: {COLORS['text_primary']};
                background: {COLORS['surface']};
                border-radius: 8px 8px 0 0;
            }}
        """)
        
        # Create tab widgets
        # 1. Home/Overview Tab (NEW - Modern Live Market)
        self.home_widget = LiveMarketWidget(self.trading_service, self.websocket_service)
        
        # 2. Analytics Tab (NEW)
        self.analytics_widget = AnalyticsWidget(self.trading_service)
        
        # 3. Auto Trading Tab (NEW)
        self.auto_trading_widget = AutoTradingWidget(self.trading_service)
        
        # 4. Traditional tabs
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
        
        # Add tabs with icons
        self.tabs.addTab(self.home_widget, "🏠 Home")
        self.tabs.addTab(self.analytics_widget, "📊 Analytics")
        self.tabs.addTab(self.auto_trading_widget, "🤖 Auto Trade")
        self.tabs.addTab(self.funds_widget, "💰 " + LABELS['funds'])
        self.tabs.addTab(self.positions_widget, "📈 " + LABELS['positions'])
        self.tabs.addTab(self.holdings_widget, "📦 " + LABELS['holdings'])
        self.tabs.addTab(self.orders_widget, "📋 " + LABELS['orders'])
        self.tabs.addTab(self.watchlist_widget, "👁️ " + LABELS['watchlist'])
        
        # Connect tab change to refresh data
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        main_area.addWidget(self.tabs)
        content.addLayout(main_area, stretch=3)
        
        # Right sidebar - Order form (collapsible)
        sidebar = QFrame()
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        sidebar.setMaximumWidth(380)
        sidebar.setMinimumWidth(350)
        
        # Add subtle shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 50))
        sidebar.setGraphicsEffect(shadow)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.order_form = OrderFormWidget(self.trading_service, self.master_contract_service)
        self.order_form.order_submitted.connect(self._on_order_submitted)
        sidebar_layout.addWidget(self.order_form)
        
        content.addWidget(sidebar)
        
        # Connect watchlist trade signal to order form
        self.watchlist_widget.trade_symbol_requested.connect(self._on_trade_from_watchlist)
        
        layout.addLayout(content)
    
    def _create_header(self) -> QFrame:
        """Create the modern header bar"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']}, stop:1 #00B386);
                padding: {SPACING['sm']}px {SPACING['md']}px;
            }}
            QLabel {{
                color: white;
            }}
        """)
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(SPACING['lg'], 0, SPACING['lg'], 0)
        
        # Logo/Title with icon
        logo_container = QHBoxLayout()
        logo_container.setSpacing(10)
        
        logo_icon = QLabel("📈")
        logo_icon.setStyleSheet("font-size: 28px; background: transparent;")
        logo_container.addWidget(logo_icon)
        
        title = QLabel("Fyers Trading")
        title.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: white;
            background: transparent;
        """)
        logo_container.addWidget(title)
        
        layout.addLayout(logo_container)
        
        layout.addStretch()
        
        # Search bar with modern styling
        search_container = QFrame()
        search_container.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }}
        """)
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 0, 12, 0)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 14px; background: transparent;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search symbols...")
        self.search_input.setFixedWidth(220)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 10px 0;
                color: white;
                font-size: 13px;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.7);
            }}
        """)
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        layout.addStretch()
        
        # Connection status
        self.connection_status = QLabel("● Connected")
        self.connection_status.setStyleSheet("""
            color: #90EE90;
            font-size: 12px;
            background: transparent;
            margin-right: 16px;
        """)
        layout.addWidget(self.connection_status)
        
        # User info with avatar
        user_container = QFrame()
        user_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 4px 12px;
            }
        """)
        user_layout = QHBoxLayout(user_container)
        user_layout.setContentsMargins(8, 4, 8, 4)
        user_layout.setSpacing(8)
        
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 18px; background: transparent;")
        user_layout.addWidget(avatar)
        
        username = "User"
        if self.user:
            username = self.user.get('broker_username', self.user.get('username', 'User')) if isinstance(self.user, dict) else getattr(self.user, 'broker_username', getattr(self.user, 'username', 'User'))
        
        user_label = QLabel(username)
        user_label.setStyleSheet("color: white; font-weight: 500; background: transparent;")
        user_layout.addWidget(user_label)
        
        layout.addWidget(user_container)
        
        # Logout button
        logout_btn = QPushButton(LABELS['logout'])
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.3);
                border-color: rgba(255, 255, 255, 0.5);
            }}
        """)
        logout_btn.clicked.connect(self._on_logout)
        logout_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(logout_btn)
        
        return header
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh data for the selected tab"""
        widget = self.tabs.widget(index)
        
        if isinstance(widget, LiveMarketWidget):
            widget._refresh_stats()
        elif isinstance(widget, FundsWidget):
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
            self.home_widget.set_trading_service(trading_service)
            self.analytics_widget.set_trading_service(trading_service)
            self.auto_trading_widget.set_trading_service(trading_service)
        
        if watchlist_service:
            self.watchlist_service = watchlist_service
            self.watchlist_widget.set_watchlist_service(watchlist_service)
        
        if websocket_service:
            self.websocket_service = websocket_service
            self.watchlist_widget.set_websocket_service(websocket_service)
            self.home_widget.set_websocket_service(websocket_service)
        
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
        if hasattr(self, 'home_widget'):
            self.home_widget._refresh_stats()
