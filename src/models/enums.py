"""Enums for the trading system"""
from enum import Enum


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = 1
    LIMIT = 2
    SL = 3
    SL_MARKET = 4


class OrderAction(Enum):
    """Order action (buy/sell) enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status enumeration"""
    OPEN = "open"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    PENDING = "pending"
    TRIGGER_PENDING = "trigger_pending"


class ProductType(Enum):
    """Product type enumeration"""
    CNC = "CNC"          # Cash and Carry (Delivery)
    INTRADAY = "INTRADAY"  # Intraday/MIS
    MARGIN = "MARGIN"    # NRML
    CO = "CO"            # Cover Order
    BO = "BO"            # Bracket Order
