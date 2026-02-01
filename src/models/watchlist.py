"""Watchlist data models"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WatchlistItem:
    """Watchlist item model"""
    id: int
    user_id: int
    symbol: str
    exchange: str
    added_at: datetime
    
    def __post_init__(self):
        if isinstance(self.added_at, str):
            self.added_at = datetime.fromisoformat(self.added_at)


@dataclass
class QuoteData:
    """Real-time quote data"""
    symbol: str
    exchange: str
    ltp: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_percent: float
    bid: float
    ask: float
    timestamp: datetime
    
    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class SymbolInfo:
    """Symbol information from master contract"""
    symbol: str
    name: str
    exchange: str
    token: str
    lot_size: int
    tick_size: float
