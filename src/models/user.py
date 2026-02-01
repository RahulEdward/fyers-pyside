"""User and Session data models"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User account model"""
    id: int
    username: str
    email: str
    password_hash: str
    created_at: datetime
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)


@dataclass
class Session:
    """User session model"""
    user_id: int
    username: str
    created_at: datetime
    access_token: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
