"""
Session Service for managing user authentication state.

This module provides session management functionality for the Fyers Auto Trading System.
It maintains the current user session in memory during active use and provides methods
to create, retrieve, and clear sessions.

Requirements: 3.1, 3.2, 3.4
- 3.1: WHILE a user is logged in, THE System SHALL maintain session state across application screens
- 3.2: WHEN a user clicks logout, THE System SHALL clear session data and navigate to login screen
- 3.4: THE System SHALL store session information securely in memory during active use

Properties supported:
- Property 7: Session Persistence Across Navigation
- Property 8: Logout Clears Session
"""

from datetime import datetime
from typing import Optional

from src.models.user import User, Session


class SessionService:
    """
    Service for managing user authentication sessions.
    
    This service maintains the current user session in memory during active use.
    It provides methods to create sessions upon successful login, retrieve the
    current session for authentication checks, and clear sessions on logout.
    
    The session is stored in memory only (not persisted to disk) for security,
    ensuring that session data is cleared when the application closes.
    
    Attributes:
        _current_session: The currently active session, or None if no user is logged in.
    
    Example:
        >>> session_service = SessionService()
        >>> user = User(id=1, username="trader", email="trader@example.com", 
        ...             password_hash="...", created_at=datetime.now())
        >>> session = session_service.create_session(user)
        >>> session_service.is_authenticated()
        True
        >>> session_service.clear_session()
        >>> session_service.is_authenticated()
        False
    """
    
    def __init__(self):
        """
        Initialize the SessionService with no active session.
        
        The session starts as None, indicating no user is currently authenticated.
        """
        self._current_session: Optional[Session] = None
    
    def create_session(self, user: User) -> Session:
        """
        Create a new session for an authenticated user.
        
        This method should be called after successful login to establish
        the user's session. The session contains the user's ID, username,
        and creation timestamp.
        
        Args:
            user: The authenticated User object containing user details.
        
        Returns:
            A new Session object containing the user's session information.
        
        Raises:
            ValueError: If user is None.
        
        Example:
            >>> user = User(id=1, username="trader", email="trader@example.com",
            ...             password_hash="...", created_at=datetime.now())
            >>> session = session_service.create_session(user)
            >>> session.user_id
            1
            >>> session.username
            'trader'
        
        Note:
            Creating a new session will replace any existing session.
            This is the expected behavior for single-user desktop applications.
        """
        if user is None:
            raise ValueError("Cannot create session for None user")
        
        # Create a new session with user information
        session = Session(
            user_id=user.id,
            username=user.username,
            created_at=datetime.now(),
            access_token=None  # Access token is set later after broker authentication
        )
        
        # Store the session in memory
        self._current_session = session
        
        return session
    
    def get_current_session(self) -> Optional[Session]:
        """
        Get the currently active session.
        
        This method returns the current session if a user is logged in,
        or None if no user is authenticated. Use this to access session
        information like user_id and username across different screens.
        
        Returns:
            The current Session object if a user is logged in, None otherwise.
        
        Example:
            >>> session = session_service.get_current_session()
            >>> if session:
            ...     print(f"Logged in as: {session.username}")
            ... else:
            ...     print("Not logged in")
        
        Note:
            This method supports Requirement 3.1 by providing consistent
            session state access across application screens.
        """
        return self._current_session
    
    def clear_session(self) -> None:
        """
        Clear the active session.
        
        This method should be called when a user logs out or when the
        application is closing. It removes all session data from memory,
        ensuring no sensitive information persists.
        
        After calling this method, is_authenticated() will return False
        and get_current_session() will return None.
        
        Example:
            >>> session_service.clear_session()
            >>> session_service.is_authenticated()
            False
            >>> session_service.get_current_session()
            None
        
        Note:
            This method supports Requirement 3.2 (logout clears session)
            and Requirement 3.3 (application close clears session).
        """
        self._current_session = None
    
    def is_authenticated(self) -> bool:
        """
        Check if a user is currently authenticated.
        
        This method provides a simple boolean check for authentication status,
        useful for guarding access to protected screens and features.
        
        Returns:
            True if a user is logged in (session exists), False otherwise.
        
        Example:
            >>> if session_service.is_authenticated():
            ...     show_dashboard()
            ... else:
            ...     show_login()
        
        Note:
            This method supports Property 7 (Session Persistence Across Navigation)
            by providing a consistent way to check authentication state.
        """
        return self._current_session is not None
    
    def set_access_token(self, access_token: str) -> None:
        """
        Set the broker access token for the current session.
        
        This method should be called after successful Fyers OAuth authentication
        to store the access token in the session for API calls.
        
        Args:
            access_token: The Fyers API access token obtained from OAuth flow.
        
        Raises:
            ValueError: If no session exists (user not logged in).
            ValueError: If access_token is None or empty.
        
        Example:
            >>> session_service.set_access_token("your_fyers_access_token")
            >>> session = session_service.get_current_session()
            >>> session.access_token
            'your_fyers_access_token'
        """
        if self._current_session is None:
            raise ValueError("Cannot set access token: no active session")
        
        if not access_token:
            raise ValueError("Access token cannot be empty")
        
        self._current_session.access_token = access_token
    
    def get_access_token(self) -> Optional[str]:
        """
        Get the broker access token from the current session.
        
        Returns:
            The Fyers API access token if set, None otherwise.
        
        Example:
            >>> token = session_service.get_access_token()
            >>> if token:
            ...     trading_service = TradingService(token)
        """
        if self._current_session is None:
            return None
        return self._current_session.access_token
