from functools import wraps
from flask import request, jsonify, current_app
import os
import jwt

# Try importing DB models
try:
    from backend.app.models.tenant_models import db, User, Role, Tenant
except Exception:
    db = None
    User = None
    Role = None
    Tenant = None


def _decode_session_token():
    token = request.cookies.get('saas_session')
    if not token:
        return None
    try:
        secret = os.getenv('JWT_SECRET', 'change_me')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except Exception:
        current_app.logger.exception('Invalid JWT in saas_session')
        return None


def require_role(role_name: str):
    """Decorator to require a role in the current tenant.

    Behavior:
    - If DB models are available, resolve the user by `sub` claim and check assigned roles for user's tenant.
    - Otherwise, fallback to checking an `roles` claim on the JWT.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            payload = _decode_session_token()
            if not payload:
                return jsonify({'error': 'unauthenticated'}), 401

            # If DB is available, resolve user and roles
            if db and User and Role:
                try:
                    sub = payload.get('sub')
                    # Attempt to find user by external id
                    user = User.query.filter_by(external_user_id=sub).first()
                    if not user:
                        # Maybe the JWT sub is a workspace account, allow only admins to continue
                        return jsonify({'error': 'user_not_found'}), 403
                    # Check roles
                    role_names = [r.name for r in user.roles]
                    if role_name in role_names:
                        return f(*args, **kwargs)
                    return jsonify({'error': 'forbidden'}), 403
                except Exception:
                    current_app.logger.exception('RBAC DB check failed')
                    return jsonify({'error': 'forbidden'}), 403

            # Fallback: check JWT roles claim
            roles = payload.get('roles') or []
            if role_name in roles or 'admin' in roles:
                return f(*args, **kwargs)
            return jsonify({'error': 'forbidden'}), 403

        return wrapped
    return decorator
