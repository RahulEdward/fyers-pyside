"""
Unit tests for AuthService.

Tests the authentication functionality including user registration,
login, and logout operations.

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.2
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.schema import Base
from src.repositories.user_repository import UserRepository
from src.services.session_service import SessionService
from src.services.auth_service import AuthService, validate_email
from src.models.user import User, Session
from src.models.result import Ok, Err


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def user_repo(db_session):
    """Create a UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
def session_service():
    """Create a SessionService instance."""
    return SessionService()


@pytest.fixture
def auth_service(user_repo, session_service):
    """Create an AuthService instance."""
    return AuthService(user_repo, session_service)


class TestValidateEmail:
    """Tests for email validation function."""
    
    def test_valid_email_simple(self):
        """Test valid simple email."""
        assert validate_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        """Test valid email with subdomain."""
        assert validate_email("user@mail.example.com") is True
    
    def test_valid_email_with_plus(self):
        """Test valid email with plus sign."""
        assert validate_email("user+tag@example.com") is True
    
    def test_valid_email_with_dots(self):
        """Test valid email with dots in local part."""
        assert validate_email("first.last@example.com") is True
    
    def test_valid_email_with_numbers(self):
        """Test valid email with numbers."""
        assert validate_email("user123@example456.com") is True
    
    def test_invalid_email_no_at(self):
        """Test invalid email without @ symbol."""
        assert validate_email("userexample.com") is False
    
    def test_invalid_email_no_domain(self):
        """Test invalid email without domain."""
        assert validate_email("user@") is False
    
    def test_invalid_email_no_tld(self):
        """Test invalid email without TLD."""
        assert validate_email("user@example") is False
    
    def test_invalid_email_empty(self):
        """Test empty email."""
        assert validate_email("") is False
    
    def test_invalid_email_none(self):
        """Test None email."""
        assert validate_email(None) is False
    
    def test_invalid_email_spaces(self):
        """Test email with spaces."""
        assert validate_email("user @example.com") is False
    
    def test_invalid_email_double_at(self):
        """Test email with double @ symbol."""
        assert validate_email("user@@example.com") is False


class TestAuthServiceInit:
    """Tests for AuthService initialization."""
    
    def test_init_with_valid_dependencies(self, user_repo, session_service):
        """Test initialization with valid dependencies."""
        auth = AuthService(user_repo, session_service)
        assert auth._user_repo is user_repo
        assert auth._session_service is session_service
    
    def test_init_with_none_user_repo_raises_error(self, session_service):
        """Test initialization with None user_repo raises ValueError."""
        with pytest.raises(ValueError, match="user_repo cannot be None"):
            AuthService(None, session_service)
    
    def test_init_with_none_session_service_raises_error(self, user_repo):
        """Test initialization with None session_service raises ValueError."""
        with pytest.raises(ValueError, match="session_service cannot be None"):
            AuthService(user_repo, None)


class TestAuthServiceRegister:
    """Tests for AuthService.register() method."""
    
    # Requirement 1.1: Validate all fields are non-empty
    def test_register_success(self, auth_service):
        """Test successful registration."""
        result = auth_service.register("testuser", "password123", "test@example.com")
        
        assert result.is_ok()
        user = result.value
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.id is not None
    
    def test_register_empty_username_fails(self, auth_service):
        """Test registration with empty username fails."""
        result = auth_service.register("", "password123", "test@example.com")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_register_whitespace_username_fails(self, auth_service):
        """Test registration with whitespace-only username fails."""
        result = auth_service.register("   ", "password123", "test@example.com")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_register_none_username_fails(self, auth_service):
        """Test registration with None username fails."""
        result = auth_service.register(None, "password123", "test@example.com")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_register_empty_password_fails(self, auth_service):
        """Test registration with empty password fails."""
        result = auth_service.register("testuser", "", "test@example.com")
        
        assert result.is_err()
        assert result.error == "Password cannot be empty"
    
    def test_register_none_password_fails(self, auth_service):
        """Test registration with None password fails."""
        result = auth_service.register("testuser", None, "test@example.com")
        
        assert result.is_err()
        assert result.error == "Password cannot be empty"
    
    def test_register_empty_email_fails(self, auth_service):
        """Test registration with empty email fails."""
        result = auth_service.register("testuser", "password123", "")
        
        assert result.is_err()
        assert result.error == "Email cannot be empty"
    
    def test_register_whitespace_email_fails(self, auth_service):
        """Test registration with whitespace-only email fails."""
        result = auth_service.register("testuser", "password123", "   ")
        
        assert result.is_err()
        assert result.error == "Email cannot be empty"
    
    def test_register_none_email_fails(self, auth_service):
        """Test registration with None email fails."""
        result = auth_service.register("testuser", "password123", None)
        
        assert result.is_err()
        assert result.error == "Email cannot be empty"
    
    # Requirement 1.1: Validate email format
    def test_register_invalid_email_format_fails(self, auth_service):
        """Test registration with invalid email format fails."""
        result = auth_service.register("testuser", "password123", "invalid-email")
        
        assert result.is_err()
        assert result.error == "Invalid email format"
    
    def test_register_email_without_at_fails(self, auth_service):
        """Test registration with email without @ fails."""
        result = auth_service.register("testuser", "password123", "testexample.com")
        
        assert result.is_err()
        assert result.error == "Invalid email format"
    
    def test_register_email_without_domain_fails(self, auth_service):
        """Test registration with email without domain fails."""
        result = auth_service.register("testuser", "password123", "test@")
        
        assert result.is_err()
        assert result.error == "Invalid email format"
    
    # Requirement 1.2: Password is hashed before storage
    def test_register_password_is_hashed(self, auth_service):
        """Test that password is hashed before storage."""
        result = auth_service.register("testuser", "password123", "test@example.com")
        
        assert result.is_ok()
        user = result.value
        # Password hash should be different from original password
        assert user.password_hash != "password123"
        # Password hash should be a bcrypt hash (starts with $2b$)
        assert user.password_hash.startswith("$2b$")
    
    # Requirement 1.3: Reject duplicate username
    def test_register_duplicate_username_fails(self, auth_service):
        """Test registration with duplicate username fails."""
        # First registration should succeed
        result1 = auth_service.register("duplicate", "password123", "first@example.com")
        assert result1.is_ok()
        
        # Second registration with same username should fail
        result2 = auth_service.register("duplicate", "password456", "second@example.com")
        assert result2.is_err()
        assert result2.error == "Username already exists"
    
    def test_register_duplicate_username_case_sensitive(self, auth_service):
        """Test that username comparison is case-sensitive."""
        result1 = auth_service.register("TestUser", "password123", "first@example.com")
        assert result1.is_ok()
        
        # Different case should be allowed (case-sensitive)
        result2 = auth_service.register("testuser", "password456", "second@example.com")
        assert result2.is_ok()
    
    # Requirement 1.4: Store user data in database
    def test_register_stores_user_in_database(self, auth_service, user_repo):
        """Test that registration stores user in database."""
        result = auth_service.register("dbuser", "password123", "db@example.com")
        
        assert result.is_ok()
        
        # Verify user exists in database
        found = user_repo.find_by_username("dbuser")
        assert found is not None
        assert found.username == "dbuser"
        assert found.email == "db@example.com"
    
    # Edge cases
    def test_register_trims_username(self, auth_service):
        """Test that username is trimmed."""
        result = auth_service.register("  trimmed  ", "password123", "trim@example.com")
        
        assert result.is_ok()
        assert result.value.username == "trimmed"
    
    def test_register_trims_email(self, auth_service):
        """Test that email is trimmed."""
        result = auth_service.register("testuser", "password123", "  trim@example.com  ")
        
        assert result.is_ok()
        assert result.value.email == "trim@example.com"
    
    def test_register_with_special_characters_in_username(self, auth_service):
        """Test registration with special characters in username."""
        result = auth_service.register("user_123", "password123", "special@example.com")
        
        assert result.is_ok()
        assert result.value.username == "user_123"
    
    def test_register_with_unicode_username(self, auth_service):
        """Test registration with Unicode username."""
        result = auth_service.register("व्यापारी", "password123", "hindi@example.com")
        
        assert result.is_ok()
        assert result.value.username == "व्यापारी"


class TestAuthServiceLogin:
    """Tests for AuthService.login() method."""
    
    @pytest.fixture
    def registered_user(self, auth_service):
        """Create a registered user for login tests."""
        result = auth_service.register("loginuser", "correct_password", "login@example.com")
        return result.value
    
    # Requirement 2.1: Validate credentials against stored data
    def test_login_success(self, auth_service, registered_user):
        """Test successful login."""
        result = auth_service.login("loginuser", "correct_password")
        
        assert result.is_ok()
        session = result.value
        assert session.user_id == registered_user.id
        assert session.username == "loginuser"
    
    def test_login_wrong_password_fails(self, auth_service, registered_user):
        """Test login with wrong password fails."""
        result = auth_service.login("loginuser", "wrong_password")
        
        assert result.is_err()
        assert result.error == "Invalid username or password"
    
    def test_login_nonexistent_user_fails(self, auth_service):
        """Test login with non-existent user fails."""
        result = auth_service.login("nonexistent", "password123")
        
        assert result.is_err()
        assert result.error == "Invalid username or password"
    
    def test_login_empty_username_fails(self, auth_service, registered_user):
        """Test login with empty username fails."""
        result = auth_service.login("", "correct_password")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_login_whitespace_username_fails(self, auth_service, registered_user):
        """Test login with whitespace-only username fails."""
        result = auth_service.login("   ", "correct_password")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_login_none_username_fails(self, auth_service, registered_user):
        """Test login with None username fails."""
        result = auth_service.login(None, "correct_password")
        
        assert result.is_err()
        assert result.error == "Username cannot be empty"
    
    def test_login_empty_password_fails(self, auth_service, registered_user):
        """Test login with empty password fails."""
        result = auth_service.login("loginuser", "")
        
        assert result.is_err()
        assert result.error == "Password cannot be empty"
    
    def test_login_none_password_fails(self, auth_service, registered_user):
        """Test login with None password fails."""
        result = auth_service.login("loginuser", None)
        
        assert result.is_err()
        assert result.error == "Password cannot be empty"
    
    # Requirement 2.2: Create session on successful login
    def test_login_creates_session(self, auth_service, registered_user, session_service):
        """Test that successful login creates a session."""
        result = auth_service.login("loginuser", "correct_password")
        
        assert result.is_ok()
        assert session_service.is_authenticated() is True
        
        current_session = session_service.get_current_session()
        assert current_session is not None
        assert current_session.user_id == registered_user.id
    
    def test_login_session_has_correct_data(self, auth_service, registered_user):
        """Test that login session contains correct user data."""
        result = auth_service.login("loginuser", "correct_password")
        
        assert result.is_ok()
        session = result.value
        assert session.user_id == registered_user.id
        assert session.username == "loginuser"
        assert session.created_at is not None
        assert session.access_token is None  # Not set until broker auth
    
    # Requirement 2.3: Error message for invalid credentials
    def test_login_error_message_is_generic(self, auth_service, registered_user):
        """Test that error message doesn't reveal if username exists."""
        # Wrong password for existing user
        result1 = auth_service.login("loginuser", "wrong_password")
        
        # Non-existent user
        result2 = auth_service.login("nonexistent", "password123")
        
        # Both should have the same error message (security best practice)
        assert result1.error == result2.error == "Invalid username or password"
    
    # Edge cases
    def test_login_trims_username(self, auth_service, registered_user):
        """Test that username is trimmed during login."""
        result = auth_service.login("  loginuser  ", "correct_password")
        
        assert result.is_ok()
        assert result.value.username == "loginuser"
    
    def test_login_password_is_case_sensitive(self, auth_service, registered_user):
        """Test that password comparison is case-sensitive."""
        result = auth_service.login("loginuser", "CORRECT_PASSWORD")
        
        assert result.is_err()
        assert result.error == "Invalid username or password"
    
    def test_login_multiple_times(self, auth_service, registered_user, session_service):
        """Test that user can login multiple times."""
        result1 = auth_service.login("loginuser", "correct_password")
        assert result1.is_ok()
        
        auth_service.logout()
        
        result2 = auth_service.login("loginuser", "correct_password")
        assert result2.is_ok()
        assert session_service.is_authenticated() is True


class TestAuthServiceLogout:
    """Tests for AuthService.logout() method."""
    
    @pytest.fixture
    def logged_in_user(self, auth_service):
        """Create and login a user."""
        auth_service.register("logoutuser", "password123", "logout@example.com")
        auth_service.login("logoutuser", "password123")
        return auth_service
    
    # Requirement 3.2: Clear session data on logout
    def test_logout_clears_session(self, logged_in_user, session_service):
        """Test that logout clears the session."""
        assert session_service.is_authenticated() is True
        
        logged_in_user.logout()
        
        assert session_service.is_authenticated() is False
        assert session_service.get_current_session() is None
    
    def test_logout_when_not_logged_in(self, auth_service, session_service):
        """Test that logout when not logged in doesn't raise error."""
        assert session_service.is_authenticated() is False
        
        # Should not raise any exception
        auth_service.logout()
        
        assert session_service.is_authenticated() is False
    
    def test_logout_multiple_times(self, logged_in_user, session_service):
        """Test that logout can be called multiple times."""
        logged_in_user.logout()
        logged_in_user.logout()
        logged_in_user.logout()
        
        assert session_service.is_authenticated() is False


class TestAuthServiceHelperMethods:
    """Tests for AuthService helper methods."""
    
    def test_is_authenticated_false_initially(self, auth_service):
        """Test is_authenticated returns False initially."""
        assert auth_service.is_authenticated() is False
    
    def test_is_authenticated_true_after_login(self, auth_service):
        """Test is_authenticated returns True after login."""
        auth_service.register("authuser", "password123", "auth@example.com")
        auth_service.login("authuser", "password123")
        
        assert auth_service.is_authenticated() is True
    
    def test_is_authenticated_false_after_logout(self, auth_service):
        """Test is_authenticated returns False after logout."""
        auth_service.register("authuser", "password123", "auth@example.com")
        auth_service.login("authuser", "password123")
        auth_service.logout()
        
        assert auth_service.is_authenticated() is False
    
    def test_get_current_session_none_initially(self, auth_service):
        """Test get_current_session returns None initially."""
        assert auth_service.get_current_session() is None
    
    def test_get_current_session_after_login(self, auth_service):
        """Test get_current_session returns session after login."""
        auth_service.register("sessionuser", "password123", "session@example.com")
        auth_service.login("sessionuser", "password123")
        
        session = auth_service.get_current_session()
        assert session is not None
        assert session.username == "sessionuser"
    
    def test_get_current_session_none_after_logout(self, auth_service):
        """Test get_current_session returns None after logout."""
        auth_service.register("sessionuser", "password123", "session@example.com")
        auth_service.login("sessionuser", "password123")
        auth_service.logout()
        
        assert auth_service.get_current_session() is None


class TestAuthServiceIntegration:
    """Integration tests for complete auth flows."""
    
    def test_full_registration_login_logout_flow(self, auth_service, session_service):
        """Test complete registration -> login -> logout flow."""
        # Register
        reg_result = auth_service.register("flowuser", "password123", "flow@example.com")
        assert reg_result.is_ok()
        assert session_service.is_authenticated() is False  # Registration doesn't auto-login
        
        # Login
        login_result = auth_service.login("flowuser", "password123")
        assert login_result.is_ok()
        assert session_service.is_authenticated() is True
        
        # Logout
        auth_service.logout()
        assert session_service.is_authenticated() is False
    
    def test_multiple_users_can_register(self, auth_service):
        """Test that multiple users can register."""
        result1 = auth_service.register("user1", "pass1", "user1@example.com")
        result2 = auth_service.register("user2", "pass2", "user2@example.com")
        result3 = auth_service.register("user3", "pass3", "user3@example.com")
        
        assert result1.is_ok()
        assert result2.is_ok()
        assert result3.is_ok()
        
        # All users should have unique IDs
        ids = {result1.value.id, result2.value.id, result3.value.id}
        assert len(ids) == 3
    
    def test_login_replaces_previous_session(self, auth_service, session_service):
        """Test that logging in as different user replaces session."""
        auth_service.register("user1", "pass1", "user1@example.com")
        auth_service.register("user2", "pass2", "user2@example.com")
        
        # Login as user1
        auth_service.login("user1", "pass1")
        session1 = session_service.get_current_session()
        assert session1.username == "user1"
        
        # Login as user2 (without explicit logout)
        auth_service.login("user2", "pass2")
        session2 = session_service.get_current_session()
        assert session2.username == "user2"
