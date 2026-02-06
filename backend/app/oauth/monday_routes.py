"""
Monday.com Integration API Routes

Handles OAuth flow, board configuration, sync management, and webhooks.
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session
from .monday_oauth import MondayOAuthService, TenantConfig, require_oauth_token, OAuthError
from .monday_api_client import MondayAPIClient, MondayDataMapper
from .monday_sync_service import MondayDataSyncService
import os

monday_bp = Blueprint("monday", __name__, url_prefix="/monday")

# Demo mode flag
DEMO_MODE = os.getenv("MONDAY_DEMO_MODE", "true").lower() == "true"


@monday_bp.route("/oauth/init", methods=["GET"])
def oauth_init():
    """Initialize OAuth flow."""
    tenant_id = request.args.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    # Create tenant if not exists
    if not MondayOAuthService.get_tenant(tenant_id):
        MondayOAuthService.create_tenant(tenant_id)
    
    # Generate auth URL
    auth_url = MondayOAuthService.generate_auth_url(tenant_id)
    
    return jsonify({
        "status": "initialized",
        "auth_url": auth_url,
        "note": "Redirect user to this URL to authorize",
    })


@monday_bp.route("/oauth/callback", methods=["GET"])
def oauth_callback():
    """OAuth callback handler."""
    code = request.args.get("code")
    state = request.args.get("state")
    
    if not code or not state:
        return jsonify({"error": "Invalid OAuth callback"}), 400
    
    try:
        tenant = MondayOAuthService.exchange_code_for_token(code, state)
        
        # Redirect to frontend with success
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return redirect(
            f"{frontend_url}/oauth/success?tenant_id={tenant.tenant_id}&status=authenticated"
        )
    
    except OAuthError as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return redirect(f"{frontend_url}/oauth/error?message={str(e)}")


@monday_bp.route("/boards", methods=["GET"])
def list_boards():
    """Get boards for tenant (requires OAuth)."""
    tenant_id = request.args.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    tenant = MondayOAuthService.get_tenant(tenant_id)
    if not tenant or not tenant.access_token:
        # Return demo boards if not authenticated
        if DEMO_MODE:
            demo_boards = [
                {
                    "id": "board_123",
                    "name": "Downtown Development Project",
                    "description": "Multi-phase urban development",
                    "owner": "John Developer",
                    "groups": 3,
                    "items": 15,
                }
            ]
            return jsonify({"boards": demo_boards, "mode": "demo"})
        
        return jsonify({"error": "Not authorized"}), 401
    
    # Refresh token if needed
    if tenant.is_token_expired():
        MondayOAuthService.refresh_token_for_tenant(tenant_id)
    
    # Get boards from API
    api_client = MondayAPIClient(tenant.access_token)
    try:
        boards = api_client.get_boards()
        return jsonify({"boards": boards, "mode": "live"})
    except Exception as e:
        return jsonify({"error": str(e), "boards": []}), 500


@monday_bp.route("/boards/<board_id>/items", methods=["GET"])
def get_board_items(board_id):
    """Get items from a board."""
    tenant_id = request.args.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    tenant = MondayOAuthService.get_tenant(tenant_id)
    if not tenant or not tenant.access_token:
        # Return demo items if not authenticated
        if DEMO_MODE:
            demo_items = [
                {
                    "id": "item_1",
                    "name": "Site Preparation & Clearing",
                    "status": "In Progress",
                    "budget": 45000,
                    "assigned": "John Developer",
                }
            ]
            return jsonify({"items": demo_items, "mode": "demo"})
        
        return jsonify({"error": "Not authorized"}), 401
    
    # Refresh token if needed
    if tenant.is_token_expired():
        MondayOAuthService.refresh_token_for_tenant(tenant_id)
    
    # Get items from API
    api_client = MondayAPIClient(tenant.access_token)
    try:
        items = api_client.get_board_items(board_id)
        return jsonify({"items": items, "count": len(items), "mode": "live"})
    except Exception as e:
        return jsonify({"error": str(e), "items": []}), 500


@monday_bp.route("/sync/configure", methods=["POST"])
def configure_sync():
    """Configure sync for a board."""
    data = request.get_json()
    tenant_id = data.get("tenant_id")
    board_id = data.get("board_id")
    project_name = data.get("project_name")
    
    if not all([tenant_id, board_id, project_name]):
        return jsonify({"error": "Missing required fields"}), 400
    
    tenant = MondayOAuthService.get_tenant(tenant_id)
    if not tenant:
        return jsonify({"error": "Tenant not found"}), 404
    
    # Configure sync mapping
    mapping = MondayDataSyncService.configure_board_sync(tenant_id, board_id, project_name)
    
    return jsonify({
        "status": "configured",
        "mapping": mapping,
    })


@monday_bp.route("/sync/start", methods=["POST"])
def start_sync():
    """Start syncing items from Monday.com."""
    data = request.get_json()
    tenant_id = data.get("tenant_id")
    board_id = data.get("board_id")
    
    if not tenant_id or not board_id:
        return jsonify({"error": "Missing required fields"}), 400
    
    tenant = MondayOAuthService.get_tenant(tenant_id)
    if not tenant or not tenant.access_token:
        if DEMO_MODE:
            # Return demo sync result
            return jsonify({
                "status": "success",
                "items_synced": 3,
                "mode": "demo",
                "tasks": [
                    {"id": "1", "name": "Site Prep", "status": "In Progress"},
                    {"id": "2", "name": "Foundation", "status": "Not Started"},
                    {"id": "3", "name": "Concrete", "status": "Not Started"},
                ]
            })
        
        return jsonify({"error": "Not authorized"}), 401
    
    # Sync items
    api_client = MondayAPIClient(tenant.access_token)
    result = MondayDataSyncService.sync_board_items(tenant_id, board_id, api_client)
    
    return jsonify(result)


@monday_bp.route("/sync/status", methods=["GET"])
def get_sync_status():
    """Get sync status for a board."""
    tenant_id = request.args.get("tenant_id")
    board_id = request.args.get("board_id")
    
    if not tenant_id or not board_id:
        return jsonify({"error": "Missing required fields"}), 400
    
    status = MondayDataSyncService.get_sync_status(tenant_id, board_id)
    return jsonify(status)


@monday_bp.route("/sync/mappings", methods=["GET"])
def list_sync_mappings():
    """List active sync mappings for tenant."""
    tenant_id = request.args.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    mappings = MondayDataSyncService.list_sync_mappings(tenant_id)
    return jsonify({"mappings": mappings})


@monday_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    """Handle incoming Monday.com webhooks."""
    webhook_data = request.get_json()
    
    # Verify webhook signature (implement in production)
    # signature = request.headers.get("X-Monday-Signature")
    
    result = MondayDataSyncService.handle_webhook_event(webhook_data)
    return jsonify(result), 200


@monday_bp.route("/tenant/status", methods=["GET"])
def get_tenant_status():
    """Get tenant authentication and sync status."""
    tenant_id = request.args.get("tenant_id")
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    tenant = MondayOAuthService.get_tenant(tenant_id)
    if not tenant:
        return jsonify({"status": "not_configured"}), 404
    
    return jsonify({
        "tenant_id": tenant_id,
        "authenticated": tenant.access_token is not None,
        "sync_enabled": tenant.sync_enabled,
        "token_expired": tenant.is_token_expired(),
        "created_at": tenant.created_at,
        "config": tenant.to_dict(),
        "mappings": MondayDataSyncService.list_sync_mappings(tenant_id),
    })


@monday_bp.route("/tenant/revoke", methods=["POST"])
def revoke_tenant():
    """Revoke authorization for a tenant."""
    data = request.get_json()
    tenant_id = data.get("tenant_id")
    
    if not tenant_id:
        return jsonify({"error": "tenant_id required"}), 400
    
    MondayOAuthService.delete_tenant(tenant_id)
    
    return jsonify({
        "status": "revoked",
        "message": "Authorization revoked. Please reinstall the app.",
    })


@monday_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "monday.com integration",
        "demo_mode": DEMO_MODE,
        "version": "1.0",
    })
