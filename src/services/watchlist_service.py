"""Watchlist service for managing user watchlists"""
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.watchlist import WatchlistItem, SymbolInfo
from src.models.result import Result, Ok, Err
from src.repositories.watchlist_repository import WatchlistRepository


class WatchlistService:
    """Service for managing user watchlists"""
    
    # Valid exchanges for Fyers
    VALID_EXCHANGES = ['NSE', 'BSE', 'NFO', 'BFO', 'MCX', 'CDS', 'NSE_INDEX', 'BSE_INDEX']
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.watchlist_repo = WatchlistRepository(db_session)
    
    def add_symbol(self, user_id: int, symbol: str, exchange: str) -> Result[WatchlistItem, str]:
        """
        Add symbol to user's watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            Result with WatchlistItem on success, error message on failure
        """
        # Validate inputs
        if not symbol or not symbol.strip():
            return Err("Symbol cannot be empty")
        
        if not exchange or not exchange.strip():
            return Err("Exchange cannot be empty")
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        # Validate exchange
        if exchange not in self.VALID_EXCHANGES:
            return Err(f"Invalid exchange: {exchange}. Valid exchanges: {', '.join(self.VALID_EXCHANGES)}")
        
        # Check if already in watchlist
        if self.watchlist_repo.exists(user_id, symbol, exchange):
            return Err(f"Symbol {symbol} on {exchange} is already in your watchlist")
        
        try:
            item = self.watchlist_repo.add(user_id, symbol, exchange)
            return Ok(item)
        except Exception as e:
            return Err(f"Failed to add symbol: {str(e)}")
    
    def remove_symbol(self, user_id: int, symbol: str, exchange: str) -> Result[bool, str]:
        """
        Remove symbol from user's watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            Result with True on success, error message on failure
        """
        if not symbol or not symbol.strip():
            return Err("Symbol cannot be empty")
        
        if not exchange or not exchange.strip():
            return Err("Exchange cannot be empty")
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        try:
            removed = self.watchlist_repo.remove(user_id, symbol, exchange)
            if removed:
                return Ok(True)
            else:
                return Err(f"Symbol {symbol} on {exchange} not found in watchlist")
        except Exception as e:
            return Err(f"Failed to remove symbol: {str(e)}")
    
    def get_watchlist(self, user_id: int) -> Result[List[WatchlistItem], str]:
        """
        Get user's watchlist
        
        Args:
            user_id: User ID
            
        Returns:
            Result with list of WatchlistItems on success, error message on failure
        """
        try:
            items = self.watchlist_repo.get_all(user_id)
            return Ok(items)
        except Exception as e:
            return Err(f"Failed to get watchlist: {str(e)}")
    
    def search_symbols(self, query: str, exchange: str) -> Result[List[SymbolInfo], str]:
        """
        Search for symbols in master contract database
        
        Args:
            query: Search query (symbol name)
            exchange: Exchange to search in
            
        Returns:
            Result with list of SymbolInfo on success, error message on failure
        """
        if not query or not query.strip():
            return Err("Search query cannot be empty")
        
        if not exchange or not exchange.strip():
            return Err("Exchange cannot be empty")
        
        query = query.strip().upper()
        exchange = exchange.strip().upper()
        
        if exchange not in self.VALID_EXCHANGES:
            return Err(f"Invalid exchange: {exchange}")
        
        try:
            # Search in local database using SQLAlchemy
            # This is a simplified implementation that searches the local watchlist
            # In production, this would query the master contract database
            results = self._search_local_symbols(query, exchange)
            return Ok(results)
        except Exception as e:
            return Err(f"Failed to search symbols: {str(e)}")
    
    def _search_local_symbols(self, query: str, exchange: str) -> List[SymbolInfo]:
        """
        Search symbols in local database
        
        This is a placeholder implementation. In production, this would
        query the master contract database from fyers/database/master_contract_db.py
        """
        # Return empty list - actual implementation would query master contract DB
        # The master contract DB uses a different database connection
        return []
    
    def clear_watchlist(self, user_id: int) -> Result[int, str]:
        """
        Clear all items from user's watchlist
        
        Args:
            user_id: User ID
            
        Returns:
            Result with count of deleted items on success, error message on failure
        """
        try:
            count = self.watchlist_repo.clear_all(user_id)
            return Ok(count)
        except Exception as e:
            return Err(f"Failed to clear watchlist: {str(e)}")
    
    def symbol_exists_in_watchlist(self, user_id: int, symbol: str, exchange: str) -> bool:
        """
        Check if symbol exists in user's watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            True if exists, False otherwise
        """
        if not symbol or not exchange:
            return False
        
        symbol = symbol.strip().upper()
        exchange = exchange.strip().upper()
        
        return self.watchlist_repo.exists(user_id, symbol, exchange)
