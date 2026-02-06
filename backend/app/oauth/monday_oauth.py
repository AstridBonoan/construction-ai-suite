"""
Monday.com OAuth 2.0 Service

Handles authorization flow, token management, and multi-tenant storage.
Implements secure token refresh and tenant isolation.
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import requests
from functools import wraps

# Configuration
MONDAY_CLIENT_ID = os.getenv("MONDAY_CLIENT_ID", "demo_client_id_placeholder")
MONDAY_CLIENT_SECRET = os.getenv("MONDAY_CLIENT_SECRET", "demo_client_secret_placeholder")
MONDAY_REDIRECT_URI = os.getenv("MONDAY_REDIRECT_URI", "http://localhost:5000/oauth/callback")
MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_AUTH_URL = "https://auth.monday.com/oauth/authorize"
MONDAY_TOKEN_URL = "https://auth.monday.com/oauth/token"

# In-memory tenant storage (replace with database in production)
TENANT_STORAGE = {}
OAUTH_STATE_STORAGE = {}


class OAuthError(Exception):
    """OAuth service error."""
    pass


class TenantConfig:
    """Multi-tenant configuration and token storage."""
    
    def __init__(self, tenant_id: str, workspace_id: str = None):
        self.tenant_id = tenant_id
        self.workspace_id = workspace_id
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.board_config = {}  # board_id -> project mapping
        self.sync_enabled = False
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "has_token": self.access_token is not None,
            "sync_enabled": self.sync_enabled,
            "board_config": self.board_config,
            "token_expires_at": self.token_expires_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def is_token_expired(self) -> bool:
        """Check if access token expired."""
        if not self.token_expires_at:
            return True
        return datetime.fromisoformat(self.token_expires_at) < datetime.utcnow()
    
    def set_tokens(self, access_token: str, refresh_token: str, expires_in: int):
        """Store tokens and expiration time."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = (datetime.utcnow() + timedelta(seconds=expires_in - 60)).isoformat()
        self.updated_at = datetime.utcnow().isoformat()


class MondayOAuthService:
    """OAuth 2.0 service for Monday.com integration."""
    
    @staticmethod
    def generate_auth_url(tenant_id: str) -> str:
        """Generate OAuth authorization URL."""
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        OAUTH_STATE_STORAGE[state] = {
            "tenant_id": tenant_id,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        params = {
            "client_id": MONDAY_CLIENT_ID,
            "redirect_uri": MONDAY_REDIRECT_URI,
            "state": state,
            "scope": "boards:read,items:read:board,updates:read,webhooks:write",
        }
        
        return f"{MONDAY_AUTH_URL}?{urlencode(params)}"
    
    @staticmethod
    def exchange_code_for_token(code: str, state: str) -> Optional[TenantConfig]:
        """Exchange authorization code for access token."""
        # Verify state token
        if state not in OAUTH_STATE_STORAGE:
            raise OAuthError("Invalid state token")
        
        state_data = OAUTH_STATE_STORAGE.pop(state)
        tenant_id = state_data["tenant_id"]
        
        try:
            # Exchange code for token
            response = requests.post(
                MONDAY_TOKEN_URL,
                json={
                    "client_id": MONDAY_CLIENT_ID,
                    "client_secret": MONDAY_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": MONDAY_REDIRECT_URI,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Store tokens
            tenant = TenantConfig(tenant_id)
            tenant.set_tokens(
                access_token=data.get("access_token"),
                refresh_token=data.get("refresh_token"),
                expires_in=data.get("expires_in", 3600),
            )
            
            TENANT_STORAGE[tenant_id] = tenant
            
            print(f"✅ OAuth: Tokens stored for tenant {tenant_id}")
            return tenant
        
        except requests.RequestException as e:
            print(f"❌ OAuth: Exchange failed: {e}")
            raise OAuthError(f"Token exchange failed: {e}")
    
    @staticmethod
    def refresh_token_for_tenant(tenant_id: str) -> bool:
        """Refresh access token using refresh token."""
        tenant = TENANT_STORAGE.get(tenant_id)
        if not tenant or not tenant.refresh_token:
            return False
        
        try:
            response = requests.post(
                MONDAY_TOKEN_URL,
                json={
                    "client_id": MONDAY_CLIENT_ID,
                    "client_secret": MONDAY_CLIENT_SECRET,
                    "refresh_token": tenant.refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            response.raise_for_status()
            data = response.json()
            
            tenant.set_tokens(
                access_token=data.get("access_token"),
                refresh_token=data.get("refresh_token", tenant.refresh_token),
                expires_in=data.get("expires_in", 3600),
            )
            
            print(f"✅ OAuth: Token refreshed for tenant {tenant_id}")
            return True
        
        except requests.RequestException as e:
            print(f"❌ OAuth: Refresh failed for tenant {tenant_id}: {e}")
            return False
    
    @staticmethod
    def get_tenant(tenant_id: str) -> Optional[TenantConfig]:
        """Get tenant configuration."""
        return TENANT_STORAGE.get(tenant_id)
    
    @staticmethod
    def create_tenant(tenant_id: str, workspace_id: str = None) -> TenantConfig:
        """Create new tenant configuration."""
        tenant = TenantConfig(tenant_id, workspace_id)
        TENANT_STORAGE[tenant_id] = tenant
        return tenant
    
    @staticmethod
    def delete_tenant(tenant_id: str) -> bool:
        """Delete tenant configuration (revoke authorization)."""
        if tenant_id in TENANT_STORAGE:
            TENANT_STORAGE.pop(tenant_id)
            print(f"🔒 OAuth: Tenant {tenant_id} revoked")
            return True
        return False
    
    @staticmethod
    def list_tenants() -> Dict[str, Dict[str, Any]]:
        """List all tenant configurations (admin only)."""
        return {
            tenant_id: tenant.to_dict()
            for tenant_id, tenant in TENANT_STORAGE.items()
        }


def require_oauth_token(f):
    """Decorator to require valid OAuth token for tenant."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant_id = kwargs.get("tenant_id")
        if not tenant_id:
            return {"error": "tenant_id required"}, 400
        
        tenant = MondayOAuthService.get_tenant(tenant_id)
        if not tenant or not tenant.access_token:
            return {"error": "Not authorized. Please complete OAuth flow."}, 401
        
        # Refresh token if expired
        if tenant.is_token_expired():
            if not MondayOAuthService.refresh_token_for_tenant(tenant_id):
                return {"error": "Token refresh failed. Please re-authorize."}, 401
        
        kwargs["tenant"] = tenant
        return f(*args, **kwargs)
    
    return decorated_function
