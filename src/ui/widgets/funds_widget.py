"""Funds widget for displaying account balance and margin information"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from src.ui.styles import COLORS, LABELS, SPACING, get_profit_loss_color
from src.ui.utils import (
    LoadingOverlay, format_currency
)


class FundsWidget(QWidget):
    """Widget for displaying account funds and margin information"""
    
    refresh_requested = Signal()
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Header with refresh button
        header = QHBoxLayout()
        
        title = QLabel(LABELS['funds'])
        title.setProperty("type", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        self.refresh_btn = QPushButton(LABELS['refresh'])
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(self.refresh_btn)
        
        layout.addLayout(header)
        
        # Funds cards container
        cards_layout = QGridLayout()
        cards_layout.setSpacing(SPACING['md'])
        
        # Available Cash card
        self.cash_card = self._create_card("Available Cash", "₹0.00")
        cards_layout.addWidget(self.cash_card, 0, 0)
        
        # Collateral card
        self.collateral_card = self._create_card("Collateral", "₹0.00")
        cards_layout.addWidget(self.collateral_card, 0, 1)
        
        # Utilized Margin card
        self.margin_card = self._create_card("Utilized Margin", "₹0.00")
        cards_layout.addWidget(self.margin_card, 1, 0)
        
        # Available Margin card
        self.available_margin_card = self._create_card("Available Margin", "₹0.00")
        cards_layout.addWidget(self.available_margin_card, 1, 1)
        
        layout.addLayout(cards_layout)
        
        # P&L Section
        pnl_frame = QFrame()
        pnl_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: {SPACING['md']}px;
            }}
        """)
        pnl_layout = QHBoxLayout(pnl_frame)
        
        # Realized P&L
        realized_layout = QVBoxLayout()
        realized_label = QLabel("Realized P&L")
        realized_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        realized_layout.addWidget(realized_label)
        
        self.realized_pnl = QLabel("₹0.00")
        self.realized_pnl.setStyleSheet("font-size: 18px; font-weight: bold;")
        realized_layout.addWidget(self.realized_pnl)
        pnl_layout.addLayout(realized_layout)
        
        pnl_layout.addStretch()
        
        # Unrealized P&L
        unrealized_layout = QVBoxLayout()
        unrealized_label = QLabel("Unrealized P&L")
        unrealized_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        unrealized_layout.addWidget(unrealized_label)
        
        self.unrealized_pnl = QLabel("₹0.00")
        self.unrealized_pnl.setStyleSheet("font-size: 18px; font-weight: bold;")
        unrealized_layout.addWidget(self.unrealized_pnl)
        pnl_layout.addLayout(unrealized_layout)
        
        pnl_layout.addStretch()
        
        # Total P&L
        total_layout = QVBoxLayout()
        total_label = QLabel("Total P&L")
        total_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        total_layout.addWidget(total_label)
        
        self.total_pnl = QLabel("₹0.00")
        self.total_pnl.setStyleSheet("font-size: 20px; font-weight: bold;")
        total_layout.addWidget(self.total_pnl)
        pnl_layout.addLayout(total_layout)
        
        layout.addWidget(pnl_frame)
        
        layout.addStretch()
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _create_card(self, title: str, value: str) -> QFrame:
        """Create a funds card widget"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: {SPACING['md']}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(SPACING['xs'])
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        value_label.setObjectName("value")
        layout.addWidget(value_label)
        
        return card
    
    def _update_card_value(self, card: QFrame, value: float):
        """Update the value in a card"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(format_currency(value))
    
    def _on_refresh(self):
        """Handle refresh button click"""
        self.refresh_requested.emit()
        self.load_funds()
    
    def load_funds(self):
        """Load funds data from trading service"""
        if not self.trading_service:
            return
        
        self.loading.show_loading("Loading funds...")
        self.refresh_btn.setEnabled(False)
        
        try:
            from src.models.result import Ok, Err
            result = self.trading_service.get_funds()
            
            if isinstance(result, Ok):
                self.update_funds(result.value)
            else:
                # Show error state
                pass
        except Exception as e:
            pass
        finally:
            self.loading.hide_loading()
            self.refresh_btn.setEnabled(True)
    
    def update_funds(self, funds_data: dict):
        """Update the display with funds data"""
        # Update cards
        self._update_card_value(self.cash_card, funds_data.get('available_cash', 0))
        self._update_card_value(self.collateral_card, funds_data.get('collateral', 0))
        self._update_card_value(self.margin_card, funds_data.get('utilized_margin', 0))
        self._update_card_value(self.available_margin_card, funds_data.get('available_margin', 0))
        
        # Update P&L
        realized = funds_data.get('realized_pnl', 0)
        unrealized = funds_data.get('unrealized_pnl', 0)
        total = realized + unrealized
        
        self.realized_pnl.setText(format_currency(realized))
        self.realized_pnl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {get_profit_loss_color(realized)};")
        
        self.unrealized_pnl.setText(format_currency(unrealized))
        self.unrealized_pnl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {get_profit_loss_color(unrealized)};")
        
        self.total_pnl.setText(format_currency(total))
        self.total_pnl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {get_profit_loss_color(total)};")
    
    def set_trading_service(self, trading_service):
        """Set the trading service"""
        self.trading_service = trading_service
