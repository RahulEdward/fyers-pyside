"""
Broker Service for managing Fyers broker credentials and authentication.

This module provides functionality for securely storing broker credentials,
generating OAuth URLs, and authenticating with the Fyers broker API.

Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.4, 5.5
"""

import os
from typing import Optional
from urllib.parse import urlencode

from src.models.credentials import BrokerCredentials, EncryptedCredentials
from src.models.result import Result, Ok, Err
from src.repositories.credential_repository import CredentialRepository
from src.services.encryption_service import EncryptionService


# Fyers OAuth configuration
FYERS_AUTH_URL = "https://api-t1.fyers.in/api/v3/generate-authcode"
FYERS_REDIRECT_URI = "http://127.0.0.1:8765/callback"
FYERS_RESPONSE_TYPE = "code"
FYERS_STATE = "fyers_auth"


class BrokerService:
    """
    Service for managing Fyers broker credentials and authentication.
    
    This service handles:
    - Encrypting and storing broker API credentials
    - Retrieving and decrypting stored credentials
    - Generating OAuth authorization URLs
    - Authenticating with Fyers API using request tokens
    - Storing access tokens for API calls
    """
    
    def __init__(self, cred_repo: CredentialRepository, encryption_service: EncryptionService):
        """
        Initialize BrokerService with dependencies.
        
        Args:
            cred_repo: Repository for credential database operations
            encryption_service: Service for encrypting/decrypting credentials
        
        Raises:
            ValueError: If cred_repo or encryption_service is None
        """
        if cred_repo is None:
            raise ValueError("cred_repo cannot be None")
        if encryption_service is None:
            raise ValueError("encryption_service cannot be None")
        
        self._cred_repo = cred_repo
        self._encryption_service = encryption_service
    
    def save_credentials(self, user_id: int, api_key: str, api_secret: str) -> Result[None, str]:
        """
        Encrypt and store broker credentials for a user.
        
        Args:
            user_id: The user's ID
            api_key: Fyers API key (plaintext)
            api_secret: Fyers API secret (plaintext)
        
        Returns:
            Result[None, str]: Ok(None) on success, Err(str) on failure
        
        Requirements: 4.1, 4.2, 4.3
        """
        # Validate inputs (Requirement 4.1)
        if not api_key or not api_key.strip():
            return Err("API key cannot be empty")
        
        if not api_secret or not api_secret.strip():
            return Err("API secret cannot be empty")
        
        api_key = api_key.strip()
        api_secret = api_secret.strip()
        
        try:
            # Encrypt credentials (Requirement 4.2)
            encrypted_api_key = self._encryption_service.encrypt(api_key)
            encrypted_api_secret = self._encryption_service.encrypt(api_secret)
            
            # Store in database (Requirement 4.3)
            self._cred_repo.save(user_id, encrypted_api_key, encrypted_api_secret)
            
            return Ok(None)
        
        except Exception as e:
            return Err(f"Failed to save credentials: {str(e)}")
    
    def get_credentials(self, user_id: int) -> Result[BrokerCredentials, str]:
        """
        Retrieve and decrypt broker credentials for a user.
        
        Args:
            user_id: The user's ID
        
        Returns:
            Result[BrokerCredentials, str]: Ok(BrokerCredentials) on success, Err(str) on failure
        
        Requirements: 4.4
        """
        try:
            # Get encrypted credentials from database
            encrypted_creds = self._cred_repo.get(user_id)
            
            if encrypted_creds is None:
                return Err("No credentials found for user")
            
            # Decrypt credentials (Requirement 4.4)
            api_key = self._encryption_service.decrypt(encrypted_creds.encrypted_api_key)
            api_secret = self._encryption_service.decrypt(encrypted_creds.encrypted_api_secret)
            
            return Ok(BrokerCredentials(api_key=api_key, api_secret=api_secret))
        
        except Exception as e:
            return Err(f"Failed to retrieve credentials: {str(e)}")
    
    def has_credentials(self, user_id: int) -> bool:
        """
        Check if a user has stored broker credentials.
        
        Args:
            user_id: The user's ID
        
        Returns:
            True if credentials exist, False otherwise
        """
        return self._cred_repo.exists(user_id)
    
    def generate_oauth_url(self, api_key: str, redirect_uri: str = None) -> Result[str, str]:
        """
        Generate Fyers OAuth authorization URL.
        
        Args:
            api_key: Fyers API key
            redirect_uri: Optional custom redirect URI (defaults to localhost)
        
        Returns:
            Result[str, str]: Ok(url) on success, Err(str) on failure
        
        Requirements: 5.1
        """
        if not api_key or not api_key.strip():
            return Err("API key cannot be empty")
        
        api_key = api_key.strip()
        redirect = redirect_uri or FYERS_REDIRECT_URI
        
        # Build OAuth URL parameters
        params = {
            "client_id": api_key,
            "redirect_uri": redirect,
            "response_type": FYERS_RESPONSE_TYPE,
            "state": FYERS_STATE,
            "scope": "openid"
        }
        
        # Construct full URL
        oauth_url = f"{FYERS_AUTH_URL}?{urlencode(params)}"
        
        return Ok(oauth_url)
    
    def authenticate_broker(self, user_id: int, request_token: str) -> Result[str, str]:
        """
        Exchange request token for access token using Fyers API.
        
        This method retrieves stored credentials, sets them as environment
        variables, and calls the existing auth_api to get an access token.
        
        Args:
            user_id: The user's ID
            request_token: Authorization code from Fyers OAuth callback
        
        Returns:
            Result[str, str]: Ok(access_token) on success, Err(str) on failure
        
        Requirements: 5.4, 5.5
        """
        if not request_token or not request_token.strip():
            return Err("Request token cannot be empty")
        
        request_token = request_token.strip()
        
        # Get user's credentials
        creds_result = self.get_credentials(user_id)
        if creds_result.is_err():
            return Err(f"Cannot authenticate: {creds_result.error}")
        
        creds = creds_result.value
        
        try:
            # Set environment variables for auth_api
            os.environ['BROKER_API_KEY'] = creds.api_key
            os.environ['BROKER_API_SECRET'] = creds.api_secret
            
            # Import and call existing auth_api
            from fyers.api.auth_api import authenticate_broker as fyers_authenticate
            
            access_token, response_data = fyers_authenticate(request_token)
            
            if access_token:
                # Store access token (Requirement 5.5)
                self.store_access_token(user_id, access_token)
                return Ok(access_token)
            else:
                error_msg = response_data.get('message', 'Authentication failed')
                return Err(error_msg)
        
        except ImportError:
            return Err("Fyers API module not available")
        
        except Exception as e:
            return Err(f"Authentication failed: {str(e)}")
        
        finally:
            # Clean up environment variables
            os.environ.pop('BROKER_API_KEY', None)
            os.environ.pop('BROKER_API_SECRET', None)
    
    def store_access_token(self, user_id: int, access_token: str) -> Result[None, str]:
        """
        Store access token for a user.
        
        Args:
            user_id: The user's ID
            access_token: Fyers API access token
        
        Returns:
            Result[None, str]: Ok(None) on success, Err(str) on failure
        
        Requirements: 5.5
        """
        if not access_token or not access_token.strip():
            return Err("Access token cannot be empty")
        
        try:
            self._cred_repo.update_access_token(user_id, access_token.strip())
            return Ok(None)
        
        except Exception as e:
            return Err(f"Failed to store access token: {str(e)}")
    
    def get_access_token(self, user_id: int) -> Optional[str]:
        """
        Get stored access token for a user.
        
        Args:
            user_id: The user's ID
        
        Returns:
            Access token if exists, None otherwise
        """
        return self._cred_repo.get_access_token(user_id)
    
    def has_valid_access_token(self, user_id: int) -> bool:
        """
        Check if user has a stored access token.
        
        Args:
            user_id: The user's ID
        
        Returns:
            True if access token exists, False otherwise
        """
        token = self.get_access_token(user_id)
        return token is not None and len(token) > 0
    
    def delete_credentials(self, user_id: int) -> bool:
        """
        Delete stored credentials for a user.
        
        Args:
            user_id: The user's ID
        
        Returns:
            True if deleted, False if not found
        """
        return self._cred_repo.delete(user_id)
    
    def save_broker_credentials(self, broker_username: str, api_key: str, api_secret: str) -> Result[int, str]:
        """
        Save broker credentials with username (no user account required).
        
        Args:
            broker_username: Fyers client ID / username
            api_key: Fyers API key (plaintext)
            api_secret: Fyers API secret (plaintext)
        
        Returns:
            Result[int, str]: Ok(credential_id) on success, Err(str) on failure
        """
        # Validate inputs
        if not broker_username or not broker_username.strip():
            return Err("Broker username cannot be empty")
        
        if not api_key or not api_key.strip():
            return Err("API key cannot be empty")
        
        if not api_secret or not api_secret.strip():
            return Err("API secret cannot be empty")
        
        broker_username = broker_username.strip().upper()
        api_key = api_key.strip()
        api_secret = api_secret.strip()
        
        try:
            # Encrypt credentials
            encrypted_api_key = self._encryption_service.encrypt(api_key)
            encrypted_api_secret = self._encryption_service.encrypt(api_secret)
            
            # Save to database
            credential_id = self._cred_repo.save_with_username(
                broker_username=broker_username,
                encrypted_api_key=encrypted_api_key,
                encrypted_api_secret=encrypted_api_secret
            )
            
            return Ok(credential_id)
        
        except Exception as e:
            return Err(f"Failed to save credentials: {str(e)}")
    
    def get_credentials_by_username(self, broker_username: str) -> Result[dict, str]:
        """
        Get credentials by broker username.
        
        Args:
            broker_username: Fyers client ID / username
        
        Returns:
            Result[dict, str]: Ok(credentials_dict) on success, Err(str) on failure
        """
        try:
            encrypted_creds = self._cred_repo.get_by_username(broker_username)
            
            if encrypted_creds is None:
                return Err("No credentials found for this username")
            
            # Decrypt credentials
            api_key = self._encryption_service.decrypt(encrypted_creds.encrypted_api_key)
            api_secret = self._encryption_service.decrypt(encrypted_creds.encrypted_api_secret)
            
            return Ok({
                'id': encrypted_creds.id,
                'broker_username': broker_username,
                'api_key': api_key,
                'api_secret': api_secret,
                'access_token': encrypted_creds.access_token
            })
        
        except Exception as e:
            return Err(f"Failed to retrieve credentials: {str(e)}")
    
    def get_last_credentials(self) -> Result[dict, str]:
        """
        Get the most recently used credentials.
        
        Returns:
            Result[dict, str]: Ok(credentials_dict) on success, Err(str) on failure
        """
        try:
            creds = self._cred_repo.get_last_used()
            if creds:
                return Ok({
                    'broker_username': creds.broker_username,
                    'id': creds.id
                })
            return Err("No saved credentials found")
        except Exception as e:
            return Err(f"Failed to get credentials: {str(e)}")
