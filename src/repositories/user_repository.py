"""User repository for database operations"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.schema import UserModel
from src.models.user import User


class UserRepository:
    """Repository for user database operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def create(self, username: str, password_hash: str, email: str) -> User:
        """
        Create a new user record
        
        Args:
            username: Unique username
            password_hash: Hashed password
            email: User email
            
        Returns:
            Created User object
            
        Raises:
            IntegrityError: If username already exists
        """
        user_model = UserModel(
            username=username,
            password_hash=password_hash,
            email=email,
            created_at=datetime.utcnow()
        )
        
        self.db_session.add(user_model)
        self.db_session.commit()
        self.db_session.refresh(user_model)
        
        return self._to_user(user_model)
    
    def find_by_username(self, username: str) -> Optional[User]:
        """
        Find user by username
        
        Args:
            username: Username to search
            
        Returns:
            User object if found, None otherwise
        """
        user_model = self.db_session.query(UserModel).filter(
            UserModel.username == username
        ).first()
        
        if user_model:
            return self._to_user(user_model)
        return None
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """
        Find user by ID
        
        Args:
            user_id: User ID to search
            
        Returns:
            User object if found, None otherwise
        """
        user_model = self.db_session.query(UserModel).filter(
            UserModel.id == user_id
        ).first()
        
        if user_model:
            return self._to_user(user_model)
        return None
    
    def exists(self, username: str) -> bool:
        """
        Check if username exists
        
        Args:
            username: Username to check
            
        Returns:
            True if exists, False otherwise
        """
        count = self.db_session.query(UserModel).filter(
            UserModel.username == username
        ).count()
        return count > 0
    
    def _to_user(self, model: UserModel) -> User:
        """Convert SQLAlchemy model to User dataclass"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            password_hash=model.password_hash,
            created_at=model.created_at
        )
