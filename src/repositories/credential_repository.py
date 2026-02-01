"""Credential repository for database operations"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.schema import BrokerCredentialModel
from src.models.credentials import EncryptedCredentials


class CredentialRepository:
    """Repository for broker credential database operations"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def save(self, user_id: int, encrypted_api_key: str, encrypted_api_secret: str) -> None:
        """
        Save encrypted credentials for a user
        
        Args:
            user_id: User ID
            encrypted_api_key: Encrypted API key
            encrypted_api_secret: Encrypted API secret
        """
        # Check if credentials already exist
        existing = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).first()
        
        if existing:
            # Update existing credentials
            existing.encrypted_api_key = encrypted_api_key
            existing.encrypted_api_secret = encrypted_api_secret
            existing.updated_at = datetime.utcnow()
        else:
            # Create new credentials
            cred_model = BrokerCredentialModel(
                user_id=user_id,
                encrypted_api_key=encrypted_api_key,
                encrypted_api_secret=encrypted_api_secret
            )
            self.db_session.add(cred_model)
        
        self.db_session.commit()
    
    def get(self, user_id: int) -> Optional[EncryptedCredentials]:
        """
        Get encrypted credentials for a user
        
        Args:
            user_id: User ID
            
        Returns:
            EncryptedCredentials if found, None otherwise
        """
        cred_model = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).first()
        
        if cred_model:
            return self._to_credentials(cred_model)
        return None
    
    def exists(self, user_id: int) -> bool:
        """
        Check if credentials exist for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if exists, False otherwise
        """
        count = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).count()
        return count > 0
    
    def update_access_token(self, user_id: int, access_token: str) -> None:
        """
        Update access token for a user
        
        Args:
            user_id: User ID
            access_token: New access token
        """
        cred_model = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).first()
        
        if cred_model:
            cred_model.access_token = access_token
            cred_model.updated_at = datetime.utcnow()
            self.db_session.commit()
    
    def get_access_token(self, user_id: int) -> Optional[str]:
        """
        Get access token for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Access token if exists, None otherwise
        """
        cred_model = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).first()
        
        if cred_model:
            return cred_model.access_token
        return None
    
    def delete(self, user_id: int) -> bool:
        """
        Delete credentials for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if not found
        """
        result = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.user_id == user_id
        ).delete()
        self.db_session.commit()
        return result > 0
    
    def _to_credentials(self, model: BrokerCredentialModel) -> EncryptedCredentials:
        """Convert SQLAlchemy model to EncryptedCredentials dataclass"""
        return EncryptedCredentials(
            user_id=model.user_id,
            encrypted_api_key=model.encrypted_api_key,
            encrypted_api_secret=model.encrypted_api_secret,
            access_token=model.access_token
        )
    
    def save_with_username(self, broker_username: str, encrypted_api_key: str, encrypted_api_secret: str) -> int:
        """
        Save credentials with broker username (no user account required)
        
        Args:
            broker_username: Fyers client ID / username
            encrypted_api_key: Encrypted API key
            encrypted_api_secret: Encrypted API secret
            
        Returns:
            Credential ID
        """
        # Check if credentials already exist for this username
        existing = self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.broker_username == broker_username
        ).first()
        
        if existing:
            # Update existing credentials
            existing.encrypted_api_key = encrypted_api_key
            existing.encrypted_api_secret = encrypted_api_secret
            existing.updated_at = datetime.utcnow()
            self.db_session.commit()
            return existing.id
        else:
            # Create new credentials
            cred_model = BrokerCredentialModel(
                broker_username=broker_username,
                encrypted_api_key=encrypted_api_key,
                encrypted_api_secret=encrypted_api_secret
            )
            self.db_session.add(cred_model)
            self.db_session.commit()
            return cred_model.id
    
    def get_by_username(self, broker_username: str) -> Optional[BrokerCredentialModel]:
        """
        Get credentials by broker username
        
        Args:
            broker_username: Fyers client ID / username
            
        Returns:
            BrokerCredentialModel if found, None otherwise
        """
        return self.db_session.query(BrokerCredentialModel).filter(
            BrokerCredentialModel.broker_username == broker_username
        ).first()
    
    def get_last_used(self) -> Optional[BrokerCredentialModel]:
        """
        Get the most recently updated credentials
        
        Returns:
            BrokerCredentialModel if found, None otherwise
        """
        return self.db_session.query(BrokerCredentialModel).order_by(
            BrokerCredentialModel.updated_at.desc()
        ).first()
    
    def save_tokens(self, broker_username: str, access_token: str, 
                   feed_token: str = None, refresh_token: str = None) -> bool:
        """
        Save OAuth tokens for a broker user
        
        Args:
            broker_username: Fyers client ID
            access_token: OAuth access token
            feed_token: WebSocket feed token
            refresh_token: Token for refreshing access
            
        Returns:
            True if saved successfully
        """
        try:
            cred = self.db_session.query(BrokerCredentialModel).filter(
                BrokerCredentialModel.broker_username == broker_username
            ).first()
            
            if cred:
                cred.access_token = access_token
                if feed_token:
                    cred.feed_token = feed_token
                if refresh_token:
                    cred.refresh_token = refresh_token
                cred.updated_at = datetime.utcnow()
                self.db_session.commit()
                return True
            return False
        except Exception as e:
            self.db_session.rollback()
            return False
    
    def get_tokens(self, broker_username: str) -> Optional[dict]:
        """
        Get all tokens for a broker user
        
        Args:
            broker_username: Fyers client ID
            
        Returns:
            Dict with tokens or None
        """
        try:
            cred = self.db_session.query(BrokerCredentialModel).filter(
                BrokerCredentialModel.broker_username == broker_username
            ).first()
            
            if cred:
                return {
                    'access_token': cred.access_token,
                    'feed_token': cred.feed_token,
                    'refresh_token': cred.refresh_token
                }
            return None
        except:
            return None
