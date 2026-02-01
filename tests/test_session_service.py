"""
Unit tests for SessionService.

Tests the session management functionality including session creation,
retrieval, clearing, and authentication state checks.

Requirements: 3.1, 3.2, 3.4
"""

import pytest
from datetime import datetime

from src.services.session_service import SessionService
from src.models.user import User, Session


class TestSessionService:
    """Unit tests for SessionService."""
    
    @pytest.fixture
    def session_service(self):
        """Create a fresh SessionService instance for each test."""
        return SessionService()
    
    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        return User(
            id=1,
            username="test_trader",
            email="trader@example.com",
            password_hash="hashed_password_123",
            created_at=datetime.now()
        )
    
    @pytest.fixture
    def another_user(self):
        """Create another sample user for testing."""
        return User(
            id=2,
            username="another_trader",
            email="another@example.com",
            password_hash="hashed_password_456",
            created_at=datetime.now()
        )
    
    # Initialization tests
    def test_init_creates_service_with_no_session(self, session_service):
        """Test that SessionService initializes with no active session."""
        assert session_service._current_session is None
    
    def test_init_is_not_authenticated(self, session_service):
        """Test that new SessionService is not authenticated."""
        assert session_service.is_authenticated() is False
    
    # create_session tests
    def test_create_session_returns_session(self, session_service, sample_user):
        """Test that create_session returns a Session object."""
        session = session_service.create_session(sample_user)
        assert isinstance(session, Session)
    
    def test_create_session_contains_user_id(self, session_service, sample_user):
        """Test that created session contains correct user_id."""
        session = session_service.create_session(sample_user)
        assert session.user_id == sample_user.id
    
    def test_create_session_contains_username(self, session_service, sample_user):
        """Test that created session contains correct username."""
        session = session_service.create_session(sample_user)
        assert session.username == sample_user.username
    
    def test_create_session_has_created_at(self, session_service, sample_user):
        """Test that created session has a created_at timestamp."""
        before = datetime.now()
        session = session_service.create_session(sample_user)
        after = datetime.now()
        
        assert session.created_at is not None
        assert before <= session.created_at <= after
    
    def test_create_session_access_token_is_none(self, session_service, sample_user):
        """Test that created session has no access token initially."""
        session = session_service.create_session(sample_user)
        assert session.access_token is None
    
    def test_create_session_with_none_user_raises_error(self, session_service):
        """Test that creating session with None user raises ValueError."""
        with pytest.raises(ValueError, match="Cannot create session for None user"):
            session_service.create_session(None)
    
    def test_create_session_sets_authenticated(self, session_service, sample_user):
        """Test that creating session sets authenticated state to True."""
        session_service.create_session(sample_user)
        assert session_service.is_authenticated() is True
    
    def test_create_session_replaces_existing_session(self, session_service, sample_user, another_user):
        """Test that creating a new session replaces the existing one."""
        session_service.create_session(sample_user)
        session_service.create_session(another_user)
        
        current = session_service.get_current_session()
        assert current.user_id == another_user.id
        assert current.username == another_user.username
    
    # get_current_session tests
    def test_get_current_session_returns_none_when_no_session(self, session_service):
        """Test that get_current_session returns None when no session exists."""
        assert session_service.get_current_session() is None
    
    def test_get_current_session_returns_session_after_create(self, session_service, sample_user):
        """Test that get_current_session returns the created session."""
        created_session = session_service.create_session(sample_user)
        retrieved_session = session_service.get_current_session()
        
        assert retrieved_session is created_session
    
    def test_get_current_session_persists_across_calls(self, session_service, sample_user):
        """Test that session persists across multiple get_current_session calls."""
        session_service.create_session(sample_user)
        
        session1 = session_service.get_current_session()
        session2 = session_service.get_current_session()
        
        assert session1 is session2
    
    # clear_session tests
    def test_clear_session_removes_session(self, session_service, sample_user):
        """Test that clear_session removes the active session."""
        session_service.create_session(sample_user)
        session_service.clear_session()
        
        assert session_service.get_current_session() is None
    
    def test_clear_session_sets_not_authenticated(self, session_service, sample_user):
        """Test that clear_session sets authenticated state to False."""
        session_service.create_session(sample_user)
        session_service.clear_session()
        
        assert session_service.is_authenticated() is False
    
    def test_clear_session_when_no_session_does_not_raise(self, session_service):
        """Test that clear_session does not raise when no session exists."""
        # Should not raise any exception
        session_service.clear_session()
        assert session_service.get_current_session() is None
    
    def test_clear_session_can_be_called_multiple_times(self, session_service, sample_user):
        """Test that clear_session can be called multiple times safely."""
        session_service.create_session(sample_user)
        session_service.clear_session()
        session_service.clear_session()
        session_service.clear_session()
        
        assert session_service.is_authenticated() is False
    
    # is_authenticated tests
    def test_is_authenticated_false_initially(self, session_service):
        """Test that is_authenticated returns False initially."""
        assert session_service.is_authenticated() is False
    
    def test_is_authenticated_true_after_create_session(self, session_service, sample_user):
        """Test that is_authenticated returns True after creating session."""
        session_service.create_session(sample_user)
        assert session_service.is_authenticated() is True
    
    def test_is_authenticated_false_after_clear_session(self, session_service, sample_user):
        """Test that is_authenticated returns False after clearing session."""
        session_service.create_session(sample_user)
        session_service.clear_session()
        assert session_service.is_authenticated() is False
    
    # set_access_token tests
    def test_set_access_token_stores_token(self, session_service, sample_user):
        """Test that set_access_token stores the token in session."""
        session_service.create_session(sample_user)
        session_service.set_access_token("test_access_token_123")
        
        session = session_service.get_current_session()
        assert session.access_token == "test_access_token_123"
    
    def test_set_access_token_without_session_raises_error(self, session_service):
        """Test that set_access_token raises error when no session exists."""
        with pytest.raises(ValueError, match="Cannot set access token: no active session"):
            session_service.set_access_token("test_token")
    
    def test_set_access_token_with_empty_token_raises_error(self, session_service, sample_user):
        """Test that set_access_token raises error for empty token."""
        session_service.create_session(sample_user)
        with pytest.raises(ValueError, match="Access token cannot be empty"):
            session_service.set_access_token("")
    
    def test_set_access_token_with_none_raises_error(self, session_service, sample_user):
        """Test that set_access_token raises error for None token."""
        session_service.create_session(sample_user)
        with pytest.raises(ValueError, match="Access token cannot be empty"):
            session_service.set_access_token(None)
    
    def test_set_access_token_can_be_updated(self, session_service, sample_user):
        """Test that access token can be updated."""
        session_service.create_session(sample_user)
        session_service.set_access_token("first_token")
        session_service.set_access_token("second_token")
        
        assert session_service.get_access_token() == "second_token"
    
    # get_access_token tests
    def test_get_access_token_returns_none_when_no_session(self, session_service):
        """Test that get_access_token returns None when no session exists."""
        assert session_service.get_access_token() is None
    
    def test_get_access_token_returns_none_when_not_set(self, session_service, sample_user):
        """Test that get_access_token returns None when token not set."""
        session_service.create_session(sample_user)
        assert session_service.get_access_token() is None
    
    def test_get_access_token_returns_token_when_set(self, session_service, sample_user):
        """Test that get_access_token returns the token when set."""
        session_service.create_session(sample_user)
        session_service.set_access_token("my_access_token")
        
        assert session_service.get_access_token() == "my_access_token"
    
    # Session persistence tests (Property 7: Session Persistence Across Navigation)
    def test_session_persists_across_multiple_operations(self, session_service, sample_user):
        """Test that session persists across multiple service operations."""
        session_service.create_session(sample_user)
        
        # Simulate multiple "navigation" operations by checking session multiple times
        assert session_service.is_authenticated() is True
        assert session_service.get_current_session().user_id == sample_user.id
        assert session_service.is_authenticated() is True
        assert session_service.get_current_session().username == sample_user.username
        assert session_service.is_authenticated() is True
    
    # Logout clears session tests (Property 8: Logout Clears Session)
    def test_logout_flow_clears_all_session_data(self, session_service, sample_user):
        """Test that logout (clear_session) clears all session data."""
        # Login
        session_service.create_session(sample_user)
        session_service.set_access_token("broker_token")
        
        # Verify logged in
        assert session_service.is_authenticated() is True
        assert session_service.get_access_token() == "broker_token"
        
        # Logout
        session_service.clear_session()
        
        # Verify logged out
        assert session_service.is_authenticated() is False
        assert session_service.get_current_session() is None
        assert session_service.get_access_token() is None
    
    # Edge cases
    def test_session_with_special_characters_in_username(self, session_service):
        """Test session creation with special characters in username."""
        user = User(
            id=1,
            username="trader_123!@#",
            email="trader@example.com",
            password_hash="hash",
            created_at=datetime.now()
        )
        session = session_service.create_session(user)
        assert session.username == "trader_123!@#"
    
    def test_session_with_unicode_username(self, session_service):
        """Test session creation with Unicode username."""
        user = User(
            id=1,
            username="व्यापारी_trader",
            email="trader@example.com",
            password_hash="hash",
            created_at=datetime.now()
        )
        session = session_service.create_session(user)
        assert session.username == "व्यापारी_trader"
