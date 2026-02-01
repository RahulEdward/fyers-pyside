"""
Unit tests for EncryptionService.

Tests the encryption and decryption functionality using Fernet symmetric encryption.
"""

import pytest
from cryptography.fernet import InvalidToken

from src.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Unit tests for EncryptionService."""
    
    def test_init_with_valid_key(self):
        """Test that EncryptionService initializes correctly with a valid key."""
        service = EncryptionService(b"test_secret_key")
        assert service is not None
        assert service._fernet is not None
    
    def test_init_with_empty_key_raises_error(self):
        """Test that empty key raises ValueError."""
        with pytest.raises(ValueError, match="Encryption key cannot be empty"):
            EncryptionService(b"")
    
    def test_init_with_none_key_raises_error(self):
        """Test that None key raises ValueError."""
        with pytest.raises(ValueError, match="Encryption key cannot be empty"):
            EncryptionService(None)
    
    def test_encrypt_returns_string(self):
        """Test that encrypt returns a string."""
        service = EncryptionService(b"test_secret_key")
        result = service.encrypt("test_plaintext")
        assert isinstance(result, str)
    
    def test_encrypt_returns_different_from_plaintext(self):
        """Test that encrypted value is different from plaintext."""
        service = EncryptionService(b"test_secret_key")
        plaintext = "my_api_key_12345"
        encrypted = service.encrypt(plaintext)
        assert encrypted != plaintext
    
    def test_encrypt_none_raises_error(self):
        """Test that encrypting None raises ValueError."""
        service = EncryptionService(b"test_secret_key")
        with pytest.raises(ValueError, match="Cannot encrypt None value"):
            service.encrypt(None)
    
    def test_encrypt_empty_string(self):
        """Test that empty string can be encrypted and decrypted."""
        service = EncryptionService(b"test_secret_key")
        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)
        assert decrypted == ""
    
    def test_decrypt_returns_original_plaintext(self):
        """Test that decrypt returns the original plaintext."""
        service = EncryptionService(b"test_secret_key")
        plaintext = "my_secret_api_key"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_decrypt_empty_ciphertext_raises_error(self):
        """Test that decrypting empty string raises ValueError."""
        service = EncryptionService(b"test_secret_key")
        with pytest.raises(ValueError, match="Cannot decrypt empty or None ciphertext"):
            service.decrypt("")
    
    def test_decrypt_none_raises_error(self):
        """Test that decrypting None raises ValueError."""
        service = EncryptionService(b"test_secret_key")
        with pytest.raises(ValueError, match="Cannot decrypt empty or None ciphertext"):
            service.decrypt(None)
    
    def test_decrypt_invalid_ciphertext_raises_error(self):
        """Test that decrypting invalid ciphertext raises InvalidToken."""
        service = EncryptionService(b"test_secret_key")
        with pytest.raises(InvalidToken):
            service.decrypt("invalid_ciphertext_not_base64_fernet")
    
    def test_decrypt_with_wrong_key_raises_error(self):
        """Test that decrypting with wrong key raises InvalidToken."""
        service1 = EncryptionService(b"key_one")
        service2 = EncryptionService(b"key_two")
        
        encrypted = service1.encrypt("secret_data")
        
        with pytest.raises(InvalidToken):
            service2.decrypt(encrypted)
    
    def test_encrypt_decrypt_round_trip_api_key(self):
        """Test round-trip encryption/decryption for API key."""
        service = EncryptionService(b"app_secret_key_12345")
        api_key = "FYERS-API-KEY-ABC123XYZ"
        
        encrypted = service.encrypt(api_key)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == api_key
    
    def test_encrypt_decrypt_round_trip_api_secret(self):
        """Test round-trip encryption/decryption for API secret."""
        service = EncryptionService(b"app_secret_key_12345")
        api_secret = "super_secret_api_secret_value_!@#$%"
        
        encrypted = service.encrypt(api_secret)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == api_secret
    
    def test_encrypt_produces_different_ciphertext_each_time(self):
        """Test that encrypting same plaintext produces different ciphertext (due to IV)."""
        service = EncryptionService(b"test_secret_key")
        plaintext = "same_plaintext"
        
        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)
        
        # Fernet uses random IV, so ciphertexts should be different
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext
    
    def test_encrypt_decrypt_unicode_characters(self):
        """Test encryption/decryption with Unicode characters."""
        service = EncryptionService(b"test_secret_key")
        plaintext = "API密钥_🔐_مفتاح"
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_encrypt_decrypt_long_string(self):
        """Test encryption/decryption with a long string."""
        service = EncryptionService(b"test_secret_key")
        plaintext = "A" * 10000  # 10KB of data
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_same_key_produces_same_derived_key(self):
        """Test that same app secret produces consistent encryption."""
        service1 = EncryptionService(b"consistent_key")
        service2 = EncryptionService(b"consistent_key")
        
        plaintext = "test_data"
        encrypted = service1.encrypt(plaintext)
        
        # Service2 with same key should be able to decrypt
        decrypted = service2.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_custom_salt(self):
        """Test that custom salt can be provided."""
        custom_salt = b"my_custom_salt_value"
        service = EncryptionService(b"test_key", salt=custom_salt)
        
        plaintext = "test_data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_different_salt_produces_different_key(self):
        """Test that different salts produce different encryption keys."""
        service1 = EncryptionService(b"same_key", salt=b"salt_one")
        service2 = EncryptionService(b"same_key", salt=b"salt_two")
        
        encrypted = service1.encrypt("test_data")
        
        # Different salt means different derived key, so decryption should fail
        with pytest.raises(InvalidToken):
            service2.decrypt(encrypted)
