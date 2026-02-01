"""
Unit tests for BrokerService.

Tests broker credential management, OAuth URL generation, and authentication.

Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.4, 5.5
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.schema import Base
from src.repositories.user_repository import UserRepository
from src.repositories.credential_repository import CredentialRepository
from src.services.encryption_service import EncryptionService
from src.services.broker_service import BrokerService, FYERS_AUTH_URL
from src.models.credentials import BrokerCredentials


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def user_repo(db_session):
    """Create a UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
def cred_repo(db_session):
    """Create a CredentialRepository instance."""
    return CredentialRepository(db_session)


@pytest.fixture
def encryption_service():
    """Create an EncryptionService instance."""
    return EncryptionService(b"test_app_secret_key_12345")


@pytest.fixture
def broker_service(cred_repo, encryption_service):
    """Create a BrokerService instance."""
    return BrokerService(cred_repo, encryption_service)


@pytest.fixture
def test_user(user_repo):
    """Create a test user."""
    return user_repo.create("broker_user", "hashed_pass", "broker@example.com")


class TestBrokerServiceInit:
    """Tests for BrokerService initialization."""
    
    def test_init_with_valid_dependencies(self, cred_repo, encryption_service):
        """Test initialization with valid dependencies."""
        service = BrokerService(cred_repo, encryption_service)
        assert service._cred_repo is cred_repo
        assert service._encryption_service is encryption_service
    
    def test_init_with_none_cred_repo_raises_error(self, encryption_service):
        """Test initialization with None cred_repo raises ValueError."""
        with pytest.raises(ValueError, match="cred_repo cannot be None"):
            BrokerService(None, encryption_service)
    
    def test_init_with_none_encryption_service_raises_error(self, cred_repo):
        """Test initialization with None encryption_service raises ValueError."""
        with pytest.raises(ValueError, match="encryption_service cannot be None"):
            BrokerService(cred_repo, None)


class TestSaveCredentials:
    """Tests for BrokerService.save_credentials()."""
    
    def test_save_credentials_success(self, broker_service, test_user):
        """Test successful credential saving."""
        result = broker_service.save_credentials(
            test_user.id, "API_KEY_123", "API_SECRET_456"
        )
        
        assert result.is_ok()
        assert broker_service.has_credentials(test_user.id)
    
    def test_save_credentials_empty_api_key_fails(self, broker_service, test_user):
        """Test saving with empty API key fails."""
        result = broker_service.save_credentials(test_user.id, "", "API_SECRET")
        
        assert result.is_err()
        assert result.error == "API key cannot be empty"
    
    def test_save_credentials_whitespace_api_key_fails(self, broker_service, test_user):
        """Test saving with whitespace API key fails."""
        result = broker_service.save_credentials(test_user.id, "   ", "API_SECRET")
        
        assert result.is_err()
        assert result.error == "API key cannot be empty"
    
    def test_save_credentials_none_api_key_fails(self, broker_service, test_user):
        """Test saving with None API key fails."""
        result = broker_service.save_credentials(test_user.id, None, "API_SECRET")
        
        assert result.is_err()
        assert result.error == "API key cannot be empty"
    
    def test_save_credentials_empty_api_secret_fails(self, broker_service, test_user):
        """Test saving with empty API secret fails."""
        result = broker_service.save_credentials(test_user.id, "API_KEY", "")
        
        assert result.is_err()
        assert result.error == "API secret cannot be empty"
    
    def test_save_credentials_none_api_secret_fails(self, broker_service, test_user):
        """Test saving with None API secret fails."""
        result = broker_service.save_credentials(test_user.id, "API_KEY", None)
        
        assert result.is_err()
        assert result.error == "API secret cannot be empty"
    
    def test_save_credentials_trims_values(self, broker_service, test_user):
        """Test that credentials are trimmed."""
        result = broker_service.save_credentials(
            test_user.id, "  API_KEY  ", "  API_SECRET  "
        )
        
        assert result.is_ok()
        
        # Verify trimmed values are stored
        creds_result = broker_service.get_credentials(test_user.id)
        assert creds_result.is_ok()
        assert creds_result.value.api_key == "API_KEY"
        assert creds_result.value.api_secret == "API_SECRET"
    
    def test_save_credentials_updates_existing(self, broker_service, test_user):
        """Test that saving credentials updates existing ones."""
        # Save initial credentials
        broker_service.save_credentials(test_user.id, "OLD_KEY", "OLD_SECRET")
        
        # Update credentials
        result = broker_service.save_credentials(test_user.id, "NEW_KEY", "NEW_SECRET")
        
        assert result.is_ok()
        
        # Verify updated values
        creds_result = broker_service.get_credentials(test_user.id)
        assert creds_result.value.api_key == "NEW_KEY"
        assert creds_result.value.api_secret == "NEW_SECRET"


class TestGetCredentials:
    """Tests for BrokerService.get_credentials()."""
    
    def test_get_credentials_success(self, broker_service, test_user):
        """Test successful credential retrieval."""
        broker_service.save_credentials(test_user.id, "MY_API_KEY", "MY_API_SECRET")
        
        result = broker_service.get_credentials(test_user.id)
        
        assert result.is_ok()
        assert isinstance(result.value, BrokerCredentials)
        assert result.value.api_key == "MY_API_KEY"
        assert result.value.api_secret == "MY_API_SECRET"
    
    def test_get_credentials_not_found(self, broker_service, test_user):
        """Test getting credentials when none exist."""
        result = broker_service.get_credentials(test_user.id)
        
        assert result.is_err()
        assert result.error == "No credentials found for user"
    
    def test_get_credentials_decrypts_correctly(self, broker_service, test_user, cred_repo):
        """Test that credentials are properly decrypted."""
        # Save credentials
        broker_service.save_credentials(test_user.id, "DECRYPT_KEY", "DECRYPT_SECRET")
        
        # Verify stored values are encrypted (different from original)
        encrypted = cred_repo.get(test_user.id)
        assert encrypted.encrypted_api_key != "DECRYPT_KEY"
        assert encrypted.encrypted_api_secret != "DECRYPT_SECRET"
        
        # Verify decryption returns original values
        result = broker_service.get_credentials(test_user.id)
        assert result.value.api_key == "DECRYPT_KEY"
        assert result.value.api_secret == "DECRYPT_SECRET"


class TestHasCredentials:
    """Tests for BrokerService.has_credentials()."""
    
    def test_has_credentials_true(self, broker_service, test_user):
        """Test has_credentials returns True when credentials exist."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        
        assert broker_service.has_credentials(test_user.id) is True
    
    def test_has_credentials_false(self, broker_service, test_user):
        """Test has_credentials returns False when no credentials."""
        assert broker_service.has_credentials(test_user.id) is False


class TestGenerateOAuthUrl:
    """Tests for BrokerService.generate_oauth_url()."""
    
    def test_generate_oauth_url_success(self, broker_service):
        """Test successful OAuth URL generation."""
        result = broker_service.generate_oauth_url("MY_API_KEY")
        
        assert result.is_ok()
        url = result.value
        assert FYERS_AUTH_URL in url
        assert "client_id=MY_API_KEY" in url
        assert "response_type=code" in url
    
    def test_generate_oauth_url_contains_redirect_uri(self, broker_service):
        """Test OAuth URL contains redirect URI."""
        result = broker_service.generate_oauth_url("API_KEY")
        
        assert result.is_ok()
        assert "redirect_uri=" in result.value
    
    def test_generate_oauth_url_custom_redirect(self, broker_service):
        """Test OAuth URL with custom redirect URI."""
        custom_redirect = "https://myapp.com/callback"
        result = broker_service.generate_oauth_url("API_KEY", redirect_uri=custom_redirect)
        
        assert result.is_ok()
        assert "myapp.com" in result.value
    
    def test_generate_oauth_url_empty_api_key_fails(self, broker_service):
        """Test OAuth URL generation with empty API key fails."""
        result = broker_service.generate_oauth_url("")
        
        assert result.is_err()
        assert result.error == "API key cannot be empty"
    
    def test_generate_oauth_url_none_api_key_fails(self, broker_service):
        """Test OAuth URL generation with None API key fails."""
        result = broker_service.generate_oauth_url(None)
        
        assert result.is_err()
        assert result.error == "API key cannot be empty"
    
    def test_generate_oauth_url_trims_api_key(self, broker_service):
        """Test that API key is trimmed in OAuth URL."""
        result = broker_service.generate_oauth_url("  TRIMMED_KEY  ")
        
        assert result.is_ok()
        assert "client_id=TRIMMED_KEY" in result.value


class TestStoreAccessToken:
    """Tests for BrokerService.store_access_token()."""
    
    def test_store_access_token_success(self, broker_service, test_user):
        """Test successful access token storage."""
        # First save credentials
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        
        result = broker_service.store_access_token(test_user.id, "ACCESS_TOKEN_123")
        
        assert result.is_ok()
        assert broker_service.get_access_token(test_user.id) == "ACCESS_TOKEN_123"
    
    def test_store_access_token_empty_fails(self, broker_service, test_user):
        """Test storing empty access token fails."""
        result = broker_service.store_access_token(test_user.id, "")
        
        assert result.is_err()
        assert result.error == "Access token cannot be empty"
    
    def test_store_access_token_none_fails(self, broker_service, test_user):
        """Test storing None access token fails."""
        result = broker_service.store_access_token(test_user.id, None)
        
        assert result.is_err()
        assert result.error == "Access token cannot be empty"


class TestGetAccessToken:
    """Tests for BrokerService.get_access_token()."""
    
    def test_get_access_token_success(self, broker_service, test_user):
        """Test successful access token retrieval."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        broker_service.store_access_token(test_user.id, "MY_TOKEN")
        
        token = broker_service.get_access_token(test_user.id)
        
        assert token == "MY_TOKEN"
    
    def test_get_access_token_none_when_not_set(self, broker_service, test_user):
        """Test get_access_token returns None when not set."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        
        token = broker_service.get_access_token(test_user.id)
        
        assert token is None
    
    def test_get_access_token_none_when_no_credentials(self, broker_service, test_user):
        """Test get_access_token returns None when no credentials."""
        token = broker_service.get_access_token(test_user.id)
        
        assert token is None


class TestHasValidAccessToken:
    """Tests for BrokerService.has_valid_access_token()."""
    
    def test_has_valid_access_token_true(self, broker_service, test_user):
        """Test has_valid_access_token returns True when token exists."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        broker_service.store_access_token(test_user.id, "VALID_TOKEN")
        
        assert broker_service.has_valid_access_token(test_user.id) is True
    
    def test_has_valid_access_token_false_no_token(self, broker_service, test_user):
        """Test has_valid_access_token returns False when no token."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        
        assert broker_service.has_valid_access_token(test_user.id) is False
    
    def test_has_valid_access_token_false_no_credentials(self, broker_service, test_user):
        """Test has_valid_access_token returns False when no credentials."""
        assert broker_service.has_valid_access_token(test_user.id) is False


class TestDeleteCredentials:
    """Tests for BrokerService.delete_credentials()."""
    
    def test_delete_credentials_success(self, broker_service, test_user):
        """Test successful credential deletion."""
        broker_service.save_credentials(test_user.id, "KEY", "SECRET")
        
        result = broker_service.delete_credentials(test_user.id)
        
        assert result is True
        assert broker_service.has_credentials(test_user.id) is False
    
    def test_delete_credentials_not_found(self, broker_service, test_user):
        """Test deleting non-existent credentials."""
        result = broker_service.delete_credentials(test_user.id)
        
        assert result is False
