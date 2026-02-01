"""SQLAlchemy database schema models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserModel(Base):
    """User account table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    credentials = relationship("BrokerCredentialModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistModel", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_users_username', 'username'),
    )


class BrokerCredentialModel(Base):
    """Broker credentials table - stores Fyers login info and tokens"""
    __tablename__ = 'broker_credentials'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)
    broker_username = Column(String(100), unique=True, nullable=False, index=True)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_api_secret = Column(Text, nullable=False)
    
    # Fyers Tokens
    access_token = Column(Text, nullable=True)
    feed_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="credentials")
    
    __table_args__ = (
        Index('idx_credentials_user_id', 'user_id'),
        Index('idx_credentials_broker_username', 'broker_username'),
    )


class WatchlistModel(Base):
    """Watchlist table"""
    __tablename__ = 'watchlist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    symbol = Column(String(50), nullable=False)
    exchange = Column(String(20), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="watchlist_items")
    
    __table_args__ = (
        Index('idx_watchlist_user_id', 'user_id'),
        Index('idx_watchlist_user_symbol_exchange', 'user_id', 'symbol', 'exchange', unique=True),
    )


class SymTokenModel(Base):
    """Symbol Token table - Master contract data from Fyers"""
    __tablename__ = 'symtoken'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(100), nullable=False, index=True)
    brsymbol = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    exchange = Column(String(20), nullable=False, index=True)
    brexchange = Column(String(20), nullable=True, index=True)
    token = Column(String(100), nullable=False, index=True)
    expiry = Column(String(20), nullable=True)
    strike = Column(Float, nullable=True)
    lotsize = Column(Integer, nullable=True)
    instrumenttype = Column(String(20), nullable=True)
    tick_size = Column(Float, nullable=True)
    
    __table_args__ = (
        Index('idx_symbol_exchange', 'symbol', 'exchange'),
    )
