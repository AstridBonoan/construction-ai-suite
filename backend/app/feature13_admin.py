from flask import Blueprint, jsonify, request, current_app

bp = Blueprint('feature13_admin', __name__, url_prefix='/api/saas/admin')

try:
    from backend.app.models.tenant_models import db, Tenant, OAuthInstallation, User, Role
    from backend.app.models.monday_token import TokenManager
    from backend.app.rbac import require_role
except Exception:
    db = None
    Tenant = None
    OAuthInstallation = None
    User = None
    Role = None
    TokenManager = None
    # fallback decorator
    def require_role(_r):
        def dec(f):
            return f
        return dec


@bp.route('/tenants', methods=['GET'])
@require_role('admin')
def list_tenants():
    if not db or not Tenant:
        return jsonify({'error': 'not_configured'}), 500
    tenants = Tenant.query.all()
    return jsonify([{'id': t.id, 'name': t.name, 'workspace_id': t.workspace_id, 'created_at': t.created_at.isoformat()} for t in tenants])


@bp.route('/installations', methods=['GET'])
@require_role('admin')
def list_installations():
    if not db or not OAuthInstallation:
        return jsonify({'error': 'not_configured'}), 500
    installs = OAuthInstallation.query.all()
    items = []
    for i in installs:
        items.append({
            'id': i.id,
            'tenant_id': i.tenant_id,
            'provider': i.provider,
            'workspace_id': i.workspace_id,
            'expires_at': i.expires_at.isoformat() if i.expires_at else None,
            'created_at': i.created_at.isoformat()
        })
    return jsonify(items)


@bp.route('/revoke/<int:installation_id>', methods=['POST'])
@require_role('admin')
def revoke_installation(installation_id):
    if not db or not OAuthInstallation:
        return jsonify({'error': 'not_configured'}), 500
    inst = OAuthInstallation.query.get(installation_id)
    if not inst:
        return jsonify({'error': 'not_found'}), 404
    try:
        # Delete DB record
        db.session.delete(inst)
        db.session.commit()
        # Delete in-memory token if present
        if TokenManager:
            TokenManager.delete_token(inst.workspace_id)
        return jsonify({'status': 'revoked'})
    except Exception:
        current_app.logger.exception('Failed to revoke installation')
        return jsonify({'error': 'failed'}), 500
