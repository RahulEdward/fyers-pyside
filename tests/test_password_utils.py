"""
Unit tests for password hashing utilities.

Tests the password hashing and verification functionality using bcrypt.

Requirements: 1.2, 18.1
"""

import pytest

from src.services.password_utils import hash_password, verify_password


class TestHashPassword:
    """Unit tests for hash_password function."""
    
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("test_password")
        assert isinstance(result, str)
    
    def test_hash_password_returns_different_from_original(self):
        """Test that hashed password is different from original."""
        password = "my_secure_password"
        hashed = hash_password(password)
        assert hashed != password
    
    def test_hash_password_returns_bcrypt_format(self):
        """Test that hash is in bcrypt format ($2b$...)."""
        hashed = hash_password("test_password")
        # bcrypt hashes start with $2b$ (or $2a$, $2y$)
        assert hashed.startswith("$2")
    
    def test_hash_password_includes_work_factor(self):
        """Test that hash includes the work factor."""
        hashed = hash_password("test_password", work_factor=12)
        # Format: $2b$12$...
        assert "$12$" in hashed
    
    def test_hash_password_with_custom_work_factor(self):
        """Test hashing with custom work factor."""
        hashed = hash_password("test_password", work_factor=10)
        assert "$10$" in hashed
    
    def test_hash_password_none_raises_error(self):
        """Test that None password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be None"):
            hash_password(None)
    
    def test_hash_password_empty_raises_error(self):
        """Test that empty password raises ValueError."""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")
    
    def test_hash_password_invalid_work_factor_low(self):
        """Test that work factor below 4 raises ValueError."""
        with pytest.raises(ValueError, match="Work factor must be between 4 and 31"):
            hash_password("test_password", work_factor=3)
    
    def test_hash_password_invalid_work_factor_high(self):
        """Test that work factor above 31 raises ValueError."""
        with pytest.raises(ValueError, match="Work factor must be between 4 and 31"):
            hash_password("test_password", work_factor=32)
    
    def test_hash_password_produces_different_hashes(self):
        """Test that same password produces different hashes (due to random salt)."""
        password = "same_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        # bcrypt uses random salt, so hashes should be different
        assert hash1 != hash2
    
    def test_hash_password_unicode_characters(self):
        """Test hashing password with Unicode characters."""
        password = "पासवर्ड_🔐_密码"
        hashed = hash_password(password)
        assert hashed != password
        assert hashed.startswith("$2")
    
    def test_hash_password_long_password(self):
        """Test hashing a long password."""
        # bcrypt has a 72-byte limit, but should handle gracefully
        password = "A" * 100
        hashed = hash_password(password)
        assert hashed != password


class TestVerifyPassword:
    """Unit tests for verify_password function."""
    
    def test_verify_password_correct_password(self):
        """Test that correct password verifies successfully."""
        password = "my_secure_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect_password(self):
        """Test that incorrect password fails verification."""
        password = "my_secure_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "MyPassword"
        hashed = hash_password(password)
        assert verify_password("mypassword", hashed) is False
        assert verify_password("MYPASSWORD", hashed) is False
        assert verify_password("MyPassword", hashed) is True
    
    def test_verify_password_none_password_raises_error(self):
        """Test that None password raises ValueError."""
        hashed = hash_password("test_password")
        with pytest.raises(ValueError, match="Password cannot be None"):
            verify_password(None, hashed)
    
    def test_verify_password_none_hash_raises_error(self):
        """Test that None hash raises ValueError."""
        with pytest.raises(ValueError, match="Password hash cannot be None or empty"):
            verify_password("test_password", None)
    
    def test_verify_password_empty_hash_raises_error(self):
        """Test that empty hash raises ValueError."""
        with pytest.raises(ValueError, match="Password hash cannot be None or empty"):
            verify_password("test_password", "")
    
    def test_verify_password_invalid_hash_returns_false(self):
        """Test that invalid hash format returns False (not exception)."""
        result = verify_password("test_password", "invalid_hash_format")
        assert result is False
    
    def test_verify_password_empty_password(self):
        """Test verification with empty password (should fail gracefully)."""
        hashed = hash_password("actual_password")
        # Empty password should not match
        assert verify_password("", hashed) is False
    
    def test_verify_password_unicode_characters(self):
        """Test verification with Unicode password."""
        password = "पासवर्ड_🔐_密码"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_unicode", hashed) is False
    
    def test_verify_password_different_work_factors(self):
        """Test that verification works across different work factors."""
        password = "test_password"
        # Hash with work factor 4 (minimum)
        hashed_low = hash_password(password, work_factor=4)
        # Hash with work factor 10
        hashed_high = hash_password(password, work_factor=10)
        
        # Both should verify correctly
        assert verify_password(password, hashed_low) is True
        assert verify_password(password, hashed_high) is True


class TestPasswordHashingRoundTrip:
    """Integration tests for hash and verify round-trip."""
    
    def test_round_trip_simple_password(self):
        """Test complete round-trip with simple password."""
        password = "simple123"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Verification should succeed
        assert verify_password(password, hashed) is True
    
    def test_round_trip_complex_password(self):
        """Test round-trip with complex password."""
        password = "C0mpl3x!P@ssw0rd#2024"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
    
    def test_round_trip_special_characters(self):
        """Test round-trip with special characters."""
        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
    
    def test_round_trip_whitespace_password(self):
        """Test round-trip with whitespace in password."""
        password = "  password with spaces  "
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        # Trimmed version should not match
        assert verify_password("password with spaces", hashed) is False
