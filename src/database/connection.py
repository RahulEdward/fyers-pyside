"""Database connection management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .schema import Base

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'trading_system.db')

# Global engine and session factory
_engine = None
_session_factory = None


def get_database_url(db_path: str = None) -> str:
    """Get SQLite database URL"""
    path = db_path or os.getenv('DATABASE_PATH', DEFAULT_DB_PATH)
    return f"sqlite:///{path}"


def get_engine(db_path: str = None):
    """Get or create database engine"""
    global _engine
    if _engine is None:
        database_url = get_database_url(db_path)
        _engine = create_engine(
            database_url,
            echo=False,
            connect_args={"check_same_thread": False}  # Required for SQLite
        )
    return _engine


def get_session_factory(db_path: str = None):
    """Get or create session factory"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
    return _session_factory


def get_session():
    """Get a new database session"""
    factory = get_session_factory()
    return factory()


def init_db(db_path: str = None):
    """Initialize database - create all tables if not exist"""
    engine = get_engine(db_path)
    Base.metadata.create_all(bind=engine)
    return engine


def close_db():
    """Close database connections"""
    global _engine, _session_factory
    if _session_factory:
        _session_factory.remove()
        _session_factory = None
    if _engine:
        _engine.dispose()
        _engine = None
