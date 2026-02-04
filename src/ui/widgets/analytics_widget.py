"""Analytics Widget - Modern trading analytics dashboard with charts"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QLinearGradient, QPen, QBrush, QPainterPath

from src.ui.styles import COLORS, SPACING
from datetime import datetime, timedelta
import random


class AreaChart(QWidget):
    """Beautiful area chart with gradient fill"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []
        self.labels = []
        self.is_positive = True
        self.setMinimumHeight(200)
        
    def set_data(self, data: list, labels: list = None, is_positive: bool = True):
        """Set chart data"""
        self.data = data
        self.labels = labels or []
        self.is_positive = is_positive
        self.update()
    
    def paintEvent(self, event):
        """Draw the area chart"""
        if not self.data or len(self.data) < 2:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        padding = 40
        chart_height = height - padding * 2
        chart_width = width - padding * 2
        
        min_val = min(self.data)
        max_val = max(self.data)
        val_range = max_val - min_val if max_val != min_val else 1
        
        # Draw grid lines
        painter.setPen(QPen(QColor(COLORS['border']), 1, Qt.DashLine))
        for i in range(5):
            y = padding + (i / 4) * chart_height
            painter.drawLine(padding, int(y), width - padding, int(y))
        
        # Calculate points
        points = []
        for i, val in enumerate(self.data):
            x = padding + (i / (len(self.data) - 1)) * chart_width
            y = height - padding - ((val - min_val) / val_range) * chart_height
            points.append((x, y))
        
        # Draw gradient area
        color = QColor(COLORS['success']) if self.is_positive else QColor(COLORS['error'])
        
        path = QPainterPath()
        path.moveTo(points[0][0], height - padding)
        for x, y in points:
            path.lineTo(x, y)
        path.lineTo(points[-1][0], height - padding)
        path.closeSubpath()
        
        gradient = QLinearGradient(0, padding, 0, height - padding)
        gradient.setColorAt(0, QColor(color.red(), color.green(), color.blue(), 100))
        gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 10))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # Draw line
        painter.setPen(QPen(color, 3))
        for i in range(len(points) - 1):
            painter.drawLine(int(points[i][0]), int(points[i][1]),
                           int(points[i+1][0]), int(points[i+1][1]))
        
        # Draw dots at data points
        painter.setBrush(QBrush(color))
        for x, y in points:
            painter.drawEllipse(int(x) - 4, int(y) - 4, 8, 8)
        
        # Draw y-axis labels
        painter.setPen(QPen(QColor(COLORS['text_secondary'])))
        for i in range(5):
            val = max_val - (i / 4) * val_range
            y = padding + (i / 4) * chart_height
            painter.drawText(5, int(y) + 5, f"₹{val:,.0f}")


class DonutChart(QWidget):
    """Modern donut chart for portfolio distribution"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = []  # List of (label, value, color)
        self.setFixedSize(180, 180)
        
    def set_data(self, data: list):
        """Set chart data: [(label, value, color), ...]"""
        self.data = data
        self.update()
    
    def paintEvent(self, event):
        """Draw the donut chart"""
        if not self.data:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        total = sum(d[1] for d in self.data)
        if total == 0:
            return
        
        size = min(self.width(), self.height()) - 20
        x = (self.width() - size) // 2
        y = (self.height() - size) // 2
        
        start_angle = 90 * 16  # Start from top
        
        for label, value, color in self.data:
            span_angle = int((value / total) * 360 * 16)
            
            painter.setPen(QPen(QColor(color), 2))
            painter.setBrush(QBrush(QColor(color)))
            painter.drawPie(x, y, size, size, start_angle, -span_angle)
            
            start_angle -= span_angle
        
        # Draw center hole
        hole_size = size * 0.6
        hole_x = x + (size - hole_size) // 2
        hole_y = y + (size - hole_size) // 2
        
        painter.setBrush(QBrush(QColor(COLORS['surface'])))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(hole_x), int(hole_y), int(hole_size), int(hole_size))


class PerformanceCard(QFrame):
    """Performance metric card"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
        
    def setup_ui(self):
        self.setStyleSheet(f"""
            PerformanceCard {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)
        
        # Title
        title = QLabel(self.title)
        title.setStyleSheet(f"""
            font-size: 11px;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title)
        
        # Value
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(self.value_label)
        
        # Subtitle
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(self.subtitle_label)
    
    def set_value(self, value: str, subtitle: str = "", color: str = None):
        """Set the card value"""
        self.value_label.setText(value)
        self.subtitle_label.setText(subtitle)
        if color:
            self.value_label.setStyleSheet(f"""
                font-size: 28px;
                font-weight: bold;
                color: {color};
            """)


class AnalyticsWidget(QWidget):
    """Modern trading analytics dashboard"""
    
    def __init__(self, trading_service=None, parent=None):
        super().__init__(parent)
        self.trading_service = trading_service
        self.setup_ui()
        
        # Demo data timer
        self.demo_timer = QTimer(self)
        self.demo_timer.timeout.connect(self._generate_demo_data)
        self.demo_timer.start(5000)
        self._generate_demo_data()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING['md'], SPACING['md'], SPACING['md'], SPACING['md'])
        layout.setSpacing(SPACING['lg'])
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("📈 Trading Analytics")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)
        
        header.addStretch()
        
        # Time period selector
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "This Week", "This Month", "This Year"])
        self.period_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 8px 16px;
                min-width: 120px;
            }}
        """)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        header.addWidget(self.period_combo)
        
        layout.addLayout(header)
        
        # Performance Cards Row
        cards_layout = QGridLayout()
        cards_layout.setSpacing(SPACING['md'])
        
        self.total_pnl_card = PerformanceCard("Total P&L")
        cards_layout.addWidget(self.total_pnl_card, 0, 0)
        
        self.win_rate_card = PerformanceCard("Win Rate")
        cards_layout.addWidget(self.win_rate_card, 0, 1)
        
        self.total_trades_card = PerformanceCard("Total Trades")
        cards_layout.addWidget(self.total_trades_card, 0, 2)
        
        self.avg_profit_card = PerformanceCard("Avg Profit")
        cards_layout.addWidget(self.avg_profit_card, 0, 3)
        
        layout.addLayout(cards_layout)
        
        # Charts Row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(SPACING['lg'])
        
        # P&L Chart Section
        pnl_section = QFrame()
        pnl_section.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        pnl_layout = QVBoxLayout(pnl_section)
        pnl_layout.setContentsMargins(20, 16, 20, 16)
        
        pnl_header = QLabel("📊 P&L Over Time")
        pnl_header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        pnl_layout.addWidget(pnl_header)
        
        self.pnl_chart = AreaChart()
        pnl_layout.addWidget(self.pnl_chart)
        
        charts_layout.addWidget(pnl_section, stretch=2)
        
        # Portfolio Distribution Section
        portfolio_section = QFrame()
        portfolio_section.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        portfolio_layout = QVBoxLayout(portfolio_section)
        portfolio_layout.setContentsMargins(20, 16, 20, 16)
        
        portfolio_header = QLabel("🎯 Portfolio Distribution")
        portfolio_header.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        portfolio_layout.addWidget(portfolio_header)
        
        chart_row = QHBoxLayout()
        chart_row.addStretch()
        self.donut_chart = DonutChart()
        chart_row.addWidget(self.donut_chart)
        chart_row.addStretch()
        portfolio_layout.addLayout(chart_row)
        
        # Legend
        self.legend_layout = QVBoxLayout()
        portfolio_layout.addLayout(self.legend_layout)
        
        charts_layout.addWidget(portfolio_section, stretch=1)
        
        layout.addLayout(charts_layout)
        
        # Recent Trades Table
        trades_section = QFrame()
        trades_section.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 16px;
            }}
        """)
        trades_layout = QVBoxLayout(trades_section)
        trades_layout.setContentsMargins(20, 16, 20, 16)
        
        trades_header = QHBoxLayout()
        trades_title = QLabel("📋 Recent Trades")
        trades_title.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {COLORS['text_primary']};
        """)
        trades_header.addWidget(trades_title)
        trades_header.addStretch()
        
        view_all_btn = QPushButton("View All →")
        view_all_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['primary']};
                border: none;
                font-size: 13px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        view_all_btn.setCursor(Qt.PointingHandCursor)
        trades_header.addWidget(view_all_btn)
        
        trades_layout.addLayout(trades_header)
        
        # Trade rows container
        self.trades_container = QVBoxLayout()
        self.trades_container.setSpacing(8)
        trades_layout.addLayout(self.trades_container)
        
        layout.addWidget(trades_section)
    
    def _on_period_changed(self, index):
        """Handle period change"""
        self._generate_demo_data()
    
    def _generate_demo_data(self):
        """Generate demo analytics data"""
        # Performance cards
        pnl = random.uniform(-5000, 15000)
        pnl_color = COLORS['success'] if pnl >= 0 else COLORS['error']
        sign = "+" if pnl >= 0 else ""
        self.total_pnl_card.set_value(f"{sign}₹{pnl:,.0f}", "vs last period", pnl_color)
        
        win_rate = random.uniform(45, 75)
        self.win_rate_card.set_value(f"{win_rate:.1f}%", f"{int(win_rate)}W / {int(100-win_rate)}L", COLORS['primary'])
        
        total_trades = random.randint(10, 100)
        self.total_trades_card.set_value(str(total_trades), "completed trades")
        
        avg_profit = random.uniform(200, 1000)
        self.avg_profit_card.set_value(f"₹{avg_profit:,.0f}", "per trade", COLORS['success'])
        
        # P&L Chart
        days = 10
        base = 10000
        chart_data = []
        for i in range(days):
            base += random.uniform(-500, 800)
            chart_data.append(base)
        
        is_positive = chart_data[-1] > chart_data[0]
        self.pnl_chart.set_data(chart_data, is_positive=is_positive)
        
        # Portfolio Distribution
        portfolio_data = [
            ("NIFTY", 35, COLORS['primary']),
            ("BANKNIFTY", 25, COLORS['secondary']),
            ("Stocks", 20, COLORS['warning']),
            ("Others", 20, COLORS['info']),
        ]
        self.donut_chart.set_data(portfolio_data)
        
        # Update legend
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for label, value, color in portfolio_data:
            row = QHBoxLayout()
            
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 12px;")
            row.addWidget(dot)
            
            name = QLabel(label)
            name.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px;")
            row.addWidget(name)
            
            row.addStretch()
            
            pct = QLabel(f"{value}%")
            pct.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            row.addWidget(pct)
            
            container = QWidget()
            container.setLayout(row)
            self.legend_layout.addWidget(container)
        
        # Recent trades
        while self.trades_container.count():
            item = self.trades_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        trades = [
            ("RELIANCE", "NSE", "BUY", 2500, 2520, 500),
            ("TCS", "NSE", "SELL", 3400, 3380, -400),
            ("HDFC BANK", "NSE", "BUY", 1650, 1680, 750),
            ("INFY", "NSE", "SELL", 1450, 1420, 750),
        ]
        
        for symbol, exchange, action, entry, exit_price, pnl in trades:
            row = self._create_trade_row(symbol, exchange, action, entry, exit_price, pnl)
            self.trades_container.addWidget(row)
    
    def _create_trade_row(self, symbol, exchange, action, entry, exit_price, pnl):
        """Create a trade row widget"""
        row = QFrame()
        row.setStyleSheet(f"""
            QFrame {{
                background: {COLORS['surface_light']};
                border-radius: 8px;
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 12, 8)
        
        # Symbol and action
        left = QVBoxLayout()
        symbol_label = QLabel(symbol)
        symbol_label.setStyleSheet(f"font-weight: bold; color: {COLORS['text_primary']};")
        left.addWidget(symbol_label)
        
        action_color = COLORS['success'] if action == "BUY" else COLORS['error']
        action_label = QLabel(f"{action} @ ₹{entry:,.0f}")
        action_label.setStyleSheet(f"font-size: 11px; color: {action_color};")
        left.addWidget(action_label)
        
        layout.addLayout(left)
        layout.addStretch()
        
        # P&L
        pnl_color = COLORS['success'] if pnl >= 0 else COLORS['error']
        sign = "+" if pnl >= 0 else ""
        pnl_label = QLabel(f"{sign}₹{pnl:,.0f}")
        pnl_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: bold;
            color: {pnl_color};
        """)
        layout.addWidget(pnl_label)
        
        return row
    
    def set_trading_service(self, trading_service):
        """Set trading service"""
        self.trading_service = trading_service
