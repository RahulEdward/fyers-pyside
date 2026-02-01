"""UI styles and theming for the trading application - Modern Dark Theme"""

# Color palette - Modern Dark Trading Theme
COLORS = {
    # Primary colors
    'primary': '#00D09C',        # Zerodha-like green
    'primary_dark': '#00B386',
    'primary_light': '#1A3D32',
    
    # Secondary colors
    'secondary': '#5B6EFF',
    'secondary_dark': '#4A5AE0',
    
    # Status colors
    'success': '#00D09C',
    'error': '#FF5252',
    'warning': '#FFB74D',
    'info': '#64B5F6',
    
    # Trading colors
    'buy': '#00D09C',      # Green for buy
    'sell': '#FF5252',     # Red for sell
    'profit': '#00D09C',   # Green for profit
    'loss': '#FF5252',     # Red for loss
    
    # Background colors - Dark theme
    'background': '#131722',      # Main dark background
    'background_dark': '#0D1117',
    'surface': '#1E222D',         # Card/panel background
    'surface_light': '#2A2E39',   # Lighter surface
    
    # Text colors
    'text_primary': '#E0E0E0',
    'text_secondary': '#9E9E9E',
    'text_disabled': '#616161',
    'text_on_primary': '#FFFFFF',
    
    # Border colors
    'border': '#2A2E39',
    'border_focus': '#00D09C',
    
    # Table colors
    'table_header': '#1E222D',
    'table_row_alt': '#1A1E29',
    'table_row_hover': '#2A3441',
}

# Font settings
FONTS = {
    'family': 'Segoe UI, Roboto, Arial, sans-serif',
    'size_small': 11,
    'size_normal': 13,
    'size_large': 15,
    'size_title': 18,
    'size_header': 22,
}

# Spacing
SPACING = {
    'xs': 4,
    'sm': 8,
    'md': 16,
    'lg': 24,
    'xl': 32,
}

# Border radius
BORDER_RADIUS = {
    'sm': 4,
    'md': 8,
    'lg': 12,
}


# Main application stylesheet - Modern Dark Theme
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    font-family: {FONTS['family']};
    font-size: {FONTS['size_normal']}px;
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QPushButton {{
    background-color: {COLORS['primary']};
    color: {COLORS['background']};
    border: none;
    border-radius: {BORDER_RADIUS['md']}px;
    padding: 10px 20px;
    font-weight: 600;
    min-height: 40px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_dark']};
}}

QPushButton:disabled {{
    background-color: {COLORS['surface_light']};
    color: {COLORS['text_disabled']};
}}

QPushButton[type="secondary"] {{
    background-color: {COLORS['surface_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[type="secondary"]:hover {{
    background-color: {COLORS['surface']};
    border-color: {COLORS['primary']};
}}

QPushButton[type="buy"] {{
    background-color: {COLORS['buy']};
    color: {COLORS['background']};
}}

QPushButton[type="sell"] {{
    background-color: {COLORS['sell']};
    color: white;
}}

QPushButton[type="danger"] {{
    background-color: {COLORS['error']};
    color: white;
}}

QLineEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['sm']}px;
    padding: 10px 12px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    min-height: 40px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['primary']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['background_dark']};
    color: {COLORS['text_disabled']};
}}

QLineEdit::placeholder {{
    color: {COLORS['text_disabled']};
}}

QComboBox {{
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['sm']}px;
    padding: 10px 12px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    min-height: 40px;
}}

QComboBox:focus {{
    border-color: {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['primary_light']};
    color: {COLORS['text_primary']};
}}

QLabel {{
    color: {COLORS['text_primary']};
    background-color: transparent;
}}

QLabel[type="error"] {{
    color: {COLORS['error']};
    font-size: {FONTS['size_small']}px;
}}

QLabel[type="success"] {{
    color: {COLORS['success']};
}}

QLabel[type="title"] {{
    font-size: {FONTS['size_title']}px;
    font-weight: bold;
}}

QLabel[type="header"] {{
    font-size: {FONTS['size_header']}px;
    font-weight: bold;
}}

QLabel[type="secondary"] {{
    color: {COLORS['text_secondary']};
}}

QTableWidget {{
    border: none;
    gridline-color: {COLORS['border']};
    background-color: {COLORS['surface']};
    alternate-background-color: {COLORS['table_row_alt']};
    selection-background-color: {COLORS['table_row_hover']};
    border-radius: {BORDER_RADIUS['md']}px;
}}

QTableWidget::item {{
    padding: 12px 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['table_row_hover']};
    color: {COLORS['text_primary']};
}}

QHeaderView::section {{
    background-color: {COLORS['surface']};
    padding: 12px 8px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    font-weight: 600;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    font-size: {FONTS['size_small']}px;
}}

QTabWidget::pane {{
    border: none;
    background-color: {COLORS['surface']};
    border-radius: {BORDER_RADIUS['md']}px;
}}

QTabBar::tab {{
    background-color: transparent;
    padding: 12px 24px;
    border: none;
    color: {COLORS['text_secondary']};
    font-weight: 500;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    color: {COLORS['primary']};
    border-bottom: 3px solid {COLORS['primary']};
}}

QTabBar::tab:hover {{
    color: {COLORS['text_primary']};
}}

QScrollBar:vertical {{
    border: none;
    background-color: {COLORS['background']};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['surface_light']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['text_disabled']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: {COLORS['background']};
    height: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['surface_light']};
    border-radius: 4px;
    min-width: 30px;
}}

QProgressBar {{
    border: none;
    border-radius: {BORDER_RADIUS['sm']}px;
    text-align: center;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: {BORDER_RADIUS['sm']}px;
}}

QSpinBox, QDoubleSpinBox {{
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['sm']}px;
    padding: 10px 12px;
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    min-height: 40px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['primary']};
}}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background-color: {COLORS['surface_light']};
    border: none;
    width: 20px;
}}

QFrame {{
    background-color: transparent;
}}

QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['md']}px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
}}

QToolTip {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: {BORDER_RADIUS['sm']}px;
    padding: 8px;
}}
"""


# English labels
LABELS = {
    # Authentication
    'login': 'Login',
    'register': 'Register',
    'logout': 'Logout',
    'username': 'Username',
    'password': 'Password',
    'confirm_password': 'Confirm Password',
    'email': 'Email',
    
    # Broker
    'api_key': 'API Key',
    'api_secret': 'API Secret',
    'authenticate': 'Authenticate',
    'connected': 'Connected',
    'disconnected': 'Disconnected',
    
    # Trading
    'buy': 'BUY',
    'sell': 'SELL',
    'quantity': 'Quantity',
    'price': 'Price',
    'order_type': 'Order Type',
    'market': 'Market',
    'limit': 'Limit',
    'stop_loss': 'Stop Loss',
    'place_order': 'Place Order',
    'modify': 'Modify',
    'cancel': 'Cancel',
    
    # Dashboard
    'funds': 'Funds',
    'positions': 'Positions',
    'holdings': 'Holdings',
    'orders': 'Orders',
    'watchlist': 'Watchlist',
    
    # Status
    'loading': 'Loading...',
    'success': 'Success',
    'error': 'Error',
    'refresh': 'Refresh',
    
    # P&L
    'profit': 'Profit',
    'loss': 'Loss',
    'pnl': 'P&L',
    'total': 'Total',
    
    # Misc
    'search': 'Search',
    'add': 'Add',
    'remove': 'Remove',
    'close': 'Close',
    'close_all': 'Close All',
    'symbol': 'Symbol',
    'exchange': 'Exchange',
    'ltp': 'LTP',
    'change': 'Change',
}


def get_profit_loss_color(value: float) -> str:
    """Get color based on profit/loss value"""
    if value > 0:
        return COLORS['profit']
    elif value < 0:
        return COLORS['loss']
    return COLORS['text_primary']


def get_buy_sell_color(action: str) -> str:
    """Get color based on buy/sell action"""
    if action.upper() == 'BUY':
        return COLORS['buy']
    elif action.upper() == 'SELL':
        return COLORS['sell']
    return COLORS['text_primary']
