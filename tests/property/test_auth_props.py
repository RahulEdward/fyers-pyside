"""
Property-based tests for Authentication.

# Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
# Feature: fyers-auto-trading-system, Property 4: Registration Persistence Round-Trip
# Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
# Feature: fyers-auto-trading-system, Property 6: Session Creation on Login

This module contains property-based tests using Hypothesis to verify that the
authentication service correctly validates registration input, persists user data,
authenticates users, and creates sessions.

Property 1 Definition:
"For any combination of username, password, and email strings, the registration 
validation SHALL accept only when all fields are non-empty AND the email matches 
a valid email format pattern."

Property 4 Definition:
"For any valid registration data (username, password, email), after successful 
registration, querying the database by username SHALL return a user with matching 
username and email."

Property 5 Definition:
"For any registered user, login with correct credentials SHALL succeed, and login 
with incorrect password SHALL fail."

Property 6 Definition:
"For any successful login, a session SHALL be created containing the user's ID 
and username."

**Validates: Requirements 1.1, 1.4, 2.1, 2.2, 2.3**
"""

import string
from datetime import datetime
from hypothesis import given, settings, assume
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.services.auth_service import AuthService, validate_email
from src.services.session_service import SessionService
from src.repositories.user_repository import UserRepository
from src.database.schema import Base
from src.models.result import Ok, Err


# ============================================================================
# Strategies for generating test data
# ============================================================================

# Strategy for generating non-empty usernames (alphanumeric with underscores)
valid_username_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != "")

# Strategy for generating non-empty passwords
valid_password_strategy = st.text(
    alphabet=string.printable,
    min_size=1,
    max_size=100
).filter(lambda x: len(x) > 0)

# Strategy for generating valid email addresses
valid_email_strategy = st.emails()

# Strategy for generating invalid emails (strings that don't match email pattern)
invalid_email_strategy = st.one_of(
    st.just(""),
    st.just("   "),
    st.just("notanemail"),
    st.just("missing@domain"),
    st.just("@nodomain.com"),
    st.just("spaces in@email.com"),
    st.text(alphabet=string.ascii_letters, min_size=1, max_size=20).filter(
        lambda x: "@" not in x and "." not in x
    )
)

# Strategy for generating empty or whitespace-only strings
empty_string_strategy = st.one_of(
    st.just(""),
    st.just("   "),
    st.just("\t"),
    st.just("\n"),
    st.just("  \t\n  ")
)

# Strategy for generating wrong passwords (different from original)
def wrong_password_strategy(original_password: str):
    """Generate a password that is definitely different from the original."""
    return st.text(
        alphabet=string.printable,
        min_size=1,
        max_size=100
    ).filter(lambda x: x != original_password and len(x) > 0)


# ============================================================================
# Helper functions
# ============================================================================

def create_test_db_session():
    """
    Create a fresh in-memory SQLite database session for testing.
    
    Returns:
        A SQLAlchemy session connected to a fresh in-memory database.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def create_auth_service():
    """
    Create an AuthService with fresh dependencies for testing.
    
    Returns:
        Tuple of (AuthService, UserRepository, SessionService, db_session)
    """
    db_session = create_test_db_session()
    user_repo = UserRepository(db_session)
    session_service = SessionService()
    auth_service = AuthService(user_repo, session_service)
    return auth_service, user_repo, session_service, db_session


# ============================================================================
# Property 1: Registration Input Validation
# ============================================================================

class TestRegistrationInputValidationProperty:
    """
    Property-based tests for registration input validation.
    
    # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
    
    Property Definition:
    "For any combination of username, password, and email strings, the registration 
    validation SHALL accept only when all fields are non-empty AND the email matches 
    a valid email format pattern."
    
    **Validates: Requirements 1.1**
    """
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_valid_inputs_are_accepted(self, username: str, password: str, email: str):
        """
        Property: For any valid username, password, and email, registration SHALL succeed.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        
        This test verifies that valid inputs are accepted by the registration process.
        """
        auth_service, user_repo, _, db_session = create_auth_service()
        
        # Attempt registration with valid inputs
        result = auth_service.register(username, password, email)
        
        # Registration should succeed
        assert isinstance(result, Ok), (
            f"Registration should succeed with valid inputs. "
            f"Username: '{username}', Email: '{email}', Error: {result.error if isinstance(result, Err) else 'N/A'}"
        )
        
        # Clean up
        db_session.close()
    
    @given(
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_empty_username_is_rejected(self, password: str, email: str):
        """
        Property: For any empty username, registration SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Test with empty string
        result = auth_service.register("", password, email)
        assert isinstance(result, Err), "Empty username should be rejected"
        
        # Test with whitespace-only
        result = auth_service.register("   ", password, email)
        assert isinstance(result, Err), "Whitespace-only username should be rejected"
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_empty_password_is_rejected(self, username: str, email: str):
        """
        Property: For any empty password, registration SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Test with empty string
        result = auth_service.register(username, "", email)
        assert isinstance(result, Err), "Empty password should be rejected"
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_empty_email_is_rejected(self, username: str, password: str):
        """
        Property: For any empty email, registration SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Test with empty string
        result = auth_service.register(username, password, "")
        assert isinstance(result, Err), "Empty email should be rejected"
        
        # Test with whitespace-only
        result = auth_service.register(username + "_2", password, "   ")
        assert isinstance(result, Err), "Whitespace-only email should be rejected"
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        invalid_email=invalid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_invalid_email_format_is_rejected(self, username: str, password: str, invalid_email: str):
        """
        Property: For any invalid email format, registration SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        result = auth_service.register(username, password, invalid_email)
        
        assert isinstance(result, Err), (
            f"Invalid email format should be rejected. "
            f"Email: '{invalid_email}'"
        )
        
        db_session.close()
    
    @given(email=valid_email_strategy)
    @settings(max_examples=10, deadline=None)
    def test_validate_email_accepts_valid_emails(self, email: str):
        """
        Property: For any valid email from Hypothesis email strategy, validate_email returns True.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        assert validate_email(email), f"Valid email should be accepted: '{email}'"
    
    @given(invalid_email=invalid_email_strategy)
    @settings(max_examples=10, deadline=None)
    def test_validate_email_rejects_invalid_emails(self, invalid_email: str):
        """
        Property: For any invalid email, validate_email returns False.
        
        # Feature: fyers-auto-trading-system, Property 1: Registration Input Validation
        **Validates: Requirements 1.1**
        """
        assert not validate_email(invalid_email), f"Invalid email should be rejected: '{invalid_email}'"


# ============================================================================
# Property 4: Registration Persistence Round-Trip
# ============================================================================

class TestRegistrationPersistenceProperty:
    """
    Property-based tests for registration persistence.
    
    # Feature: fyers-auto-trading-system, Property 4: Registration Persistence Round-Trip
    
    Property Definition:
    "For any valid registration data (username, password, email), after successful 
    registration, querying the database by username SHALL return a user with matching 
    username and email."
    
    **Validates: Requirements 1.4**
    """
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_registered_user_can_be_retrieved_by_username(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any valid registration, user can be retrieved by username.
        
        # Feature: fyers-auto-trading-system, Property 4: Registration Persistence Round-Trip
        **Validates: Requirements 1.4**
        """
        auth_service, user_repo, _, db_session = create_auth_service()
        
        # Register the user
        result = auth_service.register(username, password, email)
        assert isinstance(result, Ok), f"Registration should succeed: {result.error if isinstance(result, Err) else 'N/A'}"
        
        registered_user = result.value
        
        # Query the database by username
        retrieved_user = user_repo.find_by_username(username.strip())
        
        # Verify user was found
        assert retrieved_user is not None, (
            f"User should be retrievable by username after registration. "
            f"Username: '{username}'"
        )
        
        # Verify username matches (accounting for strip)
        assert retrieved_user.username == username.strip(), (
            f"Retrieved username should match. "
            f"Expected: '{username.strip()}', Got: '{retrieved_user.username}'"
        )
        
        # Verify email matches (accounting for strip)
        assert retrieved_user.email == email.strip(), (
            f"Retrieved email should match. "
            f"Expected: '{email.strip()}', Got: '{retrieved_user.email}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_registered_user_has_valid_id(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any valid registration, the returned user has a valid ID.
        
        # Feature: fyers-auto-trading-system, Property 4: Registration Persistence Round-Trip
        **Validates: Requirements 1.4**
        """
        auth_service, user_repo, _, db_session = create_auth_service()
        
        # Register the user
        result = auth_service.register(username, password, email)
        assert isinstance(result, Ok), f"Registration should succeed"
        
        registered_user = result.value
        
        # Verify user has a valid ID
        assert registered_user.id is not None, "Registered user should have an ID"
        assert registered_user.id > 0, "User ID should be positive"
        
        # Verify user can be retrieved by ID
        retrieved_user = user_repo.find_by_id(registered_user.id)
        assert retrieved_user is not None, "User should be retrievable by ID"
        assert retrieved_user.username == username.strip()
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_password_is_not_stored_in_plaintext(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any registration, password is NOT stored as plaintext.
        
        # Feature: fyers-auto-trading-system, Property 4: Registration Persistence Round-Trip
        **Validates: Requirements 1.4**
        
        This ensures the password hash is different from the original password.
        """
        auth_service, user_repo, _, db_session = create_auth_service()
        
        # Register the user
        result = auth_service.register(username, password, email)
        assert isinstance(result, Ok), f"Registration should succeed"
        
        # Retrieve the user
        retrieved_user = user_repo.find_by_username(username.strip())
        
        # Verify password is not stored in plaintext
        assert retrieved_user.password_hash != password, (
            f"Password should NOT be stored in plaintext. "
            f"Original: '{password}', Stored: '{retrieved_user.password_hash}'"
        )
        
        db_session.close()


# ============================================================================
# Property 5: Authentication Correctness
# ============================================================================

class TestAuthenticationCorrectnessProperty:
    """
    Property-based tests for authentication correctness.
    
    # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
    
    Property Definition:
    "For any registered user, login with correct credentials SHALL succeed, and login 
    with incorrect password SHALL fail."
    
    **Validates: Requirements 2.1, 2.3**
    """
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_login_with_correct_credentials_succeeds(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any registered user, login with correct password SHALL succeed.
        
        # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
        **Validates: Requirements 2.1**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Register the user
        reg_result = auth_service.register(username, password, email)
        assert isinstance(reg_result, Ok), f"Registration should succeed"
        
        # Login with correct credentials
        login_result = auth_service.login(username, password)
        
        assert isinstance(login_result, Ok), (
            f"Login with correct credentials should succeed. "
            f"Username: '{username}', Error: {login_result.error if isinstance(login_result, Err) else 'N/A'}"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy,
        wrong_password=valid_password_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_login_with_incorrect_password_fails(
        self, username: str, password: str, email: str, wrong_password: str
    ):
        """
        Property: For any registered user, login with incorrect password SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
        **Validates: Requirements 2.3**
        """
        # Ensure wrong_password is actually different
        assume(wrong_password != password)
        
        auth_service, _, _, db_session = create_auth_service()
        
        # Register the user
        reg_result = auth_service.register(username, password, email)
        assert isinstance(reg_result, Ok), f"Registration should succeed"
        
        # Login with incorrect password
        login_result = auth_service.login(username, wrong_password)
        
        assert isinstance(login_result, Err), (
            f"Login with incorrect password should fail. "
            f"Username: '{username}', Correct: '{password}', Wrong: '{wrong_password}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_login_with_nonexistent_user_fails(
        self, username: str, password: str
    ):
        """
        Property: For any non-existent username, login SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
        **Validates: Requirements 2.3**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Don't register any user - try to login directly
        login_result = auth_service.login(username, password)
        
        assert isinstance(login_result, Err), (
            f"Login with non-existent user should fail. "
            f"Username: '{username}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_login_with_empty_password_fails(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any registered user, login with empty password SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
        **Validates: Requirements 2.3**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Register the user
        reg_result = auth_service.register(username, password, email)
        assert isinstance(reg_result, Ok), f"Registration should succeed"
        
        # Login with empty password
        login_result = auth_service.login(username, "")
        
        assert isinstance(login_result, Err), (
            f"Login with empty password should fail. "
            f"Username: '{username}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_login_with_empty_username_fails(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any registered user, login with empty username SHALL fail.
        
        # Feature: fyers-auto-trading-system, Property 5: Authentication Correctness
        **Validates: Requirements 2.3**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Register the user
        reg_result = auth_service.register(username, password, email)
        assert isinstance(reg_result, Ok), f"Registration should succeed"
        
        # Login with empty username
        login_result = auth_service.login("", password)
        
        assert isinstance(login_result, Err), (
            f"Login with empty username should fail."
        )
        
        db_session.close()


# ============================================================================
# Property 6: Session Creation on Login
# ============================================================================

class TestSessionCreationOnLoginProperty:
    """
    Property-based tests for session creation on login.
    
    # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
    
    Property Definition:
    "For any successful login, a session SHALL be created containing the user's ID 
    and username."
    
    **Validates: Requirements 2.2**
    """
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_successful_login_creates_session(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any successful login, a session SHALL be created.
        
        # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
        **Validates: Requirements 2.2**
        """
        auth_service, _, session_service, db_session = create_auth_service()
        
        # Register the user
        reg_result = auth_service.register(username, password, email)
        assert isinstance(reg_result, Ok), f"Registration should succeed"
        
        registered_user = reg_result.value
        
        # Login
        login_result = auth_service.login(username, password)
        assert isinstance(login_result, Ok), f"Login should succeed"
        
        session = login_result.value
        
        # Verify session was created
        assert session is not None, "Session should be created on successful login"
        
        # Verify session contains user's ID
        assert session.user_id == registered_user.id, (
            f"Session should contain user's ID. "
            f"Expected: {registered_user.id}, Got: {session.user_id}"
        )
        
        # Verify session contains user's username
        assert session.username == username.strip(), (
            f"Session should contain user's username. "
            f"Expected: '{username.strip()}', Got: '{session.username}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_session_is_accessible_after_login(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any successful login, the session SHALL be accessible via get_current_session.
        
        # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
        **Validates: Requirements 2.2**
        """
        auth_service, _, session_service, db_session = create_auth_service()
        
        # Register and login
        auth_service.register(username, password, email)
        login_result = auth_service.login(username, password)
        assert isinstance(login_result, Ok), f"Login should succeed"
        
        # Verify session is accessible
        current_session = auth_service.get_current_session()
        
        assert current_session is not None, (
            "Session should be accessible via get_current_session after login"
        )
        assert current_session.username == username.strip(), (
            f"Current session should have correct username. "
            f"Expected: '{username.strip()}', Got: '{current_session.username}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_is_authenticated_returns_true_after_login(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any successful login, is_authenticated SHALL return True.
        
        # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
        **Validates: Requirements 2.2**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Verify not authenticated before login
        assert not auth_service.is_authenticated(), (
            "Should not be authenticated before login"
        )
        
        # Register and login
        auth_service.register(username, password, email)
        login_result = auth_service.login(username, password)
        assert isinstance(login_result, Ok), f"Login should succeed"
        
        # Verify authenticated after login
        assert auth_service.is_authenticated(), (
            f"Should be authenticated after successful login. "
            f"Username: '{username}'"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_session_has_creation_timestamp(
        self, username: str, password: str, email: str
    ):
        """
        Property: For any successful login, the session SHALL have a creation timestamp.
        
        # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
        **Validates: Requirements 2.2**
        """
        auth_service, _, _, db_session = create_auth_service()
        
        # Register and login
        auth_service.register(username, password, email)
        login_result = auth_service.login(username, password)
        assert isinstance(login_result, Ok), f"Login should succeed"
        
        session = login_result.value
        
        # Verify session has creation timestamp
        assert session.created_at is not None, (
            "Session should have a creation timestamp"
        )
        assert isinstance(session.created_at, datetime), (
            f"Session created_at should be a datetime. "
            f"Got: {type(session.created_at)}"
        )
        
        db_session.close()
    
    @given(
        username=valid_username_strategy,
        password=valid_password_strategy,
        email=valid_email_strategy,
        wrong_password=valid_password_strategy
    )
    @settings(max_examples=10, deadline=None)
    def test_failed_login_does_not_create_session(
        self, username: str, password: str, email: str, wrong_password: str
    ):
        """
        Property: For any failed login, no session SHALL be created.
        
        # Feature: fyers-auto-trading-system, Property 6: Session Creation on Login
        **Validates: Requirements 2.2**
        """
        # Ensure wrong_password is actually different
        assume(wrong_password != password)
        
        auth_service, _, _, db_session = create_auth_service()
        
        # Register the user
        auth_service.register(username, password, email)
        
        # Attempt login with wrong password
        login_result = auth_service.login(username, wrong_password)
        assert isinstance(login_result, Err), "Login with wrong password should fail"
        
        # Verify no session was created
        assert not auth_service.is_authenticated(), (
            "Should not be authenticated after failed login"
        )
        assert auth_service.get_current_session() is None, (
            "No session should exist after failed login"
        )
        
        db_session.close()
