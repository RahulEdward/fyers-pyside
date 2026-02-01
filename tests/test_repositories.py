"""Tests for repository classes - Database Layer Verification"""
import pytest
import os
import tempfile
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.database.schema import Base
from src.repositories.user_repository import UserRepository
from src.repositories.credential_repository import CredentialRepository
from src.repositories.watchlist_repository import WatchlistRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


class TestUserRepository:
    """Tests for UserRepository"""
    
    def test_create_user(self, db_session):
        """Test creating a new user"""
        repo = UserRepository(db_session)
        user = repo.create("testuser", "hashed_password_123", "test@example.com")
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password_123"
        assert isinstance(user.created_at, datetime)
    
    def test_find_by_username(self, db_session):
        """Test finding user by username"""
        repo = UserRepository(db_session)
        repo.create("findme", "password_hash", "find@example.com")
        
        found = repo.find_by_username("findme")
        assert found is not None
        assert found.username == "findme"
        assert found.email == "find@example.com"
    
    def test_find_by_username_not_found(self, db_session):
        """Test finding non-existent user returns None"""
        repo = UserRepository(db_session)
        found = repo.find_by_username("nonexistent")
        assert found is None
    
    def test_find_by_id(self, db_session):
        """Test finding user by ID"""
        repo = UserRepository(db_session)
        created = repo.create("iduser", "password_hash", "id@example.com")
        
        found = repo.find_by_id(created.id)
        assert found is not None
        assert found.id == created.id
        assert found.username == "iduser"
    
    def test_find_by_id_not_found(self, db_session):
        """Test finding non-existent ID returns None"""
        repo = UserRepository(db_session)
        found = repo.find_by_id(99999)
        assert found is None
    
    def test_exists_true(self, db_session):
        """Test exists returns True for existing user"""
        repo = UserRepository(db_session)
        repo.create("existsuser", "password_hash", "exists@example.com")
        
        assert repo.exists("existsuser") is True
    
    def test_exists_false(self, db_session):
        """Test exists returns False for non-existent user"""
        repo = UserRepository(db_session)
        assert repo.exists("nonexistent") is False
    
    def test_duplicate_username_raises_error(self, db_session):
        """Test that duplicate username raises IntegrityError"""
        repo = UserRepository(db_session)
        repo.create("duplicate", "password_hash", "first@example.com")
        
        with pytest.raises(IntegrityError):
            repo.create("duplicate", "password_hash", "second@example.com")


class TestCredentialRepository:
    """Tests for CredentialRepository"""
    
    def _create_test_user(self, db_session, username="creduser"):
        """Helper to create a test user"""
        user_repo = UserRepository(db_session)
        return user_repo.create(username, "password_hash", f"{username}@example.com")
    
    def test_save_credentials(self, db_session):
        """Test saving new credentials"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "encrypted_key_123", "encrypted_secret_456")
        
        creds = repo.get(user.id)
        assert creds is not None
        assert creds.user_id == user.id
        assert creds.encrypted_api_key == "encrypted_key_123"
        assert creds.encrypted_api_secret == "encrypted_secret_456"
    
    def test_save_updates_existing(self, db_session):
        """Test saving credentials updates existing record"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "old_key", "old_secret")
        repo.save(user.id, "new_key", "new_secret")
        
        creds = repo.get(user.id)
        assert creds.encrypted_api_key == "new_key"
        assert creds.encrypted_api_secret == "new_secret"
    
    def test_get_nonexistent(self, db_session):
        """Test getting credentials for user without credentials"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        creds = repo.get(user.id)
        assert creds is None
    
    def test_exists_true(self, db_session):
        """Test exists returns True when credentials exist"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "key", "secret")
        assert repo.exists(user.id) is True
    
    def test_exists_false(self, db_session):
        """Test exists returns False when no credentials"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        assert repo.exists(user.id) is False
    
    def test_update_access_token(self, db_session):
        """Test updating access token"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "key", "secret")
        repo.update_access_token(user.id, "new_access_token_xyz")
        
        creds = repo.get(user.id)
        assert creds.access_token == "new_access_token_xyz"
    
    def test_get_access_token(self, db_session):
        """Test getting access token"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "key", "secret")
        repo.update_access_token(user.id, "token_123")
        
        token = repo.get_access_token(user.id)
        assert token == "token_123"
    
    def test_get_access_token_none(self, db_session):
        """Test getting access token when not set"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "key", "secret")
        token = repo.get_access_token(user.id)
        assert token is None
    
    def test_delete_credentials(self, db_session):
        """Test deleting credentials"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        repo.save(user.id, "key", "secret")
        result = repo.delete(user.id)
        
        assert result is True
        assert repo.exists(user.id) is False
    
    def test_delete_nonexistent(self, db_session):
        """Test deleting non-existent credentials"""
        user = self._create_test_user(db_session)
        repo = CredentialRepository(db_session)
        
        result = repo.delete(user.id)
        assert result is False


class TestWatchlistRepository:
    """Tests for WatchlistRepository"""
    
    def _create_test_user(self, db_session, username="watchuser"):
        """Helper to create a test user"""
        user_repo = UserRepository(db_session)
        return user_repo.create(username, "password_hash", f"{username}@example.com")
    
    def test_add_item(self, db_session):
        """Test adding item to watchlist"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        item = repo.add(user.id, "RELIANCE", "NSE")
        
        assert item.id is not None
        assert item.user_id == user.id
        assert item.symbol == "RELIANCE"
        assert item.exchange == "NSE"
        assert isinstance(item.added_at, datetime)
    
    def test_remove_item(self, db_session):
        """Test removing item from watchlist"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        repo.add(user.id, "INFY", "NSE")
        result = repo.remove(user.id, "INFY", "NSE")
        
        assert result is True
        assert repo.exists(user.id, "INFY", "NSE") is False
    
    def test_remove_nonexistent(self, db_session):
        """Test removing non-existent item"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        result = repo.remove(user.id, "NONEXISTENT", "NSE")
        assert result is False
    
    def test_get_all(self, db_session):
        """Test getting all watchlist items"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        repo.add(user.id, "RELIANCE", "NSE")
        repo.add(user.id, "TCS", "NSE")
        repo.add(user.id, "INFY", "BSE")
        
        items = repo.get_all(user.id)
        
        assert len(items) == 3
        symbols = [item.symbol for item in items]
        assert "RELIANCE" in symbols
        assert "TCS" in symbols
        assert "INFY" in symbols
    
    def test_get_all_empty(self, db_session):
        """Test getting watchlist when empty"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        items = repo.get_all(user.id)
        assert items == []
    
    def test_exists_true(self, db_session):
        """Test exists returns True for existing item"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        repo.add(user.id, "HDFC", "NSE")
        assert repo.exists(user.id, "HDFC", "NSE") is True
    
    def test_exists_false(self, db_session):
        """Test exists returns False for non-existent item"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        assert repo.exists(user.id, "NONEXISTENT", "NSE") is False
    
    def test_get_by_id(self, db_session):
        """Test getting item by ID"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        added = repo.add(user.id, "SBIN", "NSE")
        found = repo.get_by_id(added.id)
        
        assert found is not None
        assert found.id == added.id
        assert found.symbol == "SBIN"
    
    def test_get_by_id_not_found(self, db_session):
        """Test getting non-existent ID"""
        repo = WatchlistRepository(db_session)
        found = repo.get_by_id(99999)
        assert found is None
    
    def test_clear_all(self, db_session):
        """Test clearing all watchlist items"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        repo.add(user.id, "A", "NSE")
        repo.add(user.id, "B", "NSE")
        repo.add(user.id, "C", "NSE")
        
        count = repo.clear_all(user.id)
        
        assert count == 3
        assert repo.get_all(user.id) == []
    
    def test_duplicate_item_raises_error(self, db_session):
        """Test that duplicate watchlist item raises IntegrityError"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        repo.add(user.id, "DUPLICATE", "NSE")
        
        with pytest.raises(IntegrityError):
            repo.add(user.id, "DUPLICATE", "NSE")
    
    def test_same_symbol_different_exchange(self, db_session):
        """Test same symbol on different exchanges is allowed"""
        user = self._create_test_user(db_session)
        repo = WatchlistRepository(db_session)
        
        item1 = repo.add(user.id, "RELIANCE", "NSE")
        item2 = repo.add(user.id, "RELIANCE", "BSE")
        
        assert item1.id != item2.id
        items = repo.get_all(user.id)
        assert len(items) == 2
    
    def test_different_users_same_symbol(self, db_session):
        """Test different users can have same symbol"""
        user1 = self._create_test_user(db_session, "user1")
        user2 = self._create_test_user(db_session, "user2")
        repo = WatchlistRepository(db_session)
        
        item1 = repo.add(user1.id, "TCS", "NSE")
        item2 = repo.add(user2.id, "TCS", "NSE")
        
        assert item1.id != item2.id
        assert len(repo.get_all(user1.id)) == 1
        assert len(repo.get_all(user2.id)) == 1
