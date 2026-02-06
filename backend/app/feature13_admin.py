"""
Demo stub admin blueprint for Feature 13 admin endpoints.
DEMO STUB — replaced in Phase 2.5/3
Provides minimal routes for `/api/saas/admin/*` used by tests.
"""
from flask import Blueprint, request, jsonify, redirect
import jwt

bp = Blueprint('feature13_admin', __name__, url_prefix='/api/saas/admin')


def _get_session_payload():
    token = request.cookies.get('saas_session')
    if not token:
        return None
    try:
        # DEMO: do not verify signature; tests construct tokens deterministically
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception:
        return None


@bp.route('/tenants', methods=['GET'])
def tenants():
    payload = _get_session_payload()
    if payload is None:
        # unauthenticated - redirect to login (tests accept 401 or 302)
        return redirect('/api/saas/auth/monday/login')
    roles = payload.get('roles', []) if isinstance(payload, dict) else []
    if 'admin' not in roles:
        return (jsonify({'error': 'forbidden'}), 403)
    # DEMO: return empty list (no DB)
    return (jsonify([]), 200)


@bp.route('/installations', methods=['GET'])
def installations():
    payload = _get_session_payload()
    if payload is None:
        return redirect('/api/saas/auth/monday/login')
    roles = payload.get('roles', []) if isinstance(payload, dict) else []
    if 'admin' not in roles:
        return (jsonify({'error': 'forbidden'}), 403)
    return (jsonify([]), 200)


@bp.route('/revoke/<id>', methods=['POST'])
def revoke(id):
    payload = _get_session_payload()
    if payload is None:
        return redirect('/api/saas/auth/monday/login')
    roles = payload.get('roles', []) if isinstance(payload, dict) else []
    if 'admin' not in roles:
        return (jsonify({'error': 'forbidden'}), 403)
    # DEMO: pretend revoke succeeded
    return (jsonify({'revoked': id}), 200)
