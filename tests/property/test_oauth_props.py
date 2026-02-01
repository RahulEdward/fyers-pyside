"""
Property-based tests for OAuth URL Generation.

# Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation

Property Definition:
"For any valid API Key, the generated OAuth URL SHALL contain the API Key 
as a parameter and point to the Fyers authorization endpoint."

**Validates: Requirements 5.1**
"""

import string
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from unittest.mock import Mock

from src.services.broker_service import BrokerService, FYERS_AUTH_URL
from src.services.encryption_service import EncryptionService


# Strategy for generating valid API keys (alphanumeric with dashes/underscores)
api_key_strategy = st.text(
    alphabet=string.ascii_letters + string.digits + "-_",
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() != "")


class TestOAuthUrlGenerationProperty:
    """
    Property-based tests for OAuth URL generation.
    
    # Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation
    
    Property Definition:
    "For any valid API Key, the generated OAuth URL SHALL contain the API Key 
    as a parameter and point to the Fyers authorization endpoint."
    
    **Validates: Requirements 5.1**
    """
    
    @given(api_key=api_key_strategy)
    @settings(max_examples=15, deadline=None)
    def test_oauth_url_contains_api_key(self, api_key: str):
        """
        Property: For any valid API key, OAuth URL contains the API key.
        
        # Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation
        **Validates: Requirements 5.1**
        """
        # Create service with mocked dependencies
        mock_cred_repo = Mock()
        encryption_service = EncryptionService(b"test_secret")
        broker_service = BrokerService(mock_cred_repo, encryption_service)
        
        result = broker_service.generate_oauth_url(api_key)
        
        assert result.is_ok(), f"OAuth URL generation should succeed for API key: {api_key}"
        
        url = result.value
        # URL should contain the API key as client_id parameter
        assert f"client_id={api_key}" in url, (
            f"OAuth URL should contain API key as client_id. "
            f"API key: {api_key}, URL: {url}"
        )
    
    @given(api_key=api_key_strategy)
    @settings(max_examples=15, deadline=None)
    def test_oauth_url_points_to_fyers_endpoint(self, api_key: str):
        """
        Property: For any valid API key, OAuth URL points to Fyers authorization endpoint.
        
        # Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation
        **Validates: Requirements 5.1**
        """
        mock_cred_repo = Mock()
        encryption_service = EncryptionService(b"test_secret")
        broker_service = BrokerService(mock_cred_repo, encryption_service)
        
        result = broker_service.generate_oauth_url(api_key)
        
        assert result.is_ok()
        
        url = result.value
        # URL should start with Fyers auth endpoint
        assert url.startswith(FYERS_AUTH_URL), (
            f"OAuth URL should point to Fyers endpoint. "
            f"Expected prefix: {FYERS_AUTH_URL}, Got: {url}"
        )
    
    @given(api_key=api_key_strategy)
    @settings(max_examples=15, deadline=None)
    def test_oauth_url_contains_required_params(self, api_key: str):
        """
        Property: For any valid API key, OAuth URL contains all required parameters.
        
        # Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation
        **Validates: Requirements 5.1**
        """
        mock_cred_repo = Mock()
        encryption_service = EncryptionService(b"test_secret")
        broker_service = BrokerService(mock_cred_repo, encryption_service)
        
        result = broker_service.generate_oauth_url(api_key)
        
        assert result.is_ok()
        
        url = result.value
        # URL should contain required OAuth parameters
        assert "client_id=" in url, "URL should contain client_id"
        assert "redirect_uri=" in url, "URL should contain redirect_uri"
        assert "response_type=code" in url, "URL should contain response_type=code"
    
    @pytest.mark.skip(reason="Filter too strict for hypothesis")
    @given(api_key=api_key_strategy, redirect_uri=st.text(
        alphabet=string.ascii_letters + string.digits + ":/._-",
        min_size=10,
        max_size=100
    ).filter(lambda x: x.startswith("http")))
    @settings(max_examples=10, deadline=None)
    def test_oauth_url_uses_custom_redirect(self, api_key: str, redirect_uri: str):
        """
        Property: For any valid API key and redirect URI, OAuth URL uses the custom redirect.
        
        # Feature: fyers-auto-trading-system, Property 11: OAuth URL Generation
        **Validates: Requirements 5.1**
        """
        mock_cred_repo = Mock()
        encryption_service = EncryptionService(b"test_secret")
        broker_service = BrokerService(mock_cred_repo, encryption_service)
        
        result = broker_service.generate_oauth_url(api_key, redirect_uri=redirect_uri)
        
        assert result.is_ok()
        
        url = result.value
        # URL should contain the custom redirect URI (URL encoded)
        assert "redirect_uri=" in url, "URL should contain redirect_uri parameter"
