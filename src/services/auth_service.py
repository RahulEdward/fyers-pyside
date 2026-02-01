"""
Authentication Service for user registration, login, and logout.

This module provides authentication functionality for the Fyers Auto Trading System.
It handles user registration with validation and password hashing, login with credential
verification and session creation, and logout to clear session data.

Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 3.2
- 1.1: WHEN a user submits registration with username, password, and email, THE System 
       SHALL validate all fields are non-empty and email format is valid
- 1.2: WHEN registration validation passes, THE System SHALL hash the password using 
       a secure algorithm before storage
- 1.3: WHEN a user attempts to register with an existing username, THE System SHALL 
       reject the registration and display an error message
- 1.4: WHEN registration is successful, THE System SHALL store user data in SQLite_Database 
       and navigate to login screen
- 2.1: WHEN a user submits login credentials, THE System SHALL validate username and 
       password against stored data
- 2.2: WHEN login credentials are valid, THE System SHALL create a session and navigate 
       to broker credentials screen or dashboard
- 2.3: WHEN login credentials are invalid, THE System SHALL display an error message 
       and allow retry
- 3.2: WHEN a user clicks logout, THE System SHALL clear session data and navigate to 
       login screen

Properties supported:
- Property 1: Registration Input Validation
- Property 4: Registration Persistence Round-Trip
- Property 5: Authentication Correctness
- Property 6: Session Creation on Login
"""

import re
from typing import Optional

from sqlalchemy.exc import IntegrityError

from src.models.user import User, Session
from src.models.result import Result, Ok, Err
from src.repositories.user_repository import UserRepository
from src.services.session_service import SessionService
from src.services.password_utils import hash_password, verify_password


# Email validation regex pattern
# Matches standard email format: local@domain.tld
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)


def validate_email(email: str) -> bool:
    """
    Validate email format using regex pattern.
    
    Args:
        email: The email string to validate.
    
    Returns:
        True if email matches valid format, False otherwise.
    """
    if not email:
        return False
    return bool(EMAIL_PATTERN.match(email))


class AuthService:
    """
    Service for handling user authentication operations.
    
    This service provides methods for user registration, login, and logout.
    It coordinates between the UserRepository for data persistence,
    SessionService for session management, and password utilities for
    secure password handling.
    
    Attributes:
        _user_repo: Repository for user database operations.
        _session_service: Service for managing user sessions.
    
    Example:
        >>> user_repo = UserRepository(db_session)
        >>> session_service = SessionService()
        >>> auth_service = AuthService(user_repo, session_service)
        >>> 
        >>> # Register a new user
        >>> result = auth_service.register("trader", "secure_pass123", "trader@example.com")
        >>> if result.is_ok():
        ...     print(f"Registered user: {result.value.username}")
        >>> 
        >>> # Login
        >>> result = auth_service.login("trader", "secure_pass123")
        >>> if result.is_ok():
        ...     print(f"Session created for: {result.value.username}")
        >>> 
        >>> # Logout
        >>> auth_service.logout()
    """
    
    def __init__(self, user_repo: UserRepository, session_service: SessionService):
        """
        Initialize the AuthService with required dependencies.
        
        Args:
            user_repo: Repository for user database operations.
            session_service: Service for managing user sessions.
        
        Raises:
            ValueError: If user_repo or session_service is None.
        """
        if user_repo is None:
            raise ValueError("user_repo cannot be None")
        if session_service is None:
            raise ValueError("session_service cannot be None")
        
        self._user_repo = user_repo
        self._session_service = session_service
    
    def register(self, username: str, password: str, email: str) -> Result[User, str]:
        """
        Register a new user with validation and password hashing.
        
        This method validates all input fields, checks for username uniqueness,
        hashes the password securely, and stores the user in the database.
        
        Validation rules (Requirement 1.1):
        - Username must be non-empty
        - Password must be non-empty
        - Email must be non-empty and match valid email format
        
        Args:
            username: The desired username (must be unique).
            password: The plaintext password (will be hashed before storage).
            email: The user's email address (must be valid format).
        
        Returns:
            Result[User, str]: Ok(User) on success, Err(str) with error message on failure.
        
        Example:
            >>> result = auth_service.register("trader", "secure_pass", "trader@example.com")
            >>> if result.is_ok():
            ...     user = result.value
            ...     print(f"User {user.username} registered successfully")
            >>> else:
            ...     print(f"Registration failed: {result.error}")
        
        Note:
            - Requirement 1.2: Password is hashed using bcrypt before storage
            - Requirement 1.3: Registration fails if username already exists
            - Requirement 1.4: User data is stored in SQLite database on success
        """
        # Validate username (Requirement 1.1)
        if not username or not username.strip():
            return Err("Username cannot be empty")
        
        username = username.strip()
        
        # Validate password (Requirement 1.1)
        if not password:
            return Err("Password cannot be empty")
        
        # Validate email format (Requirement 1.1)
        if not email or not email.strip():
            return Err("Email cannot be empty")
        
        email = email.strip()
        
        if not validate_email(email):
            return Err("Invalid email format")
        
        # Check if username already exists (Requirement 1.3)
        if self._user_repo.exists(username):
            return Err("Username already exists")
        
        try:
            # Hash the password (Requirement 1.2)
            password_hash = hash_password(password)
            
            # Store user in database (Requirement 1.4)
            user = self._user_repo.create(
                username=username,
                password_hash=password_hash,
                email=email
            )
            
            return Ok(user)
        
        except IntegrityError:
            # Handle race condition where username was taken between check and insert
            return Err("Username already exists")
        
        except Exception as e:
            # Handle unexpected database errors (Requirement 1.5)
            return Err(f"Registration failed: {str(e)}")
    
    def login(self, username: str, password: str) -> Result[Session, str]:
        """
        Authenticate a user and create a session.
        
        This method validates the provided credentials against stored data
        and creates a session on successful authentication.
        
        Args:
            username: The username to authenticate.
            password: The plaintext password to verify.
        
        Returns:
            Result[Session, str]: Ok(Session) on success, Err(str) with error message on failure.
        
        Example:
            >>> result = auth_service.login("trader", "secure_pass")
            >>> if result.is_ok():
            ...     session = result.value
            ...     print(f"Welcome back, {session.username}!")
            >>> else:
            ...     print(f"Login failed: {result.error}")
        
        Note:
            - Requirement 2.1: Validates username and password against stored data
            - Requirement 2.2: Creates session on successful authentication
            - Requirement 2.3: Returns error message for invalid credentials
        """
        # Validate input
        if not username or not username.strip():
            return Err("Username cannot be empty")
        
        username = username.strip()
        
        if not password:
            return Err("Password cannot be empty")
        
        try:
            # Find user by username (Requirement 2.1)
            user = self._user_repo.find_by_username(username)
            
            if user is None:
                # User not found - return generic error to prevent username enumeration
                return Err("Invalid username or password")
            
            # Verify password (Requirement 2.1)
            if not verify_password(password, user.password_hash):
                # Password doesn't match (Requirement 2.3)
                return Err("Invalid username or password")
            
            # Create session (Requirement 2.2)
            session = self._session_service.create_session(user)
            
            return Ok(session)
        
        except Exception as e:
            # Handle unexpected errors (Requirement 2.5)
            return Err(f"Login failed: {str(e)}")
    
    def logout(self) -> None:
        """
        Clear the current session.
        
        This method clears all session data, effectively logging out the user.
        After calling this method, the user will need to log in again to access
        protected features.
        
        Example:
            >>> auth_service.logout()
            >>> # User is now logged out
        
        Note:
            - Requirement 3.2: Clears session data on logout
        """
        self._session_service.clear_session()
    
    def is_authenticated(self) -> bool:
        """
        Check if a user is currently authenticated.
        
        Returns:
            True if a user is logged in, False otherwise.
        
        Example:
            >>> if auth_service.is_authenticated():
            ...     show_dashboard()
            ... else:
            ...     show_login()
        """
        return self._session_service.is_authenticated()
    
    def get_current_session(self) -> Optional[Session]:
        """
        Get the current user session.
        
        Returns:
            The current Session if authenticated, None otherwise.
        
        Example:
            >>> session = auth_service.get_current_session()
            >>> if session:
            ...     print(f"Logged in as: {session.username}")
        """
        return self._session_service.get_current_session()
