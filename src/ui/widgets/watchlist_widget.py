"""Watchlist widget for displaying and managing watchlist"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView,
    QLineEdit
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, get_profit_loss_color
from src.ui.utils import (
    LoadingOverlay, format_currency, format_percentage,
    show_confirm_dialog
)


class WatchlistWidget(QWidget):
    """Widget for displaying and managing watchlist with live prices"""
    
    refresh_requested = Signal()
    remove_symbol_requested = Signal(str, str)  # symbol, exchange
    trade_symbol_requested = Signal(str, str)   # symbol, exchange
    
    def __init__(self, watchlist_service=None, websocket_service=None, parent=None):
        super().__init__(parent)
        self.watchlist_service = watchlist_service
        self.websocket_service = websocket_service
        self.user_id = None
        self.watchlist_items = []
        self.price_data = {}  # symbol:exchange -> price data
        self.is_connected = False
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(LABELS['watchlist'])
        title.setProperty("type", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        # Connection status indicator
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(f"color: {COLORS['error']};")
        header.addWidget(self.status_dot)
        
        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        header.addWidget(self.status_label)
        
        self.refresh_btn = QPushButton(LABELS['refresh'])
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Watchlist table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Exchange", "LTP", "Change", "Change %", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Summary
        summary = QHBoxLayout()
        
        self.item_count = QLabel("0 symbols")
        self.item_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary.addWidget(self.item_count)
        
        summary.addStretch()
        
        layout.addLayout(summary)
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
        self.load_watchlist()
    
    def _on_remove_symbol(self, row: int):
        """Handle remove symbol button click"""
        if row < len(self.watchlist_items):
            item = self.watchlist_items[row]
            symbol = item.symbol
            exchange = item.exchange
            
            if show_confirm_dialog(
                self,
                "Remove Symbol",
                f"Remove {symbol} from watchlist?"
            ):
                self.remove_symbol_requested.emit(symbol, exchange)
                self._remove_from_watchlist(symbol, exchange)
    
    def _on_trade_symbol(self, row: int):
        """Handle trade button click"""
        if row < len(self.watchlist_items):
            item = self.watchlist_items[row]
            self.trade_symbol_requested.emit(item.symbol, item.exchange)
    
    def _remove_from_watchlist(self, symbol: str, exchange: str):
        """Remove symbol from watchlist"""
        if self.watchlist_service and self.user_id:
            result = self.watchlist_service.remove_symbol(self.user_id, symbol, exchange)
            from src.models.result import Ok
            if isinstance(result, Ok):
                self.load_watchlist()
    
    def load_watchlist(self):
        """Load watchlist from service"""
        if not self.watchlist_service or not self.user_id:
            return
        
        self.loading.show_loading("Loading watchlist...")
        self.refresh_btn.setEnabled(False)
        
        try:
            from src.models.result import Ok, Err
            result = self.watchlist_service.get_watchlist(self.user_id)
            
            if isinstance(result, Ok):
                self.update_watchlist(result.value)
                self._subscribe_to_prices()
        except Exception:
            pass
        finally:
            self.loading.hide_loading()
            self.refresh_btn.setEnabled(True)
    
    def update_watchlist(self, items: list):
        """Update the table with watchlist items"""
        self.watchlist_items = items
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            symbol = item.symbol
            exchange = item.exchange
            key = f"{symbol}:{exchange}"
            
            # Symbol
            symbol_item = QTableWidgetItem(symbol)
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, symbol_item)
            
            # Exchange
            exchange_item = QTableWidgetItem(exchange)
            exchange_item.setFlags(exchange_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, exchange_item)
            
            # Get price data if available
            price_info = self.price_data.get(key, {})
            ltp = price_info.get('ltp', 0)
            change = price_info.get('change', 0)
            change_pct = price_info.get('change_percent', 0)
            
            # LTP
            ltp_item = QTableWidgetItem(format_currency(ltp) if ltp else "-")
            ltp_item.setFlags(ltp_item.flags() & ~Qt.ItemIsEditable)
            ltp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, ltp_item)
            
            # Change
            change_item = QTableWidgetItem(format_currency(change) if ltp else "-")
            change_item.setFlags(change_item.flags() & ~Qt.ItemIsEditable)
            change_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if ltp:
                change_item.setForeground(Qt.GlobalColor.green if change >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 3, change_item)
            
            # Change %
            change_pct_item = QTableWidgetItem(format_percentage(change_pct) if ltp else "-")
            change_pct_item.setFlags(change_pct_item.flags() & ~Qt.ItemIsEditable)
            change_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if ltp:
                change_pct_item.setForeground(Qt.GlobalColor.green if change_pct >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 4, change_pct_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)
            
            trade_btn = QPushButton("Trade")
            trade_btn.setProperty("type", "success")
            trade_btn.setFixedHeight(28)
            trade_btn.setCursor(Qt.PointingHandCursor)
            trade_btn.clicked.connect(lambda checked, r=row: self._on_trade_symbol(r))
            actions_layout.addWidget(trade_btn)
            
            remove_btn = QPushButton(LABELS['remove'])
            remove_btn.setProperty("type", "danger")
            remove_btn.setFixedHeight(28)
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.clicked.connect(lambda checked, r=row: self._on_remove_symbol(r))
            actions_layout.addWidget(remove_btn)
            
            self.table.setCellWidget(row, 5, actions_widget)
        
        # Update summary
        self.item_count.setText(f"{len(items)} symbol{'s' if len(items) != 1 else ''}")
    
    def _subscribe_to_prices(self):
        """Subscribe to price updates for watchlist symbols"""
        if not self.websocket_service or not self.watchlist_items:
            return
        
        # Set up global callback for price updates
        self.websocket_service.set_global_callback(self._on_price_update)
        
        # Subscribe to each symbol
        for item in self.watchlist_items:
            from src.services.websocket_service import SubscriptionMode
            self.websocket_service.subscribe(
                item.symbol,
                item.exchange,
                SubscriptionMode.QUOTE
            )
        
        self._update_connection_status(True)
    
    def _on_price_update(self, data: dict):
        """Handle incoming price update"""
        symbol = data.get('symbol', '')
        exchange = data.get('exchange', '')
        
        if not symbol or not exchange:
            return
        
        key = f"{symbol}:{exchange}"
        
        # Update price data
        self.price_data[key] = {
            'ltp': data.get('ltp', 0),
            'change': data.get('change', 0),
            'change_percent': data.get('change_percent', 0),
        }
        
        # Update table row
        self._update_price_row(symbol, exchange)
    
    def _update_price_row(self, symbol: str, exchange: str):
        """Update a specific row with new price data"""
        key = f"{symbol}:{exchange}"
        price_info = self.price_data.get(key, {})
        
        # Find the row for this symbol
        for row, item in enumerate(self.watchlist_items):
            if item.symbol == symbol and item.exchange == exchange:
                ltp = price_info.get('ltp', 0)
                change = price_info.get('change', 0)
                change_pct = price_info.get('change_percent', 0)
                
                # Update LTP
                ltp_item = self.table.item(row, 2)
                if ltp_item:
                    ltp_item.setText(format_currency(ltp))
                
                # Update Change
                change_item = self.table.item(row, 3)
                if change_item:
                    change_item.setText(format_currency(change))
                    change_item.setForeground(Qt.GlobalColor.green if change >= 0 else Qt.GlobalColor.red)
                
                # Update Change %
                change_pct_item = self.table.item(row, 4)
                if change_pct_item:
                    change_pct_item.setText(format_percentage(change_pct))
                    change_pct_item.setForeground(Qt.GlobalColor.green if change_pct >= 0 else Qt.GlobalColor.red)
                
                break
    
    def _update_connection_status(self, connected: bool):
        """Update connection status indicator"""
        self.is_connected = connected
        if connected:
            self.status_dot.setStyleSheet(f"color: {COLORS['success']};")
            self.status_label.setText("Live")
        else:
            self.status_dot.setStyleSheet(f"color: {COLORS['error']};")
            self.status_label.setText("Disconnected")
    
    def set_user_id(self, user_id: int):
        """Set the user ID"""
        self.user_id = user_id
    
    def set_watchlist_service(self, watchlist_service):
        """Set the watchlist service"""
        self.watchlist_service = watchlist_service
    
    def set_websocket_service(self, websocket_service):
        """Set the websocket service"""
        self.websocket_service = websocket_service
