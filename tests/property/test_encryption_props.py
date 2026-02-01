"""
Property-based tests for EncryptionService.

# Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip

This module contains property-based tests using Hypothesis to verify that the
encryption service correctly implements round-trip encryption/decryption for
any valid credential string.

**Validates: Requirements 4.2, 4.3, 4.4, 18.2**
"""

import string
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from src.services.encryption_service import EncryptionService


# Strategy for generating random credential strings
# This covers typical API key/secret formats and various string types
credential_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + string.punctuation + " ",
    min_size=0,
    max_size=500
)

# Strategy for generating API key-like strings (alphanumeric with dashes/underscores)
api_key_strategy = st.text(
    alphabet=string.ascii_uppercase + string.digits + "-_",
    min_size=1,
    max_size=100
)

# Strategy for generating API secret-like strings (more complex characters)
api_secret_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?",
    min_size=1,
    max_size=200
)

# Strategy for generating encryption keys
encryption_key_strategy = st.binary(min_size=8, max_size=64)


class TestEncryptionRoundTripProperty:
    """
    Property-based tests for encryption round-trip.
    
    # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
    
    Property Definition:
    "For any broker credentials (API Key, API Secret), encrypting then decrypting 
    SHALL return the original values."
    
    **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
    """
    
    @given(plaintext=credential_strategy, key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypt_decrypt_round_trip_any_string(self, plaintext: str, key: bytes):
        """
        Property: For any valid string, encrypt(decrypt(x)) == x
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test verifies that any random string can be encrypted and then
        decrypted back to the original value, ensuring data integrity.
        """
        # Ensure key is not empty (required by EncryptionService)
        assume(len(key) > 0)
        
        service = EncryptionService(key)
        
        # Encrypt the plaintext
        encrypted = service.encrypt(plaintext)
        
        # Decrypt the ciphertext
        decrypted = service.decrypt(encrypted)
        
        # Verify round-trip: original == decrypted
        assert decrypted == plaintext, (
            f"Round-trip failed: original '{plaintext}' != decrypted '{decrypted}'"
        )
    
    @given(api_key=api_key_strategy, key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypt_decrypt_api_key_format(self, api_key: str, key: bytes):
        """
        Property: For any API key format string, encrypt(decrypt(x)) == x
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test specifically targets API key formats (uppercase alphanumeric
        with dashes and underscores) to ensure they survive encryption round-trip.
        """
        assume(len(key) > 0)
        
        service = EncryptionService(key)
        
        encrypted = service.encrypt(api_key)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == api_key, (
            f"API key round-trip failed: original '{api_key}' != decrypted '{decrypted}'"
        )
    
    @given(api_secret=api_secret_strategy, key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypt_decrypt_api_secret_format(self, api_secret: str, key: bytes):
        """
        Property: For any API secret format string, encrypt(decrypt(x)) == x
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test specifically targets API secret formats (mixed case with
        special characters) to ensure they survive encryption round-trip.
        """
        assume(len(key) > 0)
        
        service = EncryptionService(key)
        
        encrypted = service.encrypt(api_secret)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == api_secret, (
            f"API secret round-trip failed: original '{api_secret}' != decrypted '{decrypted}'"
        )
    
    @given(length=st.integers(min_value=0, max_value=1000), key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypt_decrypt_various_lengths(self, length: int, key: bytes):
        """
        Property: For any string length, encrypt(decrypt(x)) == x
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test verifies that strings of various lengths (from empty to 1000 chars)
        can be encrypted and decrypted correctly.
        """
        assume(len(key) > 0)
        
        # Generate a string of the specified length
        plaintext = "A" * length
        
        service = EncryptionService(key)
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext, (
            f"Length {length} round-trip failed"
        )
    
    @given(plaintext=st.text(min_size=0, max_size=200), key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypt_decrypt_unicode_strings(self, plaintext: str, key: bytes):
        """
        Property: For any Unicode string, encrypt(decrypt(x)) == x
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test verifies that Unicode strings (including emojis, non-Latin
        characters, etc.) can be encrypted and decrypted correctly.
        """
        assume(len(key) > 0)
        
        service = EncryptionService(key)
        
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)
        
        assert decrypted == plaintext, (
            f"Unicode round-trip failed for string of length {len(plaintext)}"
        )
    
    @given(key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_encrypted_differs_from_plaintext(self, key: bytes):
        """
        Property: For any non-empty plaintext, encrypted != plaintext
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test verifies that encryption actually transforms the data,
        ensuring credentials are not stored in plaintext.
        """
        assume(len(key) > 0)
        
        plaintext = "FYERS-API-KEY-12345"  # Non-empty test credential
        
        service = EncryptionService(key)
        
        encrypted = service.encrypt(plaintext)
        
        # Encrypted value should be different from plaintext
        assert encrypted != plaintext, (
            "Encrypted value should differ from plaintext"
        )
    
    @given(key=encryption_key_strategy)
    @settings(max_examples=25)
    def test_same_key_consistent_decryption(self, key: bytes):
        """
        Property: Same key produces consistent decryption results
        
        # Feature: fyers-auto-trading-system, Property 10: Credential Encryption Round-Trip
        **Validates: Requirements 4.2, 4.3, 4.4, 18.2**
        
        This test verifies that two EncryptionService instances with the same
        key can decrypt each other's ciphertexts.
        """
        assume(len(key) > 0)
        
        plaintext = "test_api_secret_value"
        
        service1 = EncryptionService(key)
        service2 = EncryptionService(key)
        
        # Encrypt with service1
        encrypted = service1.encrypt(plaintext)
        
        # Decrypt with service2 (same key)
        decrypted = service2.decrypt(encrypted)
        
        assert decrypted == plaintext, (
            "Same key should produce consistent decryption"
        )

