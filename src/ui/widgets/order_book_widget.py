"""Order book widget for displaying orders"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from src.ui.styles import COLORS, LABELS, SPACING
from src.ui.utils import (
    LoadingOverlay, format_currency, format_quantity, show_confirm_dialog
)


# Order status colors
STATUS_COLORS = {
    'PENDING': COLORS['warning'],
    'OPEN': COLORS['warning'],
    'COMPLETE': COLORS['success'],
    'FILLED': COLORS['success'],
    'REJECTED': COLORS['error'],
    'CANCELLED': COLORS['text_secondary'],
    'CANCELED': COLORS['text_secondary'],
}


class OrderBookWidget(QWidget):
    """Widget for displaying and managing orders"""
    
    refresh_requested = Signal()
    modify_order_requested = Signal(dict)  # Emits order data
    cancel_order_requested = Signal(dict)  # Emits order data
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.orders = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(LABELS['orders'])
        title.setProperty("type", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        self.refresh_btn = QPushButton(LABELS['refresh'])
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Orders table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Order ID", "Symbol", "Type", "Side", "Qty", "Price", "Status", "Actions"
        ])
        
        # Table styling
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Summary row
        summary = QHBoxLayout()
        
        self.order_count = QLabel("0 orders")
        self.order_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary.addWidget(self.order_count)
        
        summary.addStretch()
        
        self.pending_count = QLabel("0 pending")
        self.pending_count.setStyleSheet(f"color: {COLORS['warning']};")
        summary.addWidget(self.pending_count)
        
        layout.addLayout(summary)
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
        self.load_orders()
    
    def _on_modify_order(self, row: int):
        """Handle modify order button click"""
        if row < len(self.orders):
            self.modify_order_requested.emit(self.orders[row])
    
    def _on_cancel_order(self, row: int):
        """Handle cancel order button click"""
        if row < len(self.orders):
            order = self.orders[row]
            if show_confirm_dialog(
                self,
                "Cancel Order",
                f"Cancel order {order.get('order_id', '')}?"
            ):
                self.cancel_order_requested.emit(order)
    
    def load_orders(self):
        """Load orders from trading service"""
        if not self.trading_service:
            return
        
        self.loading.show_loading("Loading orders...")
        self.refresh_btn.setEnabled(False)
        
        try:
            from src.models.result import Ok, Err
            result = self.trading_service.get_order_book()
            
            if isinstance(result, Ok):
                self.update_orders(result.value)
        except Exception:
            pass
        finally:
            self.loading.hide_loading()
            self.refresh_btn.setEnabled(True)
    
    def update_orders(self, orders: list):
        """Update the table with orders data"""
        self.orders = orders
        self.table.setRowCount(len(orders))
        
        pending_count = 0
        
        for row, order in enumerate(orders):
            # Order ID
            order_id = str(order.get('order_id', ''))
            id_item = QTableWidgetItem(order_id[:12] + '...' if len(order_id) > 12 else order_id)
            id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
            id_item.setToolTip(order_id)
            self.table.setItem(row, 0, id_item)
            
            # Symbol
            symbol_item = QTableWidgetItem(order.get('symbol', ''))
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, symbol_item)
            
            # Type
            order_type = order.get('order_type', 'MARKET')
            type_item = QTableWidgetItem(order_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, type_item)
            
            # Side (Buy/Sell)
            side = order.get('side', 'BUY')
            side_item = QTableWidgetItem(side)
            side_item.setFlags(side_item.flags() & ~Qt.ItemIsEditable)
            side_color = COLORS['buy'] if side.upper() == 'BUY' else COLORS['sell']
            side_item.setForeground(QColor(side_color))
            self.table.setItem(row, 3, side_item)
            
            # Quantity
            qty = order.get('quantity', 0)
            qty_item = QTableWidgetItem(format_quantity(qty))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, qty_item)
            
            # Price
            price = order.get('price', 0)
            price_text = format_currency(price) if price > 0 else "Market"
            price_item = QTableWidgetItem(price_text)
            price_item.setFlags(price_item.flags() & ~Qt.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, price_item)
            
            # Status
            status = order.get('status', 'PENDING').upper()
            status_item = QTableWidgetItem(status)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            status_color = STATUS_COLORS.get(status, COLORS['text_primary'])
            status_item.setForeground(QColor(status_color))
            self.table.setItem(row, 6, status_item)
            
            # Track pending orders
            if status in ['PENDING', 'OPEN']:
                pending_count += 1
            
            # Actions (only for pending orders)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)
            
            if status in ['PENDING', 'OPEN']:
                modify_btn = QPushButton(LABELS['modify'])
                modify_btn.setFixedHeight(28)
                modify_btn.setCursor(Qt.PointingHandCursor)
                modify_btn.clicked.connect(lambda checked, r=row: self._on_modify_order(r))
                actions_layout.addWidget(modify_btn)
                
                cancel_btn = QPushButton(LABELS['cancel'])
                cancel_btn.setProperty("type", "danger")
                cancel_btn.setFixedHeight(28)
                cancel_btn.setCursor(Qt.PointingHandCursor)
                cancel_btn.clicked.connect(lambda checked, r=row: self._on_cancel_order(r))
                actions_layout.addWidget(cancel_btn)
            else:
                # Empty placeholder for completed/cancelled orders
                actions_layout.addStretch()
            
            self.table.setCellWidget(row, 7, actions_widget)
        
        # Update summary
        self.order_count.setText(f"{len(orders)} order{'s' if len(orders) != 1 else ''}")
        self.pending_count.setText(f"{pending_count} pending")
    
    def set_trading_service(self, trading_service):
        """Set the trading service"""
        self.trading_service = trading_service
