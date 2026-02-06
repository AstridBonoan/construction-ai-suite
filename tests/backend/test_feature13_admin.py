import os
import jwt
from backend.app.main import app


def make_session_cookie(payload, secret='change_me'):
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token


def test_admin_endpoints_require_auth():
    client = app.test_client()
    # No cookie -> unauthenticated
    r = client.get('/api/saas/admin/tenants')
    assert r.status_code in (401, 302)


def test_admin_endpoints_with_jwt_admin():
    client = app.test_client()
    # Create JWT with admin role
    payload = {'sub': 'u-1', 'roles': ['admin'], 'account': 'ws-test'}
    token = make_session_cookie(payload)
    client.set_cookie('saas_session', token)

    # With DB not configured, endpoint should return not_configured 500
    r = client.get('/api/saas/admin/tenants')
    assert r.status_code in (200, 500)

    r2 = client.get('/api/saas/admin/installations')
    assert r2.status_code in (200, 500)


def test_revoke_requires_admin():
    client = app.test_client()
    # Non-admin JWT
    payload = {'sub': 'u-2', 'roles': ['viewer'], 'account': 'ws-test'}
    token = make_session_cookie(payload)
    client.set_cookie('saas_session', token)

    r = client.post('/api/saas/admin/revoke/1')
    assert r.status_code == 403
