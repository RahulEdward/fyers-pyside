"""Market Data Service - Integrates Fyers API for live and historical data"""
import logging
import threading
import sys
import os
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.models.result import Result, Ok, Err

# Add fyers to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@dataclass
class QuoteData:
    """Quote data structure"""
    symbol: str
    exchange: str
    ltp: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_pct: float
    bid: float
    ask: float
    oi: int
    timestamp: int


class MarketDataService:
    """
    Service for fetching live and historical market data from Fyers API
    
    Integrates with:
    - fyers/api/data.py for historical data and quotes
    - fyers/streaming/fyers_adapter.py for real-time WebSocket streaming
    """
    
    def __init__(self, access_token: str, user_id: str = ""):
        """
        Initialize Market Data Service
        
        Args:
            access_token: Fyers access token
            user_id: User ID for authentication
        """
        self.access_token = access_token
        self.user_id = user_id
        self.logger = logging.getLogger("market_data_service")
        
        # Fyers API components
        self._broker_data = None
        self._adapter = None
        self._connected = False
        
        # Callbacks
        self._quote_callbacks: Dict[str, Callable[[QuoteData], None]] = {}
        self._global_callback: Optional[Callable[[QuoteData], None]] = None
        
        # Cache
        self._quote_cache: Dict[str, QuoteData] = {}
        self._lock = threading.Lock()
        
        # Initialize Fyers API
        self._init_fyers_api()
    
    def _init_fyers_api(self):
        """Initialize Fyers API components"""
        try:
            # Import Fyers BrokerData for quotes and historical data
            from fyers.api.data import BrokerData
            self._broker_data = BrokerData(self.access_token)
            self.logger.info("Fyers BrokerData API initialized")
        except ImportError as e:
            self.logger.warning(f"Could not import Fyers API: {e}")
        except Exception as e:
            self.logger.error(f"Error initializing Fyers API: {e}")
    
    def connect_streaming(self) -> Result[bool, str]:
        """
        Connect to Fyers WebSocket for real-time streaming
        
        Returns:
            Result with True on success, error message on failure
        """
        if self._connected:
            return Ok(True)
        
        try:
            from fyers.streaming.fyers_adapter import FyersAdapter
            
            self._adapter = FyersAdapter(self.access_token, self.user_id)
            
            if self._adapter.connect():
                self._connected = True
                self.logger.info("Connected to Fyers WebSocket streaming")
                return Ok(True)
            else:
                return Err("Failed to connect to Fyers WebSocket")
                
        except ImportError as e:
            self.logger.warning(f"Fyers adapter not available: {e}")
            return Err(f"Fyers adapter not available: {e}")
        except Exception as e:
            self.logger.error(f"Streaming connection error: {e}")
            return Err(f"Connection failed: {str(e)}")
    
    def disconnect_streaming(self):
        """Disconnect from WebSocket streaming"""
        if self._adapter:
            self._adapter.disconnect(clear_mappings=True)
            self._adapter = None
        self._connected = False
        self.logger.info("Disconnected from Fyers WebSocket")
    
    def is_streaming_connected(self) -> bool:
        """Check if streaming is connected"""
        return self._connected and self._adapter is not None
    
    def get_quote(self, symbol: str, exchange: str) -> Result[QuoteData, str]:
        """
        Get real-time quote for a symbol
        
        Args:
            symbol: Trading symbol (e.g., 'RELIANCE', 'NIFTY 50')
            exchange: Exchange (e.g., 'NSE', 'BSE', 'NFO')
            
        Returns:
            Result with QuoteData on success, error message on failure
        """
        if not self._broker_data:
            return Err("Fyers API not initialized")
        
        try:
            quote = self._broker_data.get_quotes(symbol, exchange)
            
            # Calculate change
            ltp = quote.get('ltp', 0)
            prev_close = quote.get('prev_close', 0)
            change = ltp - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            quote_data = QuoteData(
                symbol=symbol,
                exchange=exchange,
                ltp=ltp,
                open=quote.get('open', 0),
                high=quote.get('high', 0),
                low=quote.get('low', 0),
                close=prev_close,
                volume=quote.get('volume', 0),
                change=change,
                change_pct=change_pct,
                bid=quote.get('bid', 0),
                ask=quote.get('ask', 0),
                oi=quote.get('oi', 0),
                timestamp=int(datetime.now().timestamp())
            )
            
            # Cache the quote
            with self._lock:
                self._quote_cache[f"{exchange}:{symbol}"] = quote_data
            
            return Ok(quote_data)
            
        except Exception as e:
            self.logger.error(f"Error fetching quote for {exchange}:{symbol}: {e}")
            return Err(f"Failed to get quote: {str(e)}")
    
    def get_multi_quotes(self, symbols: List[Dict[str, str]]) -> Result[List[QuoteData], str]:
        """
        Get quotes for multiple symbols
        
        Args:
            symbols: List of dicts with 'symbol' and 'exchange' keys
            
        Returns:
            Result with list of QuoteData on success
        """
        if not self._broker_data:
            return Err("Fyers API not initialized")
        
        try:
            results = self._broker_data.get_multiquotes(symbols)
            quotes = []
            
            for item in results:
                if 'error' in item:
                    continue
                    
                data = item.get('data', {})
                symbol = item.get('symbol', '')
                exchange = item.get('exchange', '')
                
                ltp = data.get('ltp', 0)
                prev_close = data.get('prev_close', 0)
                change = ltp - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                quote_data = QuoteData(
                    symbol=symbol,
                    exchange=exchange,
                    ltp=ltp,
                    open=data.get('open', 0),
                    high=data.get('high', 0),
                    low=data.get('low', 0),
                    close=prev_close,
                    volume=data.get('volume', 0),
                    change=change,
                    change_pct=change_pct,
                    bid=data.get('bid', 0),
                    ask=data.get('ask', 0),
                    oi=data.get('oi', 0),
                    timestamp=int(datetime.now().timestamp())
                )
                quotes.append(quote_data)
                
                # Cache
                with self._lock:
                    self._quote_cache[f"{exchange}:{symbol}"] = quote_data
            
            return Ok(quotes)
            
        except Exception as e:
            self.logger.error(f"Error fetching multi-quotes: {e}")
            return Err(f"Failed to get quotes: {str(e)}")
    
    def get_historical_data(
        self, 
        symbol: str, 
        exchange: str, 
        interval: str = '1m',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Result[Any, str]:
        """
        Get historical OHLCV data for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Timeframe (5s, 1m, 5m, 15m, 1h, D)
            start_date: Start date (YYYY-MM-DD), defaults to today
            end_date: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            Result with DataFrame on success
        """
        if not self._broker_data:
            return Err("Fyers API not initialized")
        
        try:
            # Default to today if not specified
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if not start_date:
                start_date = end_date
            
            df = self._broker_data.get_history(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            return Ok(df)
            
        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")
            return Err(f"Failed to get historical data: {str(e)}")
    
    def get_market_depth(self, symbol: str, exchange: str) -> Result[Dict[str, Any], str]:
        """
        Get market depth (order book) for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            Result with depth data on success
        """
        if not self._broker_data:
            return Err("Fyers API not initialized")
        
        try:
            depth = self._broker_data.get_depth(symbol, exchange)
            return Ok(depth)
        except Exception as e:
            self.logger.error(f"Error fetching market depth: {e}")
            return Err(f"Failed to get market depth: {str(e)}")
    
    def subscribe_realtime(
        self, 
        symbol: str, 
        exchange: str, 
        callback: Callable[[Dict[str, Any]], None]
    ) -> Result[bool, str]:
        """
        Subscribe to real-time streaming updates for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            callback: Callback function for price updates
            
        Returns:
            Result with True on success
        """
        if not self._connected:
            connect_result = self.connect_streaming()
            if isinstance(connect_result, Err):
                return connect_result
        
        if not self._adapter:
            return Err("Streaming adapter not available")
        
        try:
            symbols = [{"exchange": exchange, "symbol": symbol}]
            
            def data_handler(data: Dict[str, Any]):
                # Convert to QuoteData and cache
                ltp = data.get('ltp', 0)
                prev_close = data.get('close', data.get('prev_close', 0))
                change = ltp - prev_close
                change_pct = (change / prev_close * 100) if prev_close > 0 else 0
                
                quote_data = QuoteData(
                    symbol=data.get('symbol', symbol),
                    exchange=data.get('exchange', exchange),
                    ltp=ltp,
                    open=data.get('open', 0),
                    high=data.get('high', 0),
                    low=data.get('low', 0),
                    close=prev_close,
                    volume=data.get('volume', 0),
                    change=change,
                    change_pct=change_pct,
                    bid=data.get('bid', 0),
                    ask=data.get('ask', 0),
                    oi=data.get('oi', 0),
                    timestamp=data.get('timestamp', int(datetime.now().timestamp()))
                )
                
                # Cache
                with self._lock:
                    self._quote_cache[f"{exchange}:{symbol}"] = quote_data
                
                # Call user callback
                callback(data)
                
                # Call global callback if set
                if self._global_callback:
                    self._global_callback(quote_data)
            
            success = self._adapter.subscribe_quote(symbols, data_handler)
            
            if success:
                self._quote_callbacks[f"{exchange}:{symbol}"] = callback
                self.logger.info(f"Subscribed to real-time updates for {exchange}:{symbol}")
                return Ok(True)
            else:
                return Err(f"Failed to subscribe to {exchange}:{symbol}")
                
        except Exception as e:
            self.logger.error(f"Subscription error: {e}")
            return Err(f"Subscription failed: {str(e)}")
    
    def set_global_callback(self, callback: Callable[[QuoteData], None]):
        """Set a global callback for all price updates"""
        self._global_callback = callback
    
    def get_cached_quote(self, symbol: str, exchange: str) -> Optional[QuoteData]:
        """Get cached quote data"""
        with self._lock:
            return self._quote_cache.get(f"{exchange}:{symbol}")
    
    def get_all_cached_quotes(self) -> Dict[str, QuoteData]:
        """Get all cached quotes"""
        with self._lock:
            return dict(self._quote_cache)
