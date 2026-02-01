"""
Property-based tests for Password Hashing Security.

# Feature: fyers-auto-trading-system, Property 2: Password Hashing Security

This module contains property-based tests using Hypothesis to verify that the
password hashing utilities correctly implement secure password storage.

Property Definition:
"For any password string, when stored in the database, the stored value SHALL be 
different from the original password AND the hash SHALL be verifiable against 
the original password using the same hashing algorithm."

**Validates: Requirements 1.2, 18.1**
"""

import string
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.services.password_utils import hash_password, verify_password

# Use low work factor for testing (bcrypt is intentionally slow)
TEST_WORK_FACTOR = 4


# Strategy for generating password strings
# Covers typical password characters including letters, digits, and common special chars
password_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + string.punctuation,
    min_size=1,  # Non-empty passwords (empty passwords raise ValueError)
    max_size=100
)

# Strategy for generating simple alphanumeric passwords
simple_password_strategy = st.text(
    alphabet=string.ascii_letters + string.digits,
    min_size=1,
    max_size=50
)

# Strategy for generating passwords with special characters
special_char_password_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?",
    min_size=1,
    max_size=50
)


class TestPasswordHashingSecurityProperty:
    """
    Property-based tests for password hashing security.
    
    # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
    
    Property Definition:
    "For any password string, when stored in the database, the stored value SHALL be 
    different from the original password AND the hash SHALL be verifiable against 
    the original password using the same hashing algorithm."
    
    **Validates: Requirements 1.2, 18.1**
    """
    
    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_hash_differs_from_original_password(self, password: str):
        """
        Property: For any password, hash(password) != password
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test verifies that the hashed password is always different from
        the original password, ensuring passwords are never stored in plaintext.
        """
        # Hash the password with low work factor for testing
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # The hash must be different from the original password
        assert hashed != password, (
            f"Hash should differ from original password. "
            f"Password: '{password}', Hash: '{hashed}'"
        )
    
    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_hash_is_verifiable_against_original(self, password: str):
        """
        Property: For any password, verify(password, hash(password)) == True
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test verifies that a hashed password can be verified against
        the original password using the same hashing algorithm.
        """
        # Hash the password with low work factor for testing
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # Verification with the original password should succeed
        assert verify_password(password, hashed), (
            f"Password verification should succeed for original password. "
            f"Password: '{password}'"
        )
    
    @given(password=password_strategy, wrong_password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_wrong_password_fails_verification(self, password: str, wrong_password: str):
        """
        Property: For any two different passwords, verify(wrong, hash(correct)) == False
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test verifies that verification fails when using a wrong password,
        ensuring the hashing algorithm correctly distinguishes between passwords.
        """
        # Skip if passwords happen to be the same
        assume(password != wrong_password)
        
        # Hash the correct password with low work factor for testing
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # Verification with wrong password should fail
        assert not verify_password(wrong_password, hashed), (
            f"Password verification should fail for wrong password. "
            f"Correct: '{password}', Wrong: '{wrong_password}'"
        )
    
    @given(password=simple_password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_hash_verifiable_simple_passwords(self, password: str):
        """
        Property: For any simple alphanumeric password, hash is verifiable
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test specifically targets simple alphanumeric passwords to ensure
        they are correctly hashed and verifiable.
        """
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # Hash should differ from original
        assert hashed != password
        
        # Hash should be verifiable
        assert verify_password(password, hashed)
    
    @given(password=special_char_password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_hash_verifiable_special_char_passwords(self, password: str):
        """
        Property: For any password with special characters, hash is verifiable
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test specifically targets passwords with special characters to ensure
        they are correctly hashed and verifiable.
        """
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # Hash should differ from original
        assert hashed != password
        
        # Hash should be verifiable
        assert verify_password(password, hashed)
    
    @given(password=password_strategy)
    @settings(max_examples=10, deadline=None)
    def test_multiple_hashes_are_different(self, password: str):
        """
        Property: For any password, hash(password) produces different results each time
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test verifies that bcrypt's salting produces different hashes
        for the same password, preventing rainbow table attacks.
        """
        # Hash the same password twice with low work factor for testing
        hash1 = hash_password(password, work_factor=TEST_WORK_FACTOR)
        hash2 = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # The two hashes should be different (due to random salt)
        assert hash1 != hash2, (
            f"Multiple hashes of the same password should differ due to salting. "
            f"Password: '{password}'"
        )
        
        # But both should verify against the original password
        assert verify_password(password, hash1), "First hash should verify"
        assert verify_password(password, hash2), "Second hash should verify"
    
    @given(password=st.text(min_size=1, max_size=72))
    @settings(max_examples=10, deadline=None)
    def test_unicode_passwords_hash_correctly(self, password: str):
        """
        Property: For any Unicode password, hash is different and verifiable
        
        # Feature: fyers-auto-trading-system, Property 2: Password Hashing Security
        **Validates: Requirements 1.2, 18.1**
        
        This test verifies that Unicode passwords (including non-ASCII characters)
        are correctly hashed and verifiable.
        
        Note: bcrypt has a 72-byte limit on password length, so we limit to 72 chars.
        """
        hashed = hash_password(password, work_factor=TEST_WORK_FACTOR)
        
        # Hash should differ from original
        assert hashed != password
        
        # Hash should be verifiable
        assert verify_password(password, hashed)
