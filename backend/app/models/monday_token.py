"""
Monday.com Token Storage Model
Secure encrypted storage for OAuth tokens
"""

from datetime import datetime, timedelta
import os
from cryptography.fernet import Fernet
import json
import logging

logger = logging.getLogger(__name__)

# Initialize encryption (in production, use AWS KMS or similar)
ENCRYPTION_KEY = os.getenv('MONDAY_TOKEN_ENCRYPTION_KEY')
if ENCRYPTION_KEY:
    cipher = Fernet(ENCRYPTION_KEY.encode())
else:
    cipher = None
    logger.warning("Token encryption not configured. Using plaintext storage (NOT recommended for production)")


class MondayToken:
    """Model for storing Monday.com OAuth tokens securely"""
    
    def __init__(self, workspace_id: str, access_token: str, 
                 expires_in: int = 3600, user_id: str = None, 
                 token_type: str = 'Bearer'):
        self.workspace_id = workspace_id
        self._access_token = access_token  # Will be encrypted
        self.expires_in = expires_in
        self.expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()
        self.user_id = user_id
        self.token_type = token_type
        self.created_at = datetime.utcnow().isoformat()
        self.last_used = None
    
    @property
    def access_token(self) -> str:
        """Get decrypted access token"""
        if cipher and isinstance(self._access_token, bytes):
            return cipher.decrypt(self._access_token).decode()
        return self._access_token
    
    @access_token.setter
    def access_token(self, token: str):
        """Set and encrypt access token"""
        if cipher:
            self._access_token = cipher.encrypt(token.encode())
        else:
            self._access_token = token
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired"""
        expires_at = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expires_at
    
    @property
    def is_expiring_soon(self) -> bool:
        """Check if token expiring in next 5 minutes"""
        expires_at = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > (expires_at - timedelta(minutes=5))
    
    def mark_used(self):
        """Update last used timestamp"""
        self.last_used = datetime.utcnow().isoformat()
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for JSON serialization)"""
        return {
            'workspace_id': self.workspace_id,
            'token_type': self.token_type,
            'expires_at': self.expires_at,
            'created_at': self.created_at,
            'last_used': self.last_used,
            'user_id': self.user_id,
            'is_expired': self.is_expired,
            'is_expiring_soon': self.is_expiring_soon
            # NOTE: access_token NOT included in serialization
        }
    
    def __repr__(self):
        return f"<MondayToken workspace={self.workspace_id} expires={self.expires_at}>"


class TokenManager:
    """Manage Monday.com OAuth tokens"""
    
    # In-memory cache for demo (replace with database in production)
    _token_cache = {}
    
    @classmethod
    def save_token(cls, token: MondayToken) -> bool:
        """Save token securely"""
        try:
            cls._token_cache[token.workspace_id] = token
            logger.info(f"Token saved for workspace: {token.workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
            return False
    
    @classmethod
    def get_token(cls, workspace_id: str) -> MondayToken:
        """Retrieve token"""
        token = cls._token_cache.get(workspace_id)
        
        if token is None:
            logger.warning(f"No token found for workspace: {workspace_id}")
            return None
        
        if token.is_expired:
            logger.warning(f"Token expired for workspace: {workspace_id}")
            cls.delete_token(workspace_id)
            return None
        
        token.mark_used()
        return token
    
    @classmethod
    def delete_token(cls, workspace_id: str) -> bool:
        """Delete token (when user disconnects)"""
        try:
            if workspace_id in cls._token_cache:
                del cls._token_cache[workspace_id]
                logger.info(f"Token deleted for workspace: {workspace_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete token: {e}")
            return False
    
    @classmethod
    def list_tokens(cls) -> list:
        """List all stored tokens (metadata only, not actual tokens)"""
        return [
            token.to_dict() 
            for token in cls._token_cache.values()
        ]
    
    @classmethod
    def refresh_token(cls, workspace_id: str, new_token: str, 
                     expires_in: int = 3600) -> bool:
        """Refresh expired token"""
        token = cls._token_cache.get(workspace_id)
        if token:
            token.access_token = new_token
            token.expires_in = expires_in
            token.expires_at = (
                datetime.utcnow() + timedelta(seconds=expires_in)
            ).isoformat()
            logger.info(f"Token refreshed for workspace: {workspace_id}")
            return True
        return False


# Database Model (for SQLAlchemy/Flask-SQLAlchemy)
# Use this in production with a real database

try:
    from flask_sqlalchemy import SQLAlchemy
    db = SQLAlchemy()
    
    class MondayTokenDB(db.Model):
        """Database model for Monday.com tokens"""
        
        __tablename__ = 'monday_tokens'
        
        id = db.Column(db.Integer, primary_key=True)
        workspace_id = db.Column(db.String(255), unique=True, nullable=False)
        access_token = db.Column(db.Text, nullable=False)  # Encrypted
        token_type = db.Column(db.String(50), default='Bearer')
        expires_at = db.Column(db.DateTime, nullable=False)
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_used = db.Column(db.DateTime)
        user_id = db.Column(db.String(255))
        user_name = db.Column(db.String(255))
        user_email = db.Column(db.String(255))
        
        def to_monday_token(self) -> MondayToken:
            """Convert database model to MondayToken"""
            token = MondayToken(
                workspace_id=self.workspace_id,
                access_token=self.access_token,
                user_id=self.user_id,
                token_type=self.token_type
            )
            token.created_at = self.created_at.isoformat()
            token.expires_at = self.expires_at.isoformat()
            if self.last_used:
                token.last_used = self.last_used.isoformat()
            return token
        
        @staticmethod
        def from_monday_token(token: MondayToken) -> 'MondayTokenDB':
            """Create database model from MondayToken"""
            return MondayTokenDB(
                workspace_id=token.workspace_id,
                access_token=token.access_token,
                token_type=token.token_type,
                expires_at=datetime.fromisoformat(token.expires_at),
                created_at=datetime.fromisoformat(token.created_at),
                user_id=token.user_id
            )

except ImportError:
    MondayTokenDB = None
    logger.warning("Flask-SQLAlchemy not available. Using in-memory token storage.")
