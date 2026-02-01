"""Positions widget for displaying open positions"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QHeaderView
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, get_profit_loss_color
from src.ui.utils import (
    LoadingOverlay, format_currency, format_quantity,
    show_confirm_dialog
)


class PositionsWidget(QWidget):
    """Widget for displaying and managing open positions"""
    
    refresh_requested = Signal()
    close_position_requested = Signal(dict)  # Emits position data
    close_all_requested = Signal()
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.positions = []
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel(LABELS['positions'])
        title.setProperty("type", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        self.close_all_btn = QPushButton(LABELS['close_all'])
        self.close_all_btn.setProperty("type", "danger")
        self.close_all_btn.clicked.connect(self._on_close_all)
        self.close_all_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.close_all_btn)
        
        self.refresh_btn = QPushButton(LABELS['refresh'])
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Positions table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Symbol", "Qty", "Avg Price", "LTP", "P&L", "P&L %", "Action"
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
        
        self.total_pnl_label = QLabel("Total P&L: ₹0.00")
        self.total_pnl_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary.addWidget(self.total_pnl_label)
        
        summary.addStretch()
        
        self.position_count = QLabel("0 positions")
        self.position_count.setStyleSheet(f"color: {COLORS['text_secondary']};")
        summary.addWidget(self.position_count)
        
        layout.addLayout(summary)
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
        self.load_positions()
    
    def _on_close_all(self):
        """Handle close all button click"""
        if not self.positions:
            return
        
        if show_confirm_dialog(
            self,
            "Close All Positions",
            f"Are you sure you want to close all {len(self.positions)} positions?"
        ):
            self.close_all_requested.emit()
    
    def _on_close_position(self, row: int):
        """Handle close position button click"""
        if row < len(self.positions):
            position = self.positions[row]
            if show_confirm_dialog(
                self,
                "Close Position",
                f"Close position for {position.get('symbol', 'Unknown')}?"
            ):
                self.close_position_requested.emit(position)
    
    def load_positions(self):
        """Load positions from trading service"""
        if not self.trading_service:
            return
        
        self.loading.show_loading("Loading positions...")
        self.refresh_btn.setEnabled(False)
        
        try:
            from src.models.result import Ok, Err
            result = self.trading_service.get_positions()
            
            if isinstance(result, Ok):
                self.update_positions(result.value)
        except Exception:
            pass
        finally:
            self.loading.hide_loading()
            self.refresh_btn.setEnabled(True)
    
    def update_positions(self, positions: list):
        """Update the table with positions data"""
        self.positions = positions
        self.table.setRowCount(len(positions))
        
        total_pnl = 0
        
        for row, pos in enumerate(positions):
            # Symbol
            symbol_item = QTableWidgetItem(pos.get('symbol', ''))
            symbol_item.setFlags(symbol_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, symbol_item)
            
            # Quantity
            qty = pos.get('quantity', 0)
            qty_item = QTableWidgetItem(format_quantity(qty))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, qty_item)
            
            # Avg Price
            avg_price = pos.get('avg_price', 0)
            avg_item = QTableWidgetItem(format_currency(avg_price))
            avg_item.setFlags(avg_item.flags() & ~Qt.ItemIsEditable)
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, avg_item)
            
            # LTP
            ltp = pos.get('ltp', 0)
            ltp_item = QTableWidgetItem(format_currency(ltp))
            ltp_item.setFlags(ltp_item.flags() & ~Qt.ItemIsEditable)
            ltp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, ltp_item)
            
            # P&L
            pnl = pos.get('pnl', 0)
            total_pnl += pnl
            pnl_item = QTableWidgetItem(format_currency(pnl))
            pnl_item.setFlags(pnl_item.flags() & ~Qt.ItemIsEditable)
            pnl_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_item.setForeground(Qt.GlobalColor.green if pnl >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 4, pnl_item)
            
            # P&L %
            pnl_pct = pos.get('pnl_percent', 0)
            pnl_pct_item = QTableWidgetItem(f"{pnl_pct:+.2f}%")
            pnl_pct_item.setFlags(pnl_pct_item.flags() & ~Qt.ItemIsEditable)
            pnl_pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pnl_pct_item.setForeground(Qt.GlobalColor.green if pnl_pct >= 0 else Qt.GlobalColor.red)
            self.table.setItem(row, 5, pnl_pct_item)
            
            # Close button
            close_btn = QPushButton(LABELS['close'])
            close_btn.setProperty("type", "danger")
            close_btn.setCursor(Qt.PointingHandCursor)
            close_btn.clicked.connect(lambda checked, r=row: self._on_close_position(r))
            self.table.setCellWidget(row, 6, close_btn)
        
        # Update summary
        self.total_pnl_label.setText(f"Total P&L: {format_currency(total_pnl)}")
        self.total_pnl_label.setStyleSheet(
            f"font-weight: bold; font-size: 14px; color: {get_profit_loss_color(total_pnl)};"
        )
        self.position_count.setText(f"{len(positions)} position{'s' if len(positions) != 1 else ''}")
        
        # Enable/disable close all button
        self.close_all_btn.setEnabled(len(positions) > 0)
    
    def set_trading_service(self, trading_service):
        """Set the trading service"""
        self.trading_service = trading_service
