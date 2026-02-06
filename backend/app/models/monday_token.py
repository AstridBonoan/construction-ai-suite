"""
Demo stub for tenant token storage (monday_token).
DEMO STUB — replaced in Phase 2.5/3
Provides in-memory token container and manager for tests.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MondayToken:
    # Tests and codebase sometimes refer to `workspace_id` and sometimes `tenant_id`.
    # Support `workspace_id` as first-class attribute for compatibility.
    workspace_id: str
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None

    @property
    def tenant_id(self) -> str:
        return self.workspace_id


class TokenManager:
    """In-memory, deterministic token manager used only in demo/test runs."""
    _store: Dict[str, MondayToken] = {}

    @classmethod
    def save_token(cls, token_or_workspace: "MondayToken | str", token_obj: Optional[MondayToken] = None) -> bool:
        """
        Save a token. Accepts either a MondayToken instance or (workspace_id, MondayToken).
        Returns True on success.
        """
        if token_obj is None and isinstance(token_or_workspace, MondayToken):
            mt = token_or_workspace
            cls._store[mt.workspace_id] = mt
            return True
        if isinstance(token_or_workspace, str) and isinstance(token_obj, MondayToken):
            cls._store[token_or_workspace] = token_obj
            return True
        return False

    @classmethod
    def get_token(cls, workspace_id: str) -> Optional[MondayToken]:
        return cls._store.get(workspace_id)

    @classmethod
    def clear(cls) -> None:
        cls._store.clear()

    @classmethod
    def demo_token(cls, workspace_id: str) -> MondayToken:
        tok = MondayToken(workspace_id=workspace_id, access_token="demo_access_token", refresh_token="demo_refresh", expires_in=3600)
        cls.save_token(tok)
        return tok


# module-level convenience
get_token = TokenManager.get_token
save_token = TokenManager.save_token
clear_tokens = TokenManager.clear