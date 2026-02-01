"""
Property-based tests for Session Management.

# Feature: fyers-auto-trading-system, Property 7: Session Persistence Across Navigation
# Feature: fyers-auto-trading-system, Property 8: Logout Clears Session

This module contains property-based tests using Hypothesis to verify that the
session management service correctly maintains and clears session state.

Property 7 Definition:
"For any authenticated session, navigating between application screens SHALL 
preserve the session state (user remains authenticated)."

Property 8 Definition:
"For any active session, after logout, the session SHALL be cleared 
(is_authenticated returns false)."

**Validates: Requirements 3.1, 3.2**
"""

import string
from datetime import datetime
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.services.session_service import SessionService
from src.models.user import User, Session


# Strategy for generating valid user IDs (positive integers)
user_id_strategy = st.integers(min_value=1, max_value=1000000)

# Strategy for generating valid usernames (non-empty alphanumeric strings)
username_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "_",
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != "")

# Strategy for generating valid email addresses
email_strategy = st.emails()

# Strategy for generating password hashes (simulated bcrypt-like hashes)
password_hash_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "$./",
    min_size=60,
    max_size=60
)

# Strategy for generating access tokens
access_token_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=10,
    max_size=100
).filter(lambda x: x.strip() != "")


@st.composite
def user_strategy(draw):
    """
    Composite strategy for generating valid User objects.
    """
    return User(
        id=draw(user_id_strategy),
        username=draw(username_strategy),
        email=draw(email_strategy),
        password_hash=draw(password_hash_strategy),
        created_at=datetime.now()
    )


# Strategy for generating number of operations (simulating navigation)
navigation_count_strategy = st.integers(min_value=1, max_value=20)


class TestSessionPersistenceProperty:
    """
    Property-based tests for session persistence across navigation.
    
    # Feature: fyers-auto-trading-system, Property 7: Session Persistence Across Navigation
    
    Property Definition:
    "For any authenticated session, navigating between application screens SHALL 
    preserve the session state (user remains authenticated)."
    
    **Validates: Requirements 3.1**
    """
    
    @given(user=user_strategy(), nav_count=navigation_count_strategy)
    @settings(max_examples=10, deadline=None)
    def test_session_persists_across_multiple_operations(self, user: User, nav_count: int):
        """
        Property: For any authenticated session, multiple operations preserve session state.
        
        # Feature: fyers-auto-trading-system, Property 7: Session Persistence Across Navigation
        **Validates: Requirements 3.1**
        
        This test simulates navigation by performing multiple get_current_session()
        and is_authenticated() calls, verifying the session remains consistent.
        """
        # Create a fresh session service
        session_service = SessionService()
        
        # Create a session for the user
        created_session = session_service.create_session(user)
        
        # Simulate navigation by checking session state multiple times
        for i in range(nav_count):
            # Check authentication status (simulating screen access check)
            assert session_service.is_authenticated(), (
                f"Session should remain authenticated after {i+1} navigation checks. "
                f"User: {user.username}"
            )
            
            # Get current session (simulating accessing user info on different screens)
            current_session = session_service.get_current_session()
            assert current_session is not None, (
                f"Session should not be None after {i+1} navigation checks. "
                f"User: {user.username}"
            )
            
            # Verify session data is preserved
            assert current_session.user_id == user.id, (
                f"User ID should be preserved. Expected: {user.id}, Got: {current_session.user_id}"
            )
            assert current_session.username == user.username, (
                f"Username should be preserved. Expected: {user.username}, Got: {current_session.username}"
            )
    
    @given(user=user_strategy())
    @settings(max_examples=10, deadline=None)
    def test_session_data_matches_user_after_creation(self, user: User):
        """
        Property: For any user, created session contains correct user data.
        
        # Feature: fyers-auto-trading-system, Property 7: Session Persistence Across Navigation
        **Validates: Requirements 3.1**
        
        This test verifies that session creation correctly captures user information.
        """
        session_service = SessionService()
        
        # Create session
        session = session_service.create_session(user)
        
        # Verify session contains correct user data
        assert session.user_id == user.id, (
            f"Session user_id should match. Expected: {user.id}, Got: {session.user_id}"
        )
        assert session.username == user.username, (
            f"Session username should match. Expected: {user.username}, Got: {session.username}"
        )
        
        # Verify session is retrievable
        retrieved_session = session_service.get_current_session()
        assert retrieved_session is not None
        assert retrieved_session.user_id == user.id
        assert retrieved_session.username == user.username
    
    @given(user=user_strategy(), access_token=access_token_strategy)
    @settings(max_examples=10, deadline=None)
    def test_access_token_persists_in_session(self, user: User, access_token: str):
        """
        Property: For any session with access token, token persists across operations.
        
        # Feature: fyers-auto-trading-system, Property 7: Session Persistence Across Navigation
        **Validates: Requirements 3.1**
        
        This test verifies that access tokens set on sessions persist correctly.
        """
        session_service = SessionService()
        
        # Create session and set access token
        session_service.create_session(user)
        session_service.set_access_token(access_token)
        
        # Verify access token is retrievable
        retrieved_token = session_service.get_access_token()
        assert retrieved_token == access_token, (
            f"Access token should persist. Expected: {access_token}, Got: {retrieved_token}"
        )
        
        # Verify through session object as well
        current_session = session_service.get_current_session()
        assert current_session is not None
        assert current_session.access_token == access_token


class TestLogoutClearsSessionProperty:
    """
    Property-based tests for logout clearing session.
    
    # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
    
    Property Definition:
    "For any active session, after logout, the session SHALL be cleared 
    (is_authenticated returns false)."
    
    **Validates: Requirements 3.2**
    """
    
    @given(user=user_strategy())
    @settings(max_examples=10, deadline=None)
    def test_clear_session_makes_unauthenticated(self, user: User):
        """
        Property: For any active session, clear_session() results in is_authenticated() == False.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that clearing a session always results in
        the user being unauthenticated.
        """
        session_service = SessionService()
        
        # Create a session (user is now authenticated)
        session_service.create_session(user)
        assert session_service.is_authenticated(), "User should be authenticated after login"
        
        # Clear the session (logout)
        session_service.clear_session()
        
        # Verify user is no longer authenticated
        assert not session_service.is_authenticated(), (
            f"User should NOT be authenticated after clear_session(). "
            f"User: {user.username}"
        )
    
    @given(user=user_strategy())
    @settings(max_examples=10, deadline=None)
    def test_clear_session_returns_none_session(self, user: User):
        """
        Property: For any active session, clear_session() results in get_current_session() == None.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that clearing a session removes all session data.
        """
        session_service = SessionService()
        
        # Create a session
        session_service.create_session(user)
        assert session_service.get_current_session() is not None, "Session should exist after login"
        
        # Clear the session
        session_service.clear_session()
        
        # Verify session is None
        assert session_service.get_current_session() is None, (
            f"Session should be None after clear_session(). "
            f"User: {user.username}"
        )
    
    @given(user=user_strategy(), access_token=access_token_strategy)
    @settings(max_examples=10, deadline=None)
    def test_clear_session_clears_access_token(self, user: User, access_token: str):
        """
        Property: For any session with access token, clear_session() clears the token.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that clearing a session also clears any stored access tokens.
        """
        session_service = SessionService()
        
        # Create session with access token
        session_service.create_session(user)
        session_service.set_access_token(access_token)
        assert session_service.get_access_token() == access_token, "Token should be set"
        
        # Clear the session
        session_service.clear_session()
        
        # Verify access token is cleared
        assert session_service.get_access_token() is None, (
            f"Access token should be None after clear_session(). "
            f"User: {user.username}"
        )
    
    @given(user=user_strategy(), nav_count=navigation_count_strategy)
    @settings(max_examples=10, deadline=None)
    def test_clear_session_after_multiple_operations(self, user: User, nav_count: int):
        """
        Property: For any session after multiple operations, clear_session() still clears it.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that session clearing works regardless of how many
        operations were performed on the session.
        """
        session_service = SessionService()
        
        # Create session
        session_service.create_session(user)
        
        # Perform multiple operations (simulating navigation)
        for _ in range(nav_count):
            session_service.is_authenticated()
            session_service.get_current_session()
        
        # Clear the session
        session_service.clear_session()
        
        # Verify session is cleared
        assert not session_service.is_authenticated(), (
            f"User should NOT be authenticated after clear_session() "
            f"(after {nav_count} operations). User: {user.username}"
        )
        assert session_service.get_current_session() is None, (
            f"Session should be None after clear_session() "
            f"(after {nav_count} operations). User: {user.username}"
        )
    
    @given(user=user_strategy())
    @settings(max_examples=10, deadline=None)
    def test_multiple_clear_session_calls_are_safe(self, user: User):
        """
        Property: For any session, multiple clear_session() calls are idempotent.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that calling clear_session() multiple times is safe
        and doesn't cause errors.
        """
        session_service = SessionService()
        
        # Create session
        session_service.create_session(user)
        
        # Clear session multiple times
        session_service.clear_session()
        session_service.clear_session()
        session_service.clear_session()
        
        # Verify session remains cleared
        assert not session_service.is_authenticated()
        assert session_service.get_current_session() is None
    
    @given(user1=user_strategy(), user2=user_strategy())
    @settings(max_examples=10, deadline=None)
    def test_new_session_after_clear_works(self, user1: User, user2: User):
        """
        Property: After clear_session(), a new session can be created successfully.
        
        # Feature: fyers-auto-trading-system, Property 8: Logout Clears Session
        **Validates: Requirements 3.2**
        
        This test verifies that after logout, a new user can log in successfully.
        """
        session_service = SessionService()
        
        # First user logs in
        session_service.create_session(user1)
        assert session_service.is_authenticated()
        assert session_service.get_current_session().user_id == user1.id
        
        # First user logs out
        session_service.clear_session()
        assert not session_service.is_authenticated()
        
        # Second user logs in
        session_service.create_session(user2)
        
        # Verify second user's session
        assert session_service.is_authenticated(), "Second user should be authenticated"
        current_session = session_service.get_current_session()
        assert current_session is not None
        assert current_session.user_id == user2.id, (
            f"Session should belong to second user. "
            f"Expected user_id: {user2.id}, Got: {current_session.user_id}"
        )
        assert current_session.username == user2.username

