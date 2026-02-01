"""
Password Hashing Utilities for secure password storage.

This module provides secure password hashing using bcrypt, which is designed
specifically for password hashing with built-in salting and configurable work factor.

Requirements: 1.2, 18.1
- 1.2: WHEN registration validation passes, THE System SHALL hash the password 
       using a secure algorithm before storage
- 18.1: THE SQLite_Database SHALL store user accounts with hashed passwords

Property 2: Password Hashing Security
- For any password string, when stored in the database, the stored value SHALL be 
  different from the original password AND the hash SHALL be verifiable against 
  the original password using the same hashing algorithm.
"""

import bcrypt


# Default work factor (cost) for bcrypt
# 12 is a good balance between security and performance
# Each increment doubles the computation time
DEFAULT_WORK_FACTOR = 12


def hash_password(password: str, work_factor: int = DEFAULT_WORK_FACTOR) -> str:
    """
    Hash a password securely using bcrypt.
    
    Bcrypt automatically generates a random salt and incorporates it into the hash,
    so each call with the same password produces a different hash. The work factor
    determines the computational cost, making brute-force attacks more difficult.
    
    Args:
        password: The plaintext password to hash.
        work_factor: The bcrypt work factor (cost). Higher values are more secure
                     but slower. Default is 12, which provides good security.
                     Valid range is 4-31.
    
    Returns:
        A string containing the bcrypt hash, which includes the algorithm identifier,
        work factor, salt, and hash. This string is safe for database storage.
    
    Raises:
        ValueError: If password is None or empty.
        ValueError: If work_factor is outside the valid range (4-31).
    
    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> print(hashed)  # $2b$12$... (bcrypt hash string)
        >>> # The hash is different from the original password
        >>> assert hashed != "my_secure_password"
    """
    if password is None:
        raise ValueError("Password cannot be None")
    
    if not password:
        raise ValueError("Password cannot be empty")
    
    if not (4 <= work_factor <= 31):
        raise ValueError(f"Work factor must be between 4 and 31, got {work_factor}")
    
    # Encode password to bytes (bcrypt requires bytes)
    password_bytes = password.encode('utf-8')
    
    # Generate salt with specified work factor and hash the password
    salt = bcrypt.gensalt(rounds=work_factor)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a stored bcrypt hash.
    
    This function securely compares the provided password against the stored hash
    using bcrypt's constant-time comparison to prevent timing attacks.
    
    Args:
        password: The plaintext password to verify.
        password_hash: The stored bcrypt hash to verify against.
    
    Returns:
        True if the password matches the hash, False otherwise.
    
    Raises:
        ValueError: If password is None.
        ValueError: If password_hash is None or empty.
    
    Example:
        >>> hashed = hash_password("my_secure_password")
        >>> verify_password("my_secure_password", hashed)  # Returns True
        >>> verify_password("wrong_password", hashed)  # Returns False
    """
    if password is None:
        raise ValueError("Password cannot be None")
    
    if not password_hash:
        raise ValueError("Password hash cannot be None or empty")
    
    # Encode password and hash to bytes
    password_bytes = password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    
    # Use bcrypt's checkpw for constant-time comparison
    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except (ValueError, TypeError):
        # Invalid hash format
        return False
