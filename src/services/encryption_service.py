"""
Encryption Service for secure credential storage.

This module provides symmetric encryption using Fernet from the cryptography library.
It is used to encrypt and decrypt sensitive data like broker credentials before storage.

Requirements: 4.2, 4.4
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data using Fernet symmetric encryption.
    
    The encryption key is derived from an application secret using PBKDF2 key derivation
    function, which provides protection against brute-force attacks.
    
    Attributes:
        _fernet: The Fernet instance used for encryption/decryption operations.
    """
    
    # Default salt for key derivation - in production, this should be stored securely
    # and be unique per installation
    DEFAULT_SALT = b'fyers_auto_trading_salt_v1'
    
    def __init__(self, key: bytes, salt: bytes = None):
        """
        Initialize the EncryptionService with an encryption key derived from the app secret.
        
        Args:
            key: The application secret key (bytes) used to derive the encryption key.
                 This should be a secure, randomly generated secret stored in environment
                 variables or a secure configuration file.
            salt: Optional salt for key derivation. If not provided, uses DEFAULT_SALT.
                  For production use, a unique salt should be generated and stored.
        
        Raises:
            ValueError: If the key is empty or None.
        """
        if not key:
            raise ValueError("Encryption key cannot be empty")
        
        # Use provided salt or default
        salt = salt or self.DEFAULT_SALT
        
        # Derive a proper Fernet key from the application secret using PBKDF2
        # PBKDF2 with SHA256 and 100,000 iterations provides strong key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # Fernet requires a 32-byte key
            salt=salt,
            iterations=100_000,
        )
        
        # Derive the key and encode it for Fernet (base64 URL-safe encoding)
        derived_key = base64.urlsafe_b64encode(kdf.derive(key))
        self._fernet = Fernet(derived_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt sensitive data using Fernet symmetric encryption.
        
        The plaintext is encoded to UTF-8 bytes, encrypted using Fernet,
        and the resulting ciphertext is returned as a base64-encoded string
        for safe storage in databases or configuration files.
        
        Args:
            plaintext: The sensitive data to encrypt (e.g., API key, API secret).
        
        Returns:
            A base64-encoded string containing the encrypted data.
            This string is safe for storage in databases and text files.
        
        Raises:
            ValueError: If plaintext is None.
        
        Example:
            >>> service = EncryptionService(b"my_app_secret")
            >>> encrypted = service.encrypt("my_api_key")
            >>> print(encrypted)  # Base64-encoded ciphertext
        """
        if plaintext is None:
            raise ValueError("Cannot encrypt None value")
        
        # Encode plaintext to bytes and encrypt
        plaintext_bytes = plaintext.encode('utf-8')
        encrypted_bytes = self._fernet.encrypt(plaintext_bytes)
        
        # Return as string (Fernet already returns base64-encoded bytes)
        return encrypted_bytes.decode('utf-8')
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt encrypted data.
        
        The ciphertext (base64-encoded string) is decoded and decrypted
        using Fernet, returning the original plaintext string.
        
        Args:
            ciphertext: The base64-encoded encrypted data to decrypt.
        
        Returns:
            The original plaintext string.
        
        Raises:
            ValueError: If ciphertext is None or empty.
            cryptography.fernet.InvalidToken: If the ciphertext is invalid,
                corrupted, or was encrypted with a different key.
        
        Example:
            >>> service = EncryptionService(b"my_app_secret")
            >>> encrypted = service.encrypt("my_api_key")
            >>> decrypted = service.decrypt(encrypted)
            >>> assert decrypted == "my_api_key"
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty or None ciphertext")
        
        # Decode ciphertext from string to bytes and decrypt
        ciphertext_bytes = ciphertext.encode('utf-8')
        decrypted_bytes = self._fernet.decrypt(ciphertext_bytes)
        
        # Return as string
        return decrypted_bytes.decode('utf-8')
