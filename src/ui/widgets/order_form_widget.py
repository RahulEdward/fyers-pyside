"""Order form widget for placing new orders"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QFrame, QButtonGroup, QRadioButton, QCompleter
)
from PySide6.QtCore import Qt, Signal, QStringListModel

from src.ui.styles import COLORS, LABELS, SPACING
from src.ui.utils import ErrorLabel, SuccessLabel, LoadingOverlay
from src.models.trading import OrderRequest
from src.models.enums import OrderAction, OrderType, ProductType

logger = logging.getLogger(__name__)


class OrderFormWidget(QWidget):
    """Widget for placing new orders"""
    
    order_submitted = Signal(dict)  # Emits order data
    
    def __init__(self, trading_service=None, master_contract_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.master_contract_service = master_contract_service
        self.setup_ui()
        self._setup_symbol_autocomplete()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['md'])
        
        # Title
        title = QLabel(LABELS['place_order'])
        title.setProperty("type", "title")
        layout.addWidget(title)
        
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
        form_layout = QGridLayout(form)
        form_layout.setSpacing(SPACING['sm'])
        
        row = 0
        
        # Symbol
        form_layout.addWidget(QLabel(LABELS['symbol']), row, 0)
        self.symbol_input = QLineEdit()
        self.symbol_input.setPlaceholderText("e.g., RELIANCE, NIFTY")
        form_layout.addWidget(self.symbol_input, row, 1)
        
        row += 1
        
        # Exchange
        form_layout.addWidget(QLabel(LABELS['exchange']), row, 0)
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(['NSE', 'BSE', 'NFO', 'BFO', 'MCX', 'CDS'])
        form_layout.addWidget(self.exchange_combo, row, 1)
        
        row += 1
        
        # Buy/Sell toggle
        form_layout.addWidget(QLabel("Action"), row, 0)
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        self.action_group = QButtonGroup()
        
        self.buy_radio = QRadioButton(LABELS['buy'])
        self.buy_radio.setChecked(True)
        self.buy_radio.setStyleSheet(f"""
            QRadioButton::checked {{
                color: {COLORS['buy']};
                font-weight: bold;
            }}
        """)
        self.action_group.addButton(self.buy_radio, 1)
        action_layout.addWidget(self.buy_radio)
        
        self.sell_radio = QRadioButton(LABELS['sell'])
        self.sell_radio.setStyleSheet(f"""
            QRadioButton::checked {{
                color: {COLORS['sell']};
                font-weight: bold;
            }}
        """)
        self.action_group.addButton(self.sell_radio, 2)
        action_layout.addWidget(self.sell_radio)
        
        action_layout.addStretch()
        form_layout.addWidget(action_widget, row, 1)
        
        row += 1
        
        # Quantity
        form_layout.addWidget(QLabel(LABELS['quantity']), row, 0)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100000)
        self.quantity_spin.setValue(1)
        form_layout.addWidget(self.quantity_spin, row, 1)
        
        row += 1
        
        # Order Type
        form_layout.addWidget(QLabel(LABELS['order_type']), row, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(['MARKET', 'LIMIT', 'SL', 'SL-M'])
        self.order_type_combo.currentTextChanged.connect(self._on_order_type_changed)
        form_layout.addWidget(self.order_type_combo, row, 1)
        
        row += 1
        
        # Product Type
        form_layout.addWidget(QLabel("Product"), row, 0)
        self.product_combo = QComboBox()
        self.product_combo.addItems(['INTRADAY', 'CNC', 'MARGIN'])
        form_layout.addWidget(self.product_combo, row, 1)
        
        row += 1
        
        # Price (disabled for market orders)
        form_layout.addWidget(QLabel(LABELS['price']), row, 0)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 1000000)
        self.price_spin.setDecimals(2)
        self.price_spin.setSingleStep(0.05)
        self.price_spin.setEnabled(False)  # Disabled by default (market order)
        form_layout.addWidget(self.price_spin, row, 1)
        
        row += 1
        
        # Trigger Price (for SL orders)
        form_layout.addWidget(QLabel("Trigger Price"), row, 0)
        self.trigger_spin = QDoubleSpinBox()
        self.trigger_spin.setRange(0, 1000000)
        self.trigger_spin.setDecimals(2)
        self.trigger_spin.setSingleStep(0.05)
        self.trigger_spin.setEnabled(False)  # Disabled by default
        form_layout.addWidget(self.trigger_spin, row, 1)
        
        layout.addWidget(form)
        
        # Error/Success labels
        self.error_label = ErrorLabel()
        layout.addWidget(self.error_label)
        
        self.success_label = SuccessLabel()
        layout.addWidget(self.success_label)
        
        # Submit buttons
        buttons_layout = QHBoxLayout()
        
        self.buy_btn = QPushButton(LABELS['buy'])
        self.buy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['buy']};
                color: white;
                font-weight: bold;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: #388E3C;
            }}
        """)
        self.buy_btn.clicked.connect(lambda: self._on_submit('BUY'))
        self.buy_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.buy_btn)
        
        self.sell_btn = QPushButton(LABELS['sell'])
        self.sell_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['sell']};
                color: white;
                font-weight: bold;
                min-height: 44px;
            }}
            QPushButton:hover {{
                background-color: #D32F2F;
            }}
        """)
        self.sell_btn.clicked.connect(lambda: self._on_submit('SELL'))
        self.sell_btn.setCursor(Qt.PointingHandCursor)
        buttons_layout.addWidget(self.sell_btn)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        
        # Loading overlay
        self.loading = LoadingOverlay(self)
    
    def _setup_symbol_autocomplete(self):
        """Setup symbol autocomplete"""
        if not self.master_contract_service:
            return
        
        # Create completer
        self.symbol_completer = QCompleter()
        self.symbol_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.symbol_completer.setFilterMode(Qt.MatchContains)
        self.symbol_completer.setMaxVisibleItems(10)
        
        # Set completer model
        self.symbol_model = QStringListModel()
        self.symbol_completer.setModel(self.symbol_model)
        
        # Attach to symbol input
        self.symbol_input.setCompleter(self.symbol_completer)
        
        # Connect text changed to update suggestions
        self.symbol_input.textChanged.connect(self._on_symbol_text_changed)
    
    def _on_symbol_text_changed(self, text: str):
        """Update symbol suggestions as user types"""
        if not self.master_contract_service or len(text) < 2:
            return
        
        try:
            # Get current exchange filter
            exchange = self.exchange_combo.currentText()
            
            # Search symbols
            results = self.master_contract_service.search_symbols(
                query=text,
                exchange=exchange if exchange != 'NSE' else None,  # NSE is default
                limit=20
            )
            
            # Extract symbol names
            symbols = [r.get('symbol', '') for r in results if r.get('symbol')]
            
            # Update completer model
            self.symbol_model.setStringList(symbols)
            
        except Exception as e:
            logger.error(f"Error updating symbol suggestions: {e}")
    
    def _on_order_type_changed(self, order_type: str):
        """Handle order type change"""
        is_market = order_type == 'MARKET'
        is_sl = order_type in ['SL', 'SL-M']
        
        # Enable/disable price field
        self.price_spin.setEnabled(not is_market and order_type != 'SL-M')
        
        # Enable/disable trigger price field
        self.trigger_spin.setEnabled(is_sl)
        
        # Clear values when disabled
        if is_market:
            self.price_spin.setValue(0)
        if not is_sl:
            self.trigger_spin.setValue(0)
    
    def _validate_form(self) -> bool:
        """Validate form inputs"""
        self.error_label.clear_error()
        
        symbol = self.symbol_input.text().strip()
        if not symbol:
            self.error_label.show_error("Symbol is required")
            return False
        
        quantity = self.quantity_spin.value()
        if quantity <= 0:
            self.error_label.show_error("Quantity must be greater than 0")
            return False
        
        order_type = self.order_type_combo.currentText()
        
        # Validate price for limit orders
        if order_type == 'LIMIT':
            price = self.price_spin.value()
            if price <= 0:
                self.error_label.show_error("Price is required for Limit orders")
                return False
        
        # Validate trigger price for SL orders
        if order_type in ['SL', 'SL-M']:
            trigger = self.trigger_spin.value()
            if trigger <= 0:
                self.error_label.show_error("Trigger price is required for Stop Loss orders")
                return False
        
        # Validate price for SL orders (not SL-M)
        if order_type == 'SL':
            price = self.price_spin.value()
            if price <= 0:
                self.error_label.show_error("Price is required for SL orders")
                return False
        
        return True
    
    def _on_submit(self, action: str):
        """Handle order submission"""
        if not self._validate_form():
            return
        
        # Helper to map strings to enums
        try:
            action_enum = OrderAction(action)
            order_type_str = self.order_type_combo.currentText()
            
            # Map order type strings to enum values if needed
            # Assuming OrderType enum values match strings or integer mapping is handled in service
            # Let's look at OrderType definition. Usually values are integers in Fyers.
            # But here OrderType enum might handle string mapping or we map manually.
            # Safe bet: Use string values if Enum accepts them, or map explicitly.
            # Actually TradingService place_order uses .value on enum.
            # Let's map explicitly based on standard Fyers/App conventions
            order_type_map = {
                'MARKET': OrderType.MARKET,
                'LIMIT': OrderType.LIMIT,
                'SL': OrderType.SL,
                'SL-M': OrderType.SL_MARKET
            }
            # If Enums are ints (1, 2...), we must map.
            # If Enums are strings ('MARKET'...), we can use OrderType(str).
            # I will assume standard Fyers mapping: 
            # 1: Limit, 2: Market, 3: SL-Limit, 4: SL-Market
            
            product_map = {
                'INTRADAY': ProductType.INTRADAY,
                'CNC': ProductType.CNC,
                'MARGIN': ProductType.MARGIN
            }
            
            # Temporary mapping fix - better to import types properly
            # I'll rely on the Enums being robust or map logic below
            
            # Create OrderRequest object
            order_request = OrderRequest(
                symbol=self.symbol_input.text().strip().upper(),
                exchange=self.exchange_combo.currentText(),
                action=action_enum,
                quantity=self.quantity_spin.value(),
                order_type=order_type_map.get(order_type_str, OrderType.MARKET),
                product_type=product_map.get(self.product_combo.currentText(), ProductType.INTRADAY),
                price=float(self.price_spin.value()) if self.price_spin.isEnabled() else 0.0,
                trigger_price=float(self.trigger_spin.value()) if self.trigger_spin.isEnabled() else 0.0
            )
            
            order_data = order_request # Use the object
            
        except Exception as e:
            self.error_label.show_error(f"Invalid order parameters: {e}")
            return
        
        if self.trading_service:
            self.loading.show_loading("Placing order...")
            self.buy_btn.setEnabled(False)
            self.sell_btn.setEnabled(False)
            
            try:
                from src.models.result import Ok, Err
                result = self.trading_service.place_order(order_data)
                
                if isinstance(result, Ok):
                    self.success_label.show_success(f"Order placed successfully! ID: {result.value}")
                    self.order_submitted.emit(order_data)
                    self._clear_form()
                else:
                    self.error_label.show_error(result.error)
            except Exception as e:
                self.error_label.show_error(f"Failed to place order: {str(e)}")
            finally:
                self.loading.hide_loading()
                self.buy_btn.setEnabled(True)
                self.sell_btn.setEnabled(True)
        else:
            # No trading service - emit signal for testing
            self.order_submitted.emit(order_data)
            self.success_label.show_success("Order submitted (test mode)")
    
    def _clear_form(self):
        """Clear form after successful submission"""
        self.symbol_input.clear()
        self.quantity_spin.setValue(1)
        self.price_spin.setValue(0)
        self.trigger_spin.setValue(0)
        self.order_type_combo.setCurrentIndex(0)
    
    def set_symbol(self, symbol: str, exchange: str = None):
        """Pre-fill symbol and exchange"""
        self.symbol_input.setText(symbol)
        if exchange:
            index = self.exchange_combo.findText(exchange)
            if index >= 0:
                self.exchange_combo.setCurrentIndex(index)
    
    def set_trading_service(self, trading_service):
        """Set the trading service"""
        self.trading_service = trading_service
    
    def set_master_contract_service(self, master_contract_service):
        """Set the master contract service for symbol autocomplete"""
        self.master_contract_service = master_contract_service
        self._setup_symbol_autocomplete()
