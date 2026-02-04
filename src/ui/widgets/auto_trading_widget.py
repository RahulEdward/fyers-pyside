"""Auto Trading Widget - Modern automated trading strategies interface"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QComboBox, QPushButton,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor

from src.ui.styles import COLORS, SPACING
from datetime import datetime
import random


class StrategyCard(QFrame):
    """Interactive strategy card with controls"""
    
    toggle_requested = Signal(str, bool)  # strategy_id, enabled
    configure_requested = Signal(str)  # strategy_id
    
    def __init__(self, strategy_id: str, name: str, description: str, 
                 icon: str = "🤖", is_active: bool = False, parent=None):
        super().__init__(parent)
        self.strategy_id = strategy_id
        self.name = name
        self.description = description
        self.icon = icon
        self.is_active = is_active
        self._is_hovered = False
        self.setup_ui()
        
    def setup_ui(self):
        self._update_style()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background: {COLORS['primary']}20;
            padding: 10px;
            border-radius: 12px;
        """)
        header.addWidget(icon_label)
        
        title_section = QVBoxLayout()
        title_section.setSpacing(2)
        
        title = QLabel(self.name)
        title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        title_section.addWidget(title)
        
        desc = QLabel(self.description)
        desc.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
        """)
        desc.setWordWrap(True)
        title_section.addWidget(desc)
        
        header.addLayout(title_section, stretch=1)
        
        # Status indicator
        self.status_dot = QLabel("●")
        self._update_status_indicator()
        header.addWidget(self.status_dot)
        
        layout.addLayout(header)
        
        # Stats row
        stats = QHBoxLayout()
        stats.setSpacing(SPACING['lg'])
        
        self.trades_stat = self._create_stat("Trades", "0")
        stats.addLayout(self.trades_stat)
        
        self.pnl_stat = self._create_stat("P&L", "₹0")
        stats.addLayout(self.pnl_stat)
        
        self.win_rate_stat = self._create_stat("Win Rate", "0%")
        stats.addLayout(self.win_rate_stat)
        
        stats.addStretch()
        layout.addLayout(stats)
        
        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(SPACING['sm'])
        
        self.toggle_btn = QPushButton("Start" if not self.is_active else "Stop")
        self.toggle_btn.setStyleSheet(self._get_toggle_style())
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self._on_toggle)
        actions.addWidget(self.toggle_btn)
        
        config_btn = QPushButton("⚙ Configure")
        config_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface_light']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        config_btn.setCursor(Qt.PointingHandCursor)
        config_btn.clicked.connect(lambda: self.configure_requested.emit(self.strategy_id))
        actions.addWidget(config_btn)
        
        actions.addStretch()
        layout.addLayout(actions)
    
    def _create_stat(self, label: str, value: str):
        """Create a stat display"""
        layout = QVBoxLayout()
        layout.setSpacing(2)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        value_label.setObjectName(f"{label}_value")
        layout.addWidget(value_label)
        
        label_text = QLabel(label)
        label_text.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
        """)
        layout.addWidget(label_text)
        
        return layout
    
    def _get_toggle_style(self):
        """Get toggle button style based on state"""
        if self.is_active:
            return f"""
                QPushButton {{
                    background: {COLORS['error']};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: #D93232;
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {COLORS['success']}, stop:1 #00B386);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 24px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {COLORS['success']};
                }}
            """
    
    def _update_style(self):
        """Update card style"""
        border_color = COLORS['primary'] if self._is_hovered else COLORS['border']
        if self.is_active:
            border_color = COLORS['success']
        
        self.setStyleSheet(f"""
            StrategyCard {{
                background: {COLORS['surface']};
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
        """)
    
    def _update_status_indicator(self):
        """Update status indicator"""
        if self.is_active:
            self.status_dot.setStyleSheet(f"""
                color: {COLORS['success']};
                font-size: 20px;
            """)
        else:
            self.status_dot.setStyleSheet(f"""
                color: {COLORS['text_disabled']};
                font-size: 20px;
            """)
    
    def _on_toggle(self):
        """Handle toggle button"""
        self.is_active = not self.is_active
        self.toggle_btn.setText("Stop" if self.is_active else "Start")
        self.toggle_btn.setStyleSheet(self._get_toggle_style())
        self._update_style()
        self._update_status_indicator()
        self.toggle_requested.emit(self.strategy_id, self.is_active)
    
    def enterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        
    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
    
    def update_stats(self, trades: int, pnl: float, win_rate: float):
        """Update strategy statistics"""
        trades_val = self.findChild(QLabel, "Trades_value")
        if trades_val:
            trades_val.setText(str(trades))
        
        pnl_val = self.findChild(QLabel, "P&L_value")
        if pnl_val:
            sign = "+" if pnl >= 0 else ""
            color = COLORS['success'] if pnl >= 0 else COLORS['error']
            pnl_val.setText(f"{sign}₹{pnl:,.0f}")
            pnl_val.setStyleSheet(f"""
                font-size: 18px;
                font-weight: bold;
                color: {color};
            """)
        
        win_val = self.findChild(QLabel, "Win Rate_value")
        if win_val:
            win_val.setText(f"{win_rate:.0f}%")


class SignalLogRow(QFrame):
    """A single signal log entry"""
    
    def __init__(self, timestamp: str, symbol: str, action: str, 
                 price: float, status: str, parent=None):
        super().__init__(parent)
        self.setup_ui(timestamp, symbol, action, price, status)
    
    def setup_ui(self, timestamp, symbol, action, price, status):
        self.setStyleSheet(f"""
            SignalLogRow {{
                background: {COLORS['surface_light']};
                border-radius: 8px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)
        
        # Timestamp
        time_label = QLabel(timestamp)
        time_label.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            font-family: monospace;
        """)
        time_label.setFixedWidth(80)
        layout.addWidget(time_label)
        
        # Symbol
        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet(f"""
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        symbol_label.setFixedWidth(100)
        layout.addWidget(symbol_label)
        
        # Action
        action_color = COLORS['success'] if action == "BUY" else COLORS['error']
        action_label = QLabel(action)
        action_label.setStyleSheet(f"""
            font-weight: bold;
            color: {action_color};
            background: {action_color}20;
            padding: 4px 12px;
            border-radius: 4px;
        """)
        action_label.setFixedWidth(60)
        layout.addWidget(action_label)
        
        # Price
        price_label = QLabel(f"₹{price:,.2f}")
        price_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        price_label.setFixedWidth(100)
        layout.addWidget(price_label)
        
        layout.addStretch()
        
        # Status
        status_color = COLORS['success'] if status == "EXECUTED" else COLORS['warning']
        status_label = QLabel(status)
        status_label.setStyleSheet(f"""
            color: {status_color};
            font-size: 11px;
            font-weight: bold;
        """)
        layout.addWidget(status_label)


class AutoTradingWidget(QWidget):
    """Modern auto trading interface"""
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.strategy_cards = {}
        self.setup_ui()
        
        # Demo updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_demo_data)
        self.update_timer.start(3000)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['lg'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("🤖 Auto Trading")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Master toggle
        self.master_toggle = QPushButton("🔴 All Stopped")
        self.master_toggle.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['surface']};
                color: {COLORS['error']};
                border: 2px solid {COLORS['error']};
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
        """)
        self.master_toggle.setCursor(Qt.PointingHandCursor)
        self.master_toggle.clicked.connect(self._toggle_all)
        header.addWidget(self.master_toggle)
        
        # Add strategy button
        add_btn = QPushButton("+ New Strategy")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_dark']};
            }}
        """)
        add_btn.setCursor(Qt.PointingHandCursor)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Sub-tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                background: transparent;
                padding: 12px 24px;
                color: {COLORS['text_secondary']};
                font-weight: 500;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {COLORS['primary']};
                border-bottom: 2px solid {COLORS['primary']};
            }}
        """)
        
        # Strategies Tab
        strategies_widget = QWidget()
        strategies_layout = QVBoxLayout(strategies_widget)
        strategies_layout.setContentsMargins(0, SPACING['md'], 0, 0)
        
        # Strategy cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        cards_container = QWidget()
        self.cards_layout = QVBoxLayout(cards_container)
        self.cards_layout.setSpacing(SPACING['md'])
        
        # Default strategies
        strategies = [
            ("ma_crossover", "Moving Average Crossover", 
             "Trades when short MA crosses long MA. Good for trending markets.", "📊"),
            ("rsi_reversal", "RSI Reversal", 
             "Buys oversold, sells overbought using RSI indicator.", "📈"),
            ("breakout", "Breakout Strategy", 
             "Trades range breakouts with volume confirmation.", "🚀"),
            ("scalper", "Quick Scalper", 
             "High frequency trades on small price movements.", "⚡"),
        ]
        
        for sid, name, desc, icon in strategies:
            card = StrategyCard(sid, name, desc, icon)
            card.toggle_requested.connect(self._on_strategy_toggle)
            card.configure_requested.connect(self._on_configure)
            self.cards_layout.addWidget(card)
            self.strategy_cards[sid] = card
        
        self.cards_layout.addStretch()
        scroll.setWidget(cards_container)
        strategies_layout.addWidget(scroll)
        
        self.tabs.addTab(strategies_widget, "📋 Strategies")
        
        # Signal Log Tab
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, SPACING['md'], 0, 0)
        
        # Log header
        log_header = QHBoxLayout()
        
        log_title = QLabel("Recent Signals")
        log_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        log_header.addWidget(log_title)
        
        log_header.addStretch()
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
        """)
        clear_btn.setCursor(Qt.PointingHandCursor)
        log_header.addWidget(clear_btn)
        
        log_layout.addLayout(log_header)
        
        # Signal log scroll
        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        log_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        log_container = QWidget()
        self.log_layout = QVBoxLayout(log_container)
        self.log_layout.setSpacing(8)
        
        # Add some demo signals
        demo_signals = [
            ("14:32:15", "RELIANCE", "BUY", 2456.50, "EXECUTED"),
            ("14:30:22", "TCS", "SELL", 3421.00, "EXECUTED"),
            ("14:28:45", "HDFC BANK", "BUY", 1652.75, "PENDING"),
            ("14:25:10", "INFY", "SELL", 1448.25, "EXECUTED"),
            ("14:22:33", "ICICI BANK", "BUY", 982.50, "EXECUTED"),
        ]
        
        for timestamp, symbol, action, price, status in demo_signals:
            row = SignalLogRow(timestamp, symbol, action, price, status)
            self.log_layout.addWidget(row)
        
        self.log_layout.addStretch()
        log_scroll.setWidget(log_container)
        log_layout.addWidget(log_scroll)
        
        self.tabs.addTab(log_widget, "📜 Signal Log")
        
        # Settings Tab
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(0, SPACING['md'], 0, 0)
        
        # Risk Management Section
        risk_frame = QFrame()
        risk_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        risk_layout = QVBoxLayout(risk_frame)
        risk_layout.setContentsMargins(20, 16, 20, 16)
        
        risk_title = QLabel("🛡️ Risk Management")
        risk_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        risk_layout.addWidget(risk_title)
        
        # Settings grid
        risk_grid = QGridLayout()
        risk_grid.setSpacing(SPACING['md'])
        
        # Max daily loss
        risk_grid.addWidget(QLabel("Max Daily Loss"), 0, 0)
        daily_loss = QDoubleSpinBox()
        daily_loss.setPrefix("₹")
        daily_loss.setMaximum(1000000)
        daily_loss.setValue(5000)
        risk_grid.addWidget(daily_loss, 0, 1)
        
        # Max position size
        risk_grid.addWidget(QLabel("Max Position Size"), 1, 0)
        pos_size = QSpinBox()
        pos_size.setMaximum(1000)
        pos_size.setValue(100)
        risk_grid.addWidget(pos_size, 1, 1)
        
        # Stop loss %
        risk_grid.addWidget(QLabel("Default Stop Loss %"), 2, 0)
        sl_pct = QDoubleSpinBox()
        sl_pct.setSuffix("%")
        sl_pct.setMaximum(100)
        sl_pct.setValue(1.5)
        risk_grid.addWidget(sl_pct, 2, 1)
        
        # Take profit %
        risk_grid.addWidget(QLabel("Default Take Profit %"), 3, 0)
        tp_pct = QDoubleSpinBox()
        tp_pct.setSuffix("%")
        tp_pct.setMaximum(100)
        tp_pct.setValue(3.0)
        risk_grid.addWidget(tp_pct, 3, 1)
        
        risk_layout.addLayout(risk_grid)
        settings_layout.addWidget(risk_frame)
        
        # Trading Hours Section
        hours_frame = QFrame()
        hours_frame.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        hours_layout = QVBoxLayout(hours_frame)
        hours_layout.setContentsMargins(20, 16, 20, 16)
        
        hours_title = QLabel("⏰ Trading Hours")
        hours_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        hours_layout.addWidget(hours_title)
        
        hours_row = QHBoxLayout()
        
        hours_row.addWidget(QLabel("Start Time:"))
        start_time = QLineEdit("09:15")
        start_time.setFixedWidth(80)
        hours_row.addWidget(start_time)
        
        hours_row.addSpacing(20)
        
        hours_row.addWidget(QLabel("End Time:"))
        end_time = QLineEdit("15:29")
        end_time.setFixedWidth(80)
        hours_row.addWidget(end_time)
        
        hours_row.addStretch()
        hours_layout.addLayout(hours_row)
        
        # Square off checkbox
        square_off = QCheckBox("Auto square-off at end of day")
        square_off.setChecked(True)
        hours_layout.addWidget(square_off)
        
        settings_layout.addWidget(hours_frame)
        
        settings_layout.addStretch()
        
        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 14px 28px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_dark']};
            }}
        """)
        save_btn.setCursor(Qt.PointingHandCursor)
        settings_layout.addWidget(save_btn)
        
        self.tabs.addTab(settings_widget, "⚙️ Settings")
        
        layout.addWidget(self.tabs)
    
    def _on_strategy_toggle(self, strategy_id: str, enabled: bool):
        """Handle strategy toggle"""
        self._update_master_toggle()
    
    def _on_configure(self, strategy_id: str):
        """Handle strategy configure"""
        # TODO: Open configuration dialog
        pass
    
    def _toggle_all(self):
        """Toggle all strategies"""
        # Check if any strategy is active
        any_active = any(card.is_active for card in self.strategy_cards.values())
        
        for card in self.strategy_cards.values():
            if any_active:
                if card.is_active:
                    card._on_toggle()
            else:
                if not card.is_active:
                    card._on_toggle()
        
        self._update_master_toggle()
    
    def _update_master_toggle(self):
        """Update master toggle button"""
        active_count = sum(1 for card in self.strategy_cards.values() if card.is_active)
        
        if active_count == 0:
            self.master_toggle.setText("🔴 All Stopped")
            self.master_toggle.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['surface']};
                    color: {COLORS['error']};
                    border: 2px solid {COLORS['error']};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
            """)
        elif active_count == len(self.strategy_cards):
            self.master_toggle.setText("🟢 All Running")
            self.master_toggle.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['surface']};
                    color: {COLORS['success']};
                    border: 2px solid {COLORS['success']};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
            """)
        else:
            self.master_toggle.setText(f"🟡 {active_count} Running")
            self.master_toggle.setStyleSheet(f"""
                QPushButton {{
                    background: {COLORS['surface']};
                    color: {COLORS['warning']};
                    border: 2px solid {COLORS['warning']};
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                }}
            """)
    
    def _update_demo_data(self):
        """Update demo data for active strategies"""
        for sid, card in self.strategy_cards.items():
            if card.is_active:
                trades = random.randint(5, 50)
                pnl = random.uniform(-2000, 5000)
                win_rate = random.uniform(40, 70)
                card.update_stats(trades, pnl, win_rate)
    
    def set_trading_service(self, trading_service):
        """Set trading service"""
        self.trading_service = trading_service
