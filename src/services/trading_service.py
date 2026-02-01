"""
Trading Service for executing trades and fetching portfolio data.

This module provides trading functionality using the existing Fyers API code.
It wraps the Fyers API calls and transforms data to application models.

Requirements: 6.1, 7.1, 8.1, 9.1, 10.5, 11.3, 12.2
"""

import os
from typing import List, Optional
from datetime import datetime

from src.models.trading import FundsData, Position, Holding, Order, OrderRequest, OrderModification
from src.models.enums import OrderType, OrderAction, OrderStatus, ProductType
from src.models.result import Result, Ok, Err


class TradingService:
    """
    Service for trading operations using Fyers API.
    
    This service provides methods for:
    - Fetching funds/margin data
    - Fetching positions and holdings
    - Fetching order book
    - Placing, modifying, and canceling orders
    - Closing all positions
    """
    
    def __init__(self, access_token: str, api_key: str = None):
        """
        Initialize TradingService with access token.
        
        Args:
            access_token: Fyers API access token
            api_key: Optional API key (will use env var if not provided)
        
        Raises:
            ValueError: If access_token is empty
        """
        if not access_token or not access_token.strip():
            raise ValueError("Access token cannot be empty")
        
        self.access_token = access_token.strip()
        self._api_key = api_key
    
    def _set_api_key_env(self):
        """Set API key in environment if provided."""
        if self._api_key:
            os.environ['BROKER_API_KEY'] = self._api_key
    
    def get_funds(self) -> Result[FundsData, str]:
        """
        Fetch funds/margin data from Fyers API.
        
        Returns:
            Result[FundsData, str]: Ok(FundsData) on success, Err(str) on failure
        
        Requirements: 6.1
        """
        try:
            self._set_api_key_env()
            
            from fyers.api.funds import get_margin_data
            
            margin_data = get_margin_data(self.access_token)
            
            funds = FundsData(
                available_cash=float(margin_data.get('availablecash', 0)),
                collateral=float(margin_data.get('collateral', 0)),
                utilized=float(margin_data.get('utiliseddebits', 0)),
                realized_pnl=float(margin_data.get('m2mrealized', 0)),
                unrealized_pnl=float(margin_data.get('m2munrealized', 0))
            )
            
            return Ok(funds)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to fetch funds: {str(e)}")
    
    def get_positions(self) -> Result[List[Position], str]:
        """
        Fetch open positions from Fyers API.
        
        Returns:
            Result[List[Position], str]: Ok(positions) on success, Err(str) on failure
        
        Requirements: 7.1
        """
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import get_positions as fyers_get_positions
            
            response = fyers_get_positions(self.access_token)
            
            if response.get('s') != 'ok':
                return Err(response.get('message', 'Failed to fetch positions'))
            
            positions = []
            for pos in response.get('netPositions', []):
                position = Position(
                    symbol=pos.get('symbol', ''),
                    exchange=pos.get('exchange', ''),
                    quantity=int(pos.get('netQty', 0)),
                    average_price=float(pos.get('avgPrice', 0)),
                    ltp=float(pos.get('ltp', 0)),
                    pnl=float(pos.get('pl', 0)),
                    product_type=pos.get('productType', '')
                )
                positions.append(position)
            
            return Ok(positions)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to fetch positions: {str(e)}")
    
    def get_holdings(self) -> Result[List[Holding], str]:
        """
        Fetch holdings from Fyers API.
        
        Returns:
            Result[List[Holding], str]: Ok(holdings) on success, Err(str) on failure
        
        Requirements: 8.1
        """
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import get_holdings as fyers_get_holdings
            
            response = fyers_get_holdings(self.access_token)
            
            if response.get('s') != 'ok':
                return Err(response.get('message', 'Failed to fetch holdings'))
            
            holdings = []
            for hold in response.get('holdings', []):
                avg_price = float(hold.get('costPrice', 0))
                current_price = float(hold.get('ltp', 0))
                quantity = int(hold.get('quantity', 0))
                pnl = (current_price - avg_price) * quantity
                pnl_pct = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
                
                holding = Holding(
                    symbol=hold.get('symbol', ''),
                    exchange=hold.get('exchange', ''),
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    pnl=pnl,
                    pnl_percentage=pnl_pct
                )
                holdings.append(holding)
            
            return Ok(holdings)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to fetch holdings: {str(e)}")
    
    def get_order_book(self) -> Result[List[Order], str]:
        """
        Fetch order book from Fyers API.
        
        Returns:
            Result[List[Order], str]: Ok(orders) on success, Err(str) on failure
        
        Requirements: 9.1
        """
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import get_order_book as fyers_get_order_book
            
            response = fyers_get_order_book(self.access_token)
            
            if response.get('s') != 'ok':
                return Err(response.get('message', 'Failed to fetch order book'))
            
            orders = []
            for ord in response.get('orderBook', []):
                order = Order(
                    order_id=str(ord.get('id', '')),
                    symbol=ord.get('symbol', ''),
                    exchange=ord.get('exchange', ''),
                    action=OrderAction.BUY if ord.get('side') == 1 else OrderAction.SELL,
                    quantity=int(ord.get('qty', 0)),
                    order_type=OrderType(ord.get('type', 1)),
                    price=float(ord.get('limitPrice', 0)) if ord.get('limitPrice') else None,
                    trigger_price=float(ord.get('stopPrice', 0)) if ord.get('stopPrice') else None,
                    status=self._map_order_status(ord.get('status', 0)),
                    filled_quantity=int(ord.get('filledQty', 0)),
                    average_price=float(ord.get('tradedPrice', 0)),
                    timestamp=datetime.now()  # Fyers doesn't always provide timestamp
                )
                orders.append(order)
            
            return Ok(orders)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to fetch order book: {str(e)}")
    
    def _map_order_status(self, status_code: int) -> OrderStatus:
        """Map Fyers order status code to OrderStatus enum."""
        status_map = {
            1: OrderStatus.CANCELLED,
            2: OrderStatus.COMPLETED,
            3: OrderStatus.REJECTED,
            4: OrderStatus.PENDING,  # Trigger pending
            5: OrderStatus.COMPLETED,  # Traded
            6: OrderStatus.OPEN,
        }
        return status_map.get(status_code, OrderStatus.PENDING)
    
    def place_order(self, order: OrderRequest) -> Result[str, str]:
        """
        Place a new order using Fyers API.
        
        Args:
            order: OrderRequest with order details
        
        Returns:
            Result[str, str]: Ok(order_id) on success, Err(str) on failure
        
        Requirements: 10.5
        """
        # Validate order
        validation_result = self._validate_order(order)
        if validation_result.is_err():
            return validation_result
        
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import place_order_api
            
            # Prepare order data
            order_data = {
                'symbol': order.symbol,
                'exchange': order.exchange,
                'action': order.action.value,
                'quantity': str(order.quantity),
                'order_type': order.order_type.value,
                'product': order.product_type.value,
                'price': str(order.price) if order.price else '0',
                'trigger_price': str(order.trigger_price) if order.trigger_price else '0'
            }
            
            response, response_data, order_id = place_order_api(order_data, self.access_token)
            
            if order_id:
                return Ok(order_id)
            else:
                error_msg = response_data.get('message', 'Order placement failed')
                return Err(error_msg)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to place order: {str(e)}")
    
    def _validate_order(self, order: OrderRequest) -> Result[None, str]:
        """Validate order request."""
        if not order.symbol or not order.symbol.strip():
            return Err("Symbol cannot be empty")
        
        if not order.exchange or not order.exchange.strip():
            return Err("Exchange cannot be empty")
        
        if order.quantity <= 0:
            return Err("Quantity must be positive")
        
        # Validate price for limit/SL orders
        if order.order_type in [OrderType.LIMIT, OrderType.SL]:
            if order.price is None or order.price <= 0:
                return Err("Price is required for Limit/SL orders")
        
        return Ok(None)
    
    def modify_order(self, modification: OrderModification) -> Result[None, str]:
        """
        Modify an existing order.
        
        Args:
            modification: OrderModification with changes
        
        Returns:
            Result[None, str]: Ok(None) on success, Err(str) on failure
        
        Requirements: 11.3
        """
        if not modification.order_id or not modification.order_id.strip():
            return Err("Order ID cannot be empty")
        
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import modify_order as fyers_modify_order
            
            # Prepare modification data
            mod_data = {
                'id': modification.order_id,
            }
            
            if modification.quantity is not None:
                mod_data['qty'] = modification.quantity
            if modification.price is not None:
                mod_data['limitPrice'] = modification.price
            if modification.trigger_price is not None:
                mod_data['stopPrice'] = modification.trigger_price
            
            response_data, status_code = fyers_modify_order(mod_data, self.access_token)
            
            if status_code == 200:
                return Ok(None)
            else:
                error_msg = response_data.get('message', 'Order modification failed')
                return Err(error_msg)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to modify order: {str(e)}")
    
    def cancel_order(self, order_id: str) -> Result[None, str]:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
        
        Returns:
            Result[None, str]: Ok(None) on success, Err(str) on failure
        
        Requirements: 12.2
        """
        if not order_id or not order_id.strip():
            return Err("Order ID cannot be empty")
        
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import cancel_order as fyers_cancel_order
            
            response_data, status_code = fyers_cancel_order(order_id.strip(), self.access_token)
            
            if status_code == 200:
                return Ok(None)
            else:
                error_msg = response_data.get('message', 'Order cancellation failed')
                return Err(error_msg)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to cancel order: {str(e)}")
    
    def close_all_positions(self) -> Result[None, str]:
        """
        Close all open positions.
        
        Returns:
            Result[None, str]: Ok(None) on success, Err(str) on failure
        
        Requirements: 7.4
        """
        try:
            self._set_api_key_env()
            
            from fyers.api.order_api import close_all_positions as fyers_close_all
            
            response_data, status_code = fyers_close_all(self._api_key, self.access_token)
            
            if status_code == 200:
                return Ok(None)
            else:
                error_msg = response_data.get('message', 'Failed to close positions')
                return Err(error_msg)
        
        except ImportError:
            return Err("Fyers API module not available")
        except Exception as e:
            return Err(f"Failed to close positions: {str(e)}")
