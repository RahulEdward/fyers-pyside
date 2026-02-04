"""Live Market Widget - Modern animated market overview with live prices from Fyers API"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property, Signal, QThread
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush

from src.ui.styles import COLORS, SPACING
from src.models.result import Ok, Err

import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class AnimatedNumber(QLabel):
    """Label that animates number changes with smooth transitions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._target_value = 0.0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate_step)
        self._animation_step = 0
        
    def set_value(self, value: float, animate: bool = True):
        """Set the value with optional animation"""
        self._target_value = value
        if animate and self._value != value:
            self._animation_step = 0
            self._animation_timer.start(16)  # ~60fps
        else:
            self._value = value
            self._update_display()
    
    def _animate_step(self):
        """Perform one animation step"""
        self._animation_step += 1
        progress = min(1.0, self._animation_step / 30)  # 30 steps
        eased = 1 - (1 - progress) ** 3  # Ease out cubic
        
        self._value = self._value + (self._target_value - self._value) * eased
        self._update_display()
        
        if progress >= 1.0:
            self._animation_timer.stop()
            self._value = self._target_value
            self._update_display()
    
    def _update_display(self):
        """Update the display text"""
        self.setText(f"₹{self._value:,.2f}")


class MiniSparkline(QWidget):
    """Mini sparkline chart for price history"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.is_positive = True
        self.setFixedHeight(40)
        self.setMinimumWidth(80)
    
    def set_data(self, data: list, is_positive: bool = True):
        """Set sparkline data"""
        self.data = data[-20:] if len(data) > 20 else data  # Last 20 points
        self.is_positive = is_positive
        self.update()
    
    def paintEvent(self, event):
        """Draw the sparkline"""
        if not self.data or len(self.data) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate drawing area
        width = self.width()
        height = self.height()
        padding = 4
        
        min_val = min(self.data)
        max_val = max(self.data)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Create gradient
        color = QColor(COLORS['success']) if self.is_positive else QColor(COLORS['error'])
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, color)
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 50))
        
        # Draw line
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        points = []
        for i, val in enumerate(self.data):
            x = padding + (i / (len(self.data) - 1)) * (width - 2 * padding)
            y = height - padding - ((val - min_val) / val_range) * (height - 2 * padding)
            points.append((x, y))
        
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))


class MarketCard(QFrame):
    """Modern market card with live price, change, and sparkline"""
    
    clicked = Signal(str, str)  # symbol, exchange
    
    def __init__(self, symbol: str, exchange: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.exchange = exchange
        self._is_hovered = False
        self._price_history = []
        self._last_ltp = 0.0
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(200, 130)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        # Header row
        header = QHBoxLayout()
        
        self.symbol_label = QLabel(self.symbol)
        self.symbol_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(self.symbol_label)
        
        self.exchange_badge = QLabel(self.exchange)
        self.exchange_badge.setStyleSheet(f"""
            background: {COLORS['primary_light']};
            color: {COLORS['primary']};
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        header.addWidget(self.exchange_badge)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Price
        self.price_label = AnimatedNumber()
        self.price_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        self.price_label.setText("₹0.00")
        layout.addWidget(self.price_label)
        
        # Change row
        change_layout = QHBoxLayout()
        
        self.change_label = QLabel("+₹0.00")
        self.change_label.setStyleSheet(f"font-size: 12px; color: {COLORS['success']};")
        change_layout.addWidget(self.change_label)
        
        self.change_pct_label = QLabel("(+0.00%)")
        self.change_pct_label.setStyleSheet(f"font-size: 12px; color: {COLORS['success']};")
        change_layout.addWidget(self.change_pct_label)
        
        change_layout.addStretch()
        layout.addLayout(change_layout)
        
        # Sparkline
        self.sparkline = MiniSparkline()
        layout.addWidget(self.sparkline)
    
    def _update_style(self):
        """Update card style based on hover state"""
        border_color = COLORS['primary'] if self._is_hovered else COLORS['border']
        transform = "scale(1.02)" if self._is_hovered else ""
        
        self.setStyleSheet(f"""
            MarketCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['surface']}, stop:1 {COLORS['surface_light']});
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
    
    def enterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        
    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.symbol, self.exchange)
        super().mousePressEvent(event)
    
    def update_price(self, ltp: float, change: float, change_pct: float):
        """Update price data"""
        self.price_label.set_value(ltp)
        self._last_ltp = ltp
        
        # Store for sparkline
        self._price_history.append(ltp)
        
        # Update change labels
        is_positive = change >= 0
        sign = "+" if is_positive else ""
        color = COLORS['success'] if is_positive else COLORS['error']
        
        self.change_label.setText(f"{sign}₹{change:,.2f}")
        self.change_label.setStyleSheet(f"font-size: 12px; color: {color};")
        
        self.change_pct_label.setText(f"({sign}{change_pct:.2f}%)")
        self.change_pct_label.setStyleSheet(f"font-size: 12px; color: {color};")
        
        # Update sparkline
        self.sparkline.set_data(self._price_history, is_positive)
    
    def get_last_price(self) -> float:
        return self._last_ltp


class StatCard(QFrame):
    """Animated stat card with icon and value"""
    
    def __init__(self, title: str, icon: str, color: str = None, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.color = color or COLORS['primary']
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(f"""
            StatCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {COLORS['surface']}, stop:1 rgba(0, 208, 156, 0.1));
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        self.setMinimumHeight(100)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        
        # Header with icon
        header = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            font-size: 24px;
            background: {self.color}20;
            padding: 8px;
            border-radius: 8px;
        """)
        header.addWidget(icon_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value
        self.value_label = QLabel("₹0.00")
        self.value_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(self.value_label)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title_label)
    
    def set_value(self, value: str, color: str = None):
        """Set the value"""
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"""
                font-size: 24px;
                font-weight: bold;
                color: {color};
            """)


class LiveMarketWidget(QWidget):
    """Modern live market overview widget with Fyers API integration"""
    
    trade_requested = Signal(str, str)  # symbol, exchange
    market_data_updated = Signal(dict, str, str)  # thread-safe signal
    
    def __init__(self, trading_service=None, websocket_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.websocket_service = websocket_service
        self.market_data_service = None
        self.market_cards: Dict[str, MarketCard] = {}
        self._streaming_connected = False
        
        # Connect thread-safe signal
        self.market_data_updated.connect(self._on_realtime_update_safe)
        
        self.setup_ui()
        
        # Timer for refreshing quotes (fallback when streaming not available)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_quotes)
        
        # Timer for stats refresh
        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._refresh_stats)
        self.stats_timer.start(30000)  # Every 30 seconds
        
        # Initialize market data service after UI is set up
        QTimer.singleShot(500, self._init_market_data)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING['lg'])
        
        # Welcome Section
        welcome = QLabel("📊 Market Overview")
        welcome.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            padding: 8px 0;
        """)
        layout.addWidget(welcome)
        
        # Stats Row
        stats_layout = QGridLayout()
        stats_layout.setSpacing(SPACING['md'])
        
        self.balance_card = StatCard("Available Balance", "💰", COLORS['primary'])
        stats_layout.addWidget(self.balance_card, 0, 0)
        
        self.margin_card = StatCard("Used Margin", "📊", COLORS['warning'])
        stats_layout.addWidget(self.margin_card, 0, 1)
        
        self.pnl_card = StatCard("Today's P&L", "📈", COLORS['success'])
        stats_layout.addWidget(self.pnl_card, 0, 2)
        
        self.positions_card = StatCard("Active Positions", "🎯", COLORS['secondary'])
        stats_layout.addWidget(self.positions_card, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # Market Section Header
        market_header = QHBoxLayout()
        
        market_title = QLabel("🔥 Live Prices")
        market_title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        market_header.addWidget(market_title)
        
        market_header.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: {COLORS['surface_light']};
                border-color: {COLORS['primary']};
            }}
        """)
        self.refresh_btn.clicked.connect(self._refresh_quotes)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        market_header.addWidget(self.refresh_btn)
        
        # Connection indicator
        self.live_dot = QLabel("●")
        self.live_dot.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
        market_header.addWidget(self.live_dot)
        
        self.live_label = QLabel("Connecting...")
        self.live_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        market_header.addWidget(self.live_label)
        
        layout.addLayout(market_header)
        
        # Market Cards Container (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
        """)
        
        cards_container = QWidget()
        self.cards_layout = QGridLayout(cards_container)
        self.cards_layout.setSpacing(SPACING['md'])
        
        # Default symbols to track - popular Indian stocks and indices
        self.default_symbols = [
            ("NIFTY 50", "NSE"),
            ("BANKNIFTY", "NSE"),
            ("SENSEX", "BSE"),
            ("RELIANCE", "NSE"),
            ("TCS", "NSE"),
            ("HDFCBANK", "NSE"),
            ("INFY", "NSE"),
            ("ICICIBANK", "NSE"),
        ]
        
        for i, (symbol, exchange) in enumerate(self.default_symbols):
            card = MarketCard(symbol, exchange)
            card.clicked.connect(self._on_card_clicked)
            self.cards_layout.addWidget(card, i // 4, i % 4)
            self.market_cards[f"{exchange}:{symbol}"] = card
        
        scroll.setWidget(cards_container)
        layout.addWidget(scroll, stretch=1)
        
        # Quick Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(SPACING['md'])
        
        quick_buy = QPushButton("⚡ Quick Buy")
        quick_buy.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['success']}, stop:1 #00B386);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 28px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['success']};
            }}
        """)
        quick_buy.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(quick_buy)
        
        quick_sell = QPushButton("🔻 Quick Sell")
        quick_sell.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['error']}, stop:1 #D93232);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 28px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['error']};
            }}
        """)
        quick_sell.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(quick_sell)
        
        actions_layout.addStretch()
        layout.addLayout(actions_layout)
    
    def _init_market_data(self):
        """Initialize market data service"""
        try:
            # Get access token from trading service if available
            access_token = ""
            user_id = ""
            
            if self.trading_service:
                access_token = getattr(self.trading_service, 'access_token', '')
            
            if access_token:
                from src.services.market_data_service import MarketDataService
                self.market_data_service = MarketDataService(access_token, user_id)
                
                # Set global callback for streaming updates
                self.market_data_service.set_global_callback(self._on_streaming_data)
                
                # Try to connect streaming
                self._connect_streaming()
                
                # Fetch initial quotes
                self._refresh_quotes()
                
                logger.info("Market data service initialized")
            else:
                logger.warning("No access token available for market data")
                self.update_connection_status(False)
                # Start polling timer as fallback
                self.refresh_timer.start(10000)  # Every 10 seconds
                
        except Exception as e:
            logger.error(f"Error initializing market data: {e}")
            self.update_connection_status(False)
    
    def _connect_streaming(self):
        """Connect to streaming WebSocket"""
        if not self.market_data_service:
            return
        
        try:
            result = self.market_data_service.connect_streaming()
            if isinstance(result, Ok):
                self._streaming_connected = True
                self.update_connection_status(True)
                
                # Subscribe to all default symbols
                for symbol, exchange in self.default_symbols:
                    self.market_data_service.subscribe_realtime(
                        symbol, exchange, 
                        lambda data, s=symbol, e=exchange: self._on_realtime_update(data, s, e)
                    )
                
                logger.info("Connected to real-time streaming")
            else:
                logger.warning(f"Streaming connection failed: {result.error}")
                self.update_connection_status(False)
                # Fallback to polling
                self.refresh_timer.start(5000)  # Every 5 seconds
                
        except Exception as e:
            logger.error(f"Streaming connection error: {e}")
            self.update_connection_status(False)
            self.refresh_timer.start(5000)
    
    def _on_streaming_data(self, quote_data):
        """Handle streaming data from global callback"""
        try:
            key = f"{quote_data.exchange}:{quote_data.symbol}"
            if key in self.market_cards:
                self.market_cards[key].update_price(
                    quote_data.ltp,
                    quote_data.change,
                    quote_data.change_pct
                )
        except Exception as e:
            logger.debug(f"Error processing streaming data: {e}")
    
    def _on_realtime_update(self, data: Dict[str, Any], symbol: str, exchange: str):
        """Handle real-time price update (Thread Safe)"""
        self.market_data_updated.emit(data, symbol, exchange)

    def _on_realtime_update_safe(self, data: Dict[str, Any], symbol: str, exchange: str):
        """Handle real-time price update in main thread"""
        try:
            ltp = data.get('ltp', 0)
            prev_close = data.get('close', data.get('prev_close', 0))
            change = ltp - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            key = f"{exchange}:{symbol}"
            if key in self.market_cards:
                self.market_cards[key].update_price(ltp, change, change_pct)
                
        except Exception as e:
            logger.debug(f"Error processing real-time update: {e}")
    
    def _refresh_quotes(self):
        """Refresh quotes for all symbols"""
        if not self.market_data_service:
            return
        
        try:
            symbols = [{"symbol": s, "exchange": e} for s, e in self.default_symbols]
            result = self.market_data_service.get_multi_quotes(symbols)
            
            if isinstance(result, Ok):
                for quote in result.value:
                    key = f"{quote.exchange}:{quote.symbol}"
                    if key in self.market_cards:
                        self.market_cards[key].update_price(
                            quote.ltp,
                            quote.change,
                            quote.change_pct
                        )
                logger.debug(f"Refreshed {len(result.value)} quotes")
            else:
                logger.warning(f"Failed to refresh quotes: {result.error}")
                
        except Exception as e:
            logger.error(f"Error refreshing quotes: {e}")
    
    def _refresh_stats(self):
        """Refresh account statistics"""
        if not self.trading_service:
            return
        
        try:
            # Get funds
            funds_result = self.trading_service.get_funds()
            if isinstance(funds_result, Ok):
                funds = funds_result.value
                self.balance_card.set_value(f"₹{funds.get('available_cash', 0):,.2f}")
                self.margin_card.set_value(f"₹{funds.get('utilized_margin', 0):,.2f}")
                
                pnl = funds.get('realized_pnl', 0) + funds.get('unrealized_pnl', 0)
                pnl_color = COLORS['success'] if pnl >= 0 else COLORS['error']
                sign = "+" if pnl >= 0 else ""
                self.pnl_card.set_value(f"{sign}₹{pnl:,.2f}", pnl_color)
            
            # Get positions count
            pos_result = self.trading_service.get_positions()
            if isinstance(pos_result, Ok):
                positions = pos_result.value
                self.positions_card.set_value(str(len(positions)))
        except Exception as e:
            logger.debug(f"Error refreshing stats: {e}")
    
    def _on_card_clicked(self, symbol: str, exchange: str):
        """Handle market card click"""
        self.trade_requested.emit(symbol, exchange)
    
    def update_connection_status(self, connected: bool):
        """Update live connection status"""
        if connected:
            self.live_dot.setStyleSheet(f"color: {COLORS['success']}; font-size: 16px;")
            self.live_label.setText("Live")
        else:
            self.live_dot.setStyleSheet(f"color: {COLORS['error']}; font-size: 16px;")
            self.live_label.setText("Disconnected")
    
    def update_price(self, symbol: str, exchange: str, ltp: float, change: float, change_pct: float):
        """Update price for a symbol"""
        key = f"{exchange}:{symbol}"
        if key in self.market_cards:
            self.market_cards[key].update_price(ltp, change, change_pct)
    
    def set_trading_service(self, trading_service):
        """Set trading service"""
        self.trading_service = trading_service
        self._refresh_stats()
        
        # Re-initialize market data if we now have access token
        if trading_service and self.market_data_service is None:
            QTimer.singleShot(500, self._init_market_data)
    
    def set_websocket_service(self, websocket_service):
        """Set websocket service"""
        self.websocket_service = websocket_service
    
    def add_symbol(self, symbol: str, exchange: str):
        """Add a new symbol to track"""
        key = f"{exchange}:{symbol}"
        if key not in self.market_cards:
            row = len(self.market_cards) // 4
            col = len(self.market_cards) % 4
            
            card = MarketCard(symbol, exchange)
            card.clicked.connect(self._on_card_clicked)
            self.cards_layout.addWidget(card, row, col)
            self.market_cards[key] = card
            
            # Subscribe to streaming if connected
            if self.market_data_service and self._streaming_connected:
                self.market_data_service.subscribe_realtime(
                    symbol, exchange,
                    lambda data, s=symbol, e=exchange: self._on_realtime_update(data, s, e)
                )
