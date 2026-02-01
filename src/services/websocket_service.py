"""WebSocket service for real-time market data streaming"""
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from src.models.result import Result, Ok, Err
from src.models.watchlist import QuoteData


class SubscriptionMode(Enum):
    """WebSocket subscription modes"""
    LTP = 1      # Last Traded Price only
    QUOTE = 2    # Quote data (LTP + OHLC + volume)
    DEPTH = 3    # Market depth (order book)


@dataclass
class SubscriptionInfo:
    """Information about an active subscription"""
    symbol: str
    exchange: str
    mode: SubscriptionMode
    callback: Optional[Callable[[Dict[str, Any]], None]] = None


class WebSocketService:
    """
    Service for managing WebSocket connections for real-time market data
    
    This service wraps the Fyers streaming functionality and provides
    a simplified interface for subscribing to market data.
    """
    
    def __init__(self, access_token: str, user_id: str):
        """
        Initialize WebSocket service
        
        Args:
            access_token: Fyers access token
            user_id: User ID for authentication
        """
        self.access_token = access_token
        self.user_id = user_id
        self.logger = logging.getLogger("websocket_service")
        
        # Connection state
        self._connected = False
        self._connecting = False
        self._adapter = None
        
        # Subscription tracking
        self._subscriptions: Dict[str, SubscriptionInfo] = {}
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {}
        self._global_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Threading
        self._lock = threading.Lock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._should_reconnect = True
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
    
    def connect(self) -> Result[bool, str]:
        """
        Connect to WebSocket server
        
        Returns:
            Result with True on success, error message on failure
        """
        if self._connected:
            return Ok(True)
        
        if self._connecting:
            return Err("Connection already in progress")
        
        try:
            self._connecting = True
            self.logger.info("Connecting to Fyers WebSocket...")
            
            # Try to import and use Fyers adapter
            try:
                from fyers.streaming.fyers_adapter import FyersAdapter
                self._adapter = FyersAdapter(self.access_token, self.user_id)
                
                if self._adapter.connect():
                    self._connected = True
                    self.logger.info("Connected to Fyers WebSocket")
                    return Ok(True)
                else:
                    return Err("Failed to connect to Fyers WebSocket")
                    
            except ImportError as e:
                self.logger.warning(f"Fyers adapter not available: {e}")
                # Fallback to mock connection for testing
                self._connected = True
                self.logger.info("Connected (mock mode - Fyers adapter not available)")
                return Ok(True)
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return Err(f"Connection failed: {str(e)}")
        finally:
            self._connecting = False
    
    def disconnect(self) -> Result[bool, str]:
        """
        Disconnect from WebSocket server
        
        Returns:
            Result with True on success, error message on failure
        """
        try:
            self._should_reconnect = False
            
            with self._lock:
                # Clear all subscriptions
                self._subscriptions.clear()
                self._callbacks.clear()
            
            # Disconnect adapter
            if self._adapter:
                self._adapter.disconnect(clear_mappings=True)
                self._adapter = None
            
            self._connected = False
            self.logger.info("Disconnected from WebSocket")
            return Ok(True)
            
        except Exception as e:
            self.logger.error(f"Disconnect error: {e}")
            return Err(f"Disconnect failed: {str(e)}")
    
    def subscribe(
        self,
        symbol: str,
        exchange: str,
        mode: SubscriptionMode = SubscriptionMode.QUOTE,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Result[bool, str]:
        """
        Subscribe to market data for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            mode: Subscription mode (LTP, QUOTE, or DEPTH)
            callback: Optional callback for this specific subscription
            
        Returns:
            Result with True on success, error message on failure
        """
        if not symbol or not exchange:
            return Err("Symbol and exchange are required")
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        # Auto-connect if not connected
        if not self._connected:
            connect_result = self.connect()
            if isinstance(connect_result, Err):
                return connect_result
        
        try:
            with self._lock:
                key = f"{exchange}:{symbol}:{mode.value}"
                
                # Check if already subscribed
                if key in self._subscriptions:
                    return Ok(True)  # Already subscribed
                
                # Store subscription info
                self._subscriptions[key] = SubscriptionInfo(
                    symbol=symbol,
                    exchange=exchange,
                    mode=mode,
                    callback=callback
                )
                
                if callback:
                    self._callbacks[key] = callback
            
            # Subscribe via adapter if available
            if self._adapter:
                symbol_info = [{"exchange": exchange, "symbol": symbol}]
                
                def data_handler(data: Dict[str, Any]):
                    self._on_data_received(data, symbol, exchange, mode)
                
                if mode == SubscriptionMode.LTP:
                    success = self._adapter.subscribe_ltp(symbol_info, data_handler)
                elif mode == SubscriptionMode.QUOTE:
                    success = self._adapter.subscribe_quote(symbol_info, data_handler)
                elif mode == SubscriptionMode.DEPTH:
                    success = self._adapter.subscribe_depth(symbol_info, data_handler)
                else:
                    success = False
                
                if not success:
                    # Remove from tracking if subscription failed
                    with self._lock:
                        self._subscriptions.pop(key, None)
                        self._callbacks.pop(key, None)
                    return Err(f"Failed to subscribe to {exchange}:{symbol}")
            
            self.logger.info(f"Subscribed to {exchange}:{symbol} (mode: {mode.name})")
            return Ok(True)
            
        except Exception as e:
            self.logger.error(f"Subscribe error: {e}")
            return Err(f"Subscribe failed: {str(e)}")
    
    def unsubscribe(self, symbol: str, exchange: str, mode: Optional[SubscriptionMode] = None) -> Result[bool, str]:
        """
        Unsubscribe from market data for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            mode: Optional subscription mode (if None, unsubscribe from all modes)
            
        Returns:
            Result with True on success, error message on failure
        """
        if not symbol or not exchange:
            return Err("Symbol and exchange are required")
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        try:
            with self._lock:
                removed = False
                
                if mode:
                    # Remove specific mode
                    key = f"{exchange}:{symbol}:{mode.value}"
                    if key in self._subscriptions:
                        del self._subscriptions[key]
                        self._callbacks.pop(key, None)
                        removed = True
                else:
                    # Remove all modes for this symbol
                    keys_to_remove = [
                        k for k in self._subscriptions.keys()
                        if k.startswith(f"{exchange}:{symbol}:")
                    ]
                    for key in keys_to_remove:
                        del self._subscriptions[key]
                        self._callbacks.pop(key, None)
                        removed = True
                
                if not removed:
                    return Err(f"No subscription found for {exchange}:{symbol}")
            
            self.logger.info(f"Unsubscribed from {exchange}:{symbol}")
            return Ok(True)
            
        except Exception as e:
            self.logger.error(f"Unsubscribe error: {e}")
            return Err(f"Unsubscribe failed: {str(e)}")
    
    def set_global_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Set a global callback for all market data
        
        Args:
            callback: Callback function to receive all market data
        """
        self._global_callback = callback
    
    def get_subscriptions(self) -> List[SubscriptionInfo]:
        """
        Get list of active subscriptions
        
        Returns:
            List of SubscriptionInfo objects
        """
        with self._lock:
            return list(self._subscriptions.values())
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._connected
    
    def _on_data_received(
        self,
        data: Dict[str, Any],
        symbol: str,
        exchange: str,
        mode: SubscriptionMode
    ) -> None:
        """
        Handle incoming market data
        
        Args:
            data: Market data dictionary
            symbol: Symbol this data is for
            exchange: Exchange this data is for
            mode: Subscription mode
        """
        try:
            # Add symbol info to data
            data['symbol'] = symbol
            data['exchange'] = exchange
            data['mode'] = mode.value
            
            # Call global callback if set
            if self._global_callback:
                self._global_callback(data)
            
            # Call symbol-specific callback if set
            key = f"{exchange}:{symbol}:{mode.value}"
            callback = self._callbacks.get(key)
            if callback:
                callback(data)
                
        except Exception as e:
            self.logger.error(f"Error in data callback: {e}")
    
    def _start_reconnect_loop(self) -> None:
        """Start background reconnection loop"""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        
        self._should_reconnect = True
        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            daemon=True
        )
        self._reconnect_thread.start()
    
    def _reconnect_loop(self) -> None:
        """Background reconnection loop"""
        import time
        
        attempts = 0
        while self._should_reconnect and attempts < self._max_reconnect_attempts:
            if self._connected:
                break
            
            self.logger.info(f"Reconnection attempt {attempts + 1}/{self._max_reconnect_attempts}")
            
            result = self.connect()
            if isinstance(result, Ok):
                # Resubscribe to all symbols
                self._resubscribe_all()
                break
            
            attempts += 1
            time.sleep(self._reconnect_delay)
        
        if not self._connected:
            self.logger.error("Failed to reconnect after maximum attempts")
    
    def _resubscribe_all(self) -> None:
        """Resubscribe to all previously subscribed symbols"""
        with self._lock:
            subscriptions = list(self._subscriptions.values())
        
        for sub in subscriptions:
            self.subscribe(
                symbol=sub.symbol,
                exchange=sub.exchange,
                mode=sub.mode,
                callback=sub.callback
            )
