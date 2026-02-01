"""Broker credentials data models"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrokerCredentials:
    """Decrypted broker credentials"""
    api_key: str
    api_secret: str


@dataclass
class EncryptedCredentials:
    """Encrypted broker credentials stored in database"""
    user_id: int
    encrypted_api_key: str
    encrypted_api_secret: str
    access_token: Optional[str] = None
