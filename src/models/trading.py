"""Trading data models"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .enums import OrderType, OrderAction, OrderStatus, ProductType


@dataclass
class FundsData:
    """Account funds/margin data"""
    available_cash: float
    collateral: float
    utilized: float
    realized_pnl: float
    unrealized_pnl: float


@dataclass
class Position:
    """Open position model"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    ltp: float
    pnl: float
    product_type: str


@dataclass
class Holding:
    """Holdings/portfolio model"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percentage: float


@dataclass
class Order:
    """Order model"""
    order_id: str
    symbol: str
    exchange: str
    action: OrderAction
    quantity: int
    order_type: OrderType
    price: Optional[float]
    trigger_price: Optional[float]
    status: OrderStatus
    filled_quantity: int
    average_price: float
    timestamp: datetime
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)
        if isinstance(self.action, str):
            self.action = OrderAction(self.action)
        if isinstance(self.order_type, int):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)


@dataclass
class OrderRequest:
    """Order placement request"""
    symbol: str
    exchange: str
    action: OrderAction
    quantity: int
    order_type: OrderType
    product_type: ProductType
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    
    def __post_init__(self):
        if isinstance(self.action, str):
            self.action = OrderAction(self.action)
        if isinstance(self.order_type, int):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.product_type, str):
            self.product_type = ProductType(self.product_type)


@dataclass
class OrderModification:
    """Order modification request"""
    order_id: str
    quantity: Optional[int] = None
    price: Optional[float] = None
    trigger_price: Optional[float] = None
