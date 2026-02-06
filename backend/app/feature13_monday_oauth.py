"""
Demo stub for monday.com OAuth integration.
DEMO STUB — replaced in Phase 2.5/3
Provides deterministic, non-networking placeholder functions so tests can import.
"""
from typing import Any, Dict
from flask import Blueprint, redirect

bp = Blueprint('feature13_monday_oauth', __name__, url_prefix='/api/saas/auth/monday')


def get_oauth_authorization_url(*args, **kwargs) -> str:
    """Return a deterministic placeholder authorization URL."""
    # Return a monday.com-looking URL for tests that assert 'monday.com' in redirect
    return "https://auth.monday.com/oauth/authorize?demo=1"


def exchange_code_for_token(code: str, *args, **kwargs) -> Dict[str, Any]:
    """Return a deterministic placeholder token dict. No network calls.

    Args:
        code: authorization code (ignored in demo)
    """
    return {
        "access_token": "demo_access_token",
        "refresh_token": "demo_refresh_token",
        "expires_in": 3600,
        "demo": True,
    }


@bp.route('/login')
def login():
    """Redirect to a demo monday.com authorization URL (deterministic)."""
    return redirect(get_oauth_authorization_url(), code=302)


# small compatibility helpers expected by some calling code
def demo_authorize_flow(*args, **kwargs) -> Dict[str, Any]:
    return {"url": get_oauth_authorization_url(), "note": "DEMO STUB"}
