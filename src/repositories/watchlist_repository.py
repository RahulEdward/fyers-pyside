"""Watchlist repository for database operations"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.schema import WatchlistModel
from src.models.watchlist import WatchlistItem


class WatchlistRepository:
    """Repository for watchlist database operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def add(self, user_id: int, symbol: str, exchange: str) -> WatchlistItem:
        """
        Add item to watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            Created WatchlistItem
            
        Raises:
            IntegrityError: If item already exists
        """
        watchlist_model = WatchlistModel(
            user_id=user_id,
            symbol=symbol,
            exchange=exchange,
            added_at=datetime.utcnow()
        )
        
        self.db_session.add(watchlist_model)
        self.db_session.commit()
        self.db_session.refresh(watchlist_model)
        
        return self._to_watchlist_item(watchlist_model)
    
    def remove(self, user_id: int, symbol: str, exchange: str) -> bool:
        """
        Remove item from watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            True if removed, False if not found
        """
        result = self.db_session.query(WatchlistModel).filter(
            WatchlistModel.user_id == user_id,
            WatchlistModel.symbol == symbol,
            WatchlistModel.exchange == exchange
        ).delete()
        self.db_session.commit()
        return result > 0
    
    def get_all(self, user_id: int) -> List[WatchlistItem]:
        """
        Get all watchlist items for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of WatchlistItem objects
        """
        models = self.db_session.query(WatchlistModel).filter(
            WatchlistModel.user_id == user_id
        ).order_by(WatchlistModel.added_at.desc()).all()
        
        return [self._to_watchlist_item(m) for m in models]
    
    def exists(self, user_id: int, symbol: str, exchange: str) -> bool:
        """
        Check if item exists in watchlist
        
        Args:
            user_id: User ID
            symbol: Trading symbol
            exchange: Exchange name
            
        Returns:
            True if exists, False otherwise
        """
        count = self.db_session.query(WatchlistModel).filter(
            WatchlistModel.user_id == user_id,
            WatchlistModel.symbol == symbol,
            WatchlistModel.exchange == exchange
        ).count()
        return count > 0
    
    def get_by_id(self, item_id: int) -> Optional[WatchlistItem]:
        """
        Get watchlist item by ID
        
        Args:
            item_id: Watchlist item ID
            
        Returns:
            WatchlistItem if found, None otherwise
        """
        model = self.db_session.query(WatchlistModel).filter(
            WatchlistModel.id == item_id
        ).first()
        
        if model:
            return self._to_watchlist_item(model)
        return None
    
    def clear_all(self, user_id: int) -> int:
        """
        Clear all watchlist items for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of items deleted
        """
        result = self.db_session.query(WatchlistModel).filter(
            WatchlistModel.user_id == user_id
        ).delete()
        self.db_session.commit()
        return result
    
    def _to_watchlist_item(self, model: WatchlistModel) -> WatchlistItem:
        """Convert SQLAlchemy model to WatchlistItem dataclass"""
        return WatchlistItem(
            id=model.id,
            user_id=model.user_id,
            symbol=model.symbol,
            exchange=model.exchange,
            added_at=model.added_at
        )
