from flask import Blueprint, current_app, redirect, request, session, url_for, jsonify
import os
import requests
import jwt
from urllib.parse import urlencode
from datetime import datetime, timedelta

# Attempt to import DB models and token manager
try:
    from backend.app.models.monday_token import TokenManager, MondayToken, MondayTokenDB
except Exception:
    TokenManager = None
    MondayToken = None
    MondayTokenDB = None

try:
    from backend.app.models.tenant_models import db, Tenant, OAuthInstallation, User
except Exception:
    db = None
    Tenant = None
    OAuthInstallation = None
    User = None

bp = Blueprint('feature13_monday_oauth', __name__, url_prefix='/api/saas')

# Environment expectations (set in server env):
# MONDAY_CLIENT_ID, MONDAY_CLIENT_SECRET, MONDAY_OAUTH_REDIRECT_URI, JWT_SECRET

@bp.route('/auth/monday/login')
def monday_login():
    client_id = os.getenv('MONDAY_CLIENT_ID')
    redirect_uri = os.getenv('MONDAY_OAUTH_REDIRECT_URI')
    scopes = 'boards:read,boards:write'  # minimal example; adapt per marketplace requirements
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': scopes,
        'state': 'saas'  # production: generate random state per session
    }
    auth_url = f"https://auth.monday.com/oauth2/authorize?{urlencode(params)}"
    return redirect(auth_url)

@bp.route('/auth/monday/callback')
def monday_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if not code:
        return jsonify({'error':'missing_code'}), 400
    token_url = 'https://auth.monday.com/oauth2/token'
    client_id = os.getenv('MONDAY_CLIENT_ID')
    client_secret = os.getenv('MONDAY_CLIENT_SECRET')
    redirect_uri = os.getenv('MONDAY_OAUTH_REDIRECT_URI')

    resp = requests.post(token_url, data={
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    })
    if resp.status_code != 200:
        return jsonify({'error':'token_exchange_failed','details':resp.text}), 502
    token_data = resp.json()
    # Token_data contains access_token, refresh_token and account info depending on monday response

    # Create a minimal JWT session for frontend (short-lived)
    jwt_secret = os.getenv('JWT_SECRET', 'change_me')
    account_id = token_data.get('account_id') or token_data.get('workspace_id')
    user_id = token_data.get('user_id') or token_data.get('account_id') or 'unknown'
    payload = {
        'sub': user_id,
        'platform': 'monday',
        'account': account_id,
    }
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')

    # Persist tokens and installation info if DB models available
    access_token = token_data.get('access_token') or token_data.get('accessToken')
    refresh_token = token_data.get('refresh_token')
    expires_in = int(token_data.get('expires_in') or token_data.get('expires') or 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    if TokenManager:
        try:
            mt = MondayToken(workspace_id=account_id, access_token=access_token, expires_in=expires_in, user_id=user_id)
            TokenManager.save_token(mt)
        except Exception:
            current_app.logger.exception('Failed to save token in TokenManager')

    if db and Tenant and OAuthInstallation:
        try:
            # Create or get tenant by workspace/account id
            tenant = Tenant.query.filter_by(workspace_id=account_id).first()
            if not tenant:
                tenant = Tenant(name=f"Tenant {account_id}", workspace_id=account_id)
                db.session.add(tenant)
                db.session.commit()

            # Create installation record
            inst = OAuthInstallation(
                tenant_id=tenant.id,
                provider='monday',
                workspace_id=account_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                scope=request.args.get('scope') or None
            )
            db.session.add(inst)
            db.session.commit()
        except Exception:
            current_app.logger.exception('Failed to persist oauth installation')

    response = redirect('/')
    response.set_cookie('saas_session', token, httponly=True, secure=True, samesite='Lax')
    return response

@bp.route('/integration/status')
def integration_status():
    # Lightweight health of integration for the logged-in tenant
    session_token = request.cookies.get('saas_session')
    if not session_token:
        return jsonify({'status':'unauthenticated'}), 401
    try:
        jwt_secret = os.getenv('JWT_SECRET', 'change_me')
        info = jwt.decode(session_token, jwt_secret, algorithms=['HS256'])
    except Exception as e:
        return jsonify({'status':'invalid_session'}), 401
    # Placeholder: check stored tokens / webhook subscriptions for this account
    return jsonify({'status':'connected','account':info.get('account')})
