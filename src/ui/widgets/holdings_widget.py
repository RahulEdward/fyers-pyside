"""Holdings widget for displaying portfolio holdings"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, get_profit_loss_color
from src.ui.utils import (
    LoadingOverlay, format_currency, format_quantity
)


class HoldingsWidget(QWidget):
    """Widget for displaying portfolio holdings"""
    
    refresh_requested = Signal()
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.holdings = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(LABELS['holdings'])
        title.setProperty("type", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        self.refresh_btn = QPushButton(LABELS['refresh'])
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Holdings table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Qty", "Avg Price", "Current Value", "P&L", "P&L %"
        ])
        
        # Table styling
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Summary row
        summary = QHBoxLayout()
        
        self.total_value_label = QLabel("Total Value: ₹0.00")
        self.total_value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary.addWidget(self.total_value_label)
        
        self.total_pnl_label = QLabel("Total P&L: ₹0.00")
        self.total_pnl_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary.addWidget(self.total_pnl_label)
        
        summary.addStretch()
        
        self.holding_count = QLabel("0 holdings")
        self.holding_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary.addWidget(self.holding_count)
        
        layout.addLayout(summary)
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
        self.load_holdings()
    
    def load_holdings(self):
        """Load holdings from trading service"""
        if not self.trading_service:
            return
        
        self.loading.show_loading("Loading holdings...")
        self.refresh_btn.setEnabled(False)
        
        try:
            from src.models.result import Ok, Err
            result = self.trading_service.get_holdings()
            
            if isinstance(result, Ok):
                self.update_holdings(result.value)
        except Exception:
            pass
        finally:
            self.loading.hide_loading()
            self.refresh_btn.setEnabled(True)
    
    def update_holdings(self, holdings: list):
        """Update the table with holdings data"""
        self.holdings = holdings
        self.table.setRowCount(len(holdings))
        
        total_value = 0
        total_pnl = 0
        
        for row, holding in enumerate(holdings):
            # Symbol
            symbol_item = QTableWidgetItem(holding.get('symbol', ''))
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, symbol_item)
            
            # Quantity
            qty = holding.get('quantity', 0)
            qty_item = QTableWidgetItem(format_quantity(qty))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, qty_item)
            
            # Avg Price
            avg_price = holding.get('avg_price', 0)
            avg_item = QTableWidgetItem(format_currency(avg_price))
            avg_item.setFlags(avg_item.flags() & ~Qt.ItemIsEditable)
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, avg_item)
            
            # Current Value
            current_value = holding.get('current_value', 0)
            total_value += current_value
            value_item = QTableWidgetItem(format_currency(current_value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            value_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, value_item)
            
            # P&L
            pnl = holding.get('pnl', 0)
            total_pnl += pnl
            pnl_item = QTableWidgetItem(format_currency(pnl))
            pnl_item.setFlags(pnl_item.flags() & ~Qt.ItemIsEditable)
            pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_item.setForeground(Qt.GlobalColor.green if pnl >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 4, pnl_item)
            
            # P&L %
            pnl_pct = holding.get('pnl_percent', 0)
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            pnl_pct_item.setFlags(pnl_pct_item.flags() & ~Qt.ItemIsEditable)
            pnl_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_pct_item.setForeground(Qt.GlobalColor.green if pnl_pct >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 5, pnl_pct_item)
        
        # Update summary
        self.total_value_label.setText(f"Total Value: {format_currency(total_value)}")
        self.total_pnl_label.setText(f"Total P&L: {format_currency(total_pnl)}")
        self.total_pnl_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {get_profit_loss_color(total_pnl)};"
        )
        self.holding_count.setText(f"{len(holdings)} holding{'s' if len(holdings) != 1 else ''}")
    
    def set_trading_service(self, trading_service):
        """Set the trading service"""
        self.trading_service = trading_service
