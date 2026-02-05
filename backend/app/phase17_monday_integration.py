"""
Phase 17: Monday.com Seamless Integration (App-Mode)

Zero-friction OAuth integration for Monday.com without requiring API keys.
Acts like a native Monday.com app with automatic sync capabilities.
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from typing import Optional, Dict, Any
import os
import json
import logging
from pathlib import Path
import requests
from datetime import datetime, timedelta
import hmac
import hashlib
from backend.app.ml.schedule_dependency import (
    DependencyGraph,
    Task as SDTask,
    Dependency as SDDependency,
    DependencyType as SDDependencyType,
)

logger = logging.getLogger(__name__)

monday_bp = Blueprint('monday', __name__, url_prefix='/api/monday')

# Configuration
MONDAY_API_ENDPOINT = "https://api.monday.com/v2"
MONDAY_OAUTH_AUTHORIZE_URL = "https://auth.monday.com/oauth2/authorize"
MONDAY_OAUTH_TOKEN_URL = "https://auth.monday.com/oauth2/token"

# Token storage (in production, use secure storage like KMS/vault)
TOKEN_CACHE = {}


class MondayOAuthHandler:
    """Handles OAuth flow without requiring manual API key entry"""
    
    def __init__(self):
        self.client_id = os.getenv('MONDAY_OAUTH_CLIENT_ID')
        self.client_secret = os.getenv('MONDAY_OAUTH_CLIENT_SECRET')
        self.redirect_uri = os.getenv('MONDAY_OAUTH_REDIRECT_URI', 'http://localhost:5000/api/monday/oauth/callback')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Monday.com OAuth credentials not configured. Install from Monday.com app store.")
    
    def get_authorization_url(self, state: str = None) -> str:
        """Generate OAuth authorization URL"""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state or ""
        }
        return f"{MONDAY_OAUTH_AUTHORIZE_URL}?" + "&".join(
            f"{k}={v}" for k, v in params.items()
        )
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        try:
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri
            }
            response = requests.post(MONDAY_OAUTH_TOKEN_URL, json=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            # Store with expiration
            token_data['expires_at'] = (
                datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
            ).isoformat()
            
            return token_data
        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None
    
    def is_valid_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """Validate incoming webhook from Monday.com"""
        if not self.client_secret:
            return False
        
        expected_sig = hmac.new(
            self.client_secret.encode(),
            request_body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature)


class MondayAPI:
    """Wrapper for Monday.com GraphQL API calls"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
    
    def query(self, query_str: str, variables: Dict = None) -> Dict[str, Any]:
        """Execute GraphQL query"""
        try:
            payload = {"query": query_str}
            if variables:
                payload["variables"] = variables
            
            response = requests.post(
                MONDAY_API_ENDPOINT,
                json=payload,
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            if "errors" in data:
                logger.error(f"Monday.com API error: {data['errors']}")
                return None
            
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Monday.com API call failed: {e}")
            return None
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information"""
        query = """
        {
            me {
                id
                name
                email
            }
        }
        """
        return self.query(query)
    
    def get_boards(self) -> list:
        """Get all boards accessible to user"""
        query = """
        {
            boards {
                id
                name
                owner { name email }
            }
        }
        """
        data = self.query(query)
        return data.get("boards", []) if data else []
    
    def get_board_columns(self, board_id: str) -> list:
        """Get columns for a specific board"""
        query = """
        query ($boardId: ID!) {
            boards(ids: $boardId) {
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        data = self.query(query, {"boardId": board_id})
        if data and data.get("boards"):
            return data["boards"][0].get("columns", [])
        return []
    
    def get_items(self, board_id: str) -> list:
        """Get all items (tasks) in a board"""
        query = """
        query ($boardId: ID!) {
            boards(ids: $boardId) {
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
        """
        data = self.query(query, {"boardId": board_id})
        if data and data.get("boards"):
            return data["boards"][0].get("items", [])
        return []
    
    def update_item_column(self, item_id: str, column_id: str, value: str) -> bool:
        """Update an item's column value"""
        mutation = """
        mutation ($itemId: ID!, $columnId: String!, $value: JSON!) {
            change_column_value(item_id: $itemId, column_id: $columnId, value: $value) {
                id
            }
        }
        """
        variables = {
            "itemId": item_id,
            "columnId": column_id,
            "value": json.dumps(value)
        }
        result = self.query(mutation, variables)
        return result is not None


# OAuth Routes

@monday_bp.route('/oauth/start', methods=['GET'])
def start_oauth():
    """Initiate OAuth flow (no API key needed!)"""
    handler = MondayOAuthHandler()
    if not handler.client_id:
        return jsonify({
            "error": "Monday.com app not configured",
            "message": "Install the Construction AI app from Monday.com app store"
        }), 400
    
    auth_url = handler.get_authorization_url()
    return jsonify({"authorization_url": auth_url}), 200


@monday_bp.route('/oauth/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback from Monday.com"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return jsonify({"error": "Missing authorization code"}), 400
    
    handler = MondayOAuthHandler()
    token_data = handler.exchange_code_for_token(code)
    
    if not token_data:
        return jsonify({"error": "Failed to obtain access token"}), 500
    
    # Store token securely
    workspace_id = token_data.get('workspace_id', 'default')
    TOKEN_CACHE[workspace_id] = token_data
    
    # In production, persist to secure storage
    logger.info(f"OAuth successful for workspace {workspace_id}")
    
    # Redirect to success page
    return redirect('/monday/oauth/success'), 302


@monday_bp.route('/oauth/success', methods=['GET'])
def oauth_success():
    """OAuth success page"""
    return jsonify({
        "success": True,
        "message": "Successfully connected to Monday.com!",
        "next_steps": [
            "Boards and projects will automatically sync",
            "Risk analyses will update task statuses",
            "Schedule intelligence will be visible in your board"
        ]
    }), 200


# Data Sync Routes

@monday_bp.route('/sync/boards', methods=['GET'])
def sync_boards():
    """Fetch user's Monday.com boards"""
    workspace_id = request.args.get('workspace_id', 'default')
    token_data = TOKEN_CACHE.get(workspace_id)
    
    if not token_data:
        return jsonify({"error": "Not authenticated with Monday.com"}), 401
    
    api = MondayAPI(token_data['access_token'])
    
    # Get user info
    user = api.get_user_info()
    
    # Get boards
    boards = api.get_boards()
    
    return jsonify({
        "user": user,
        "boards": boards,
        "workspace_id": workspace_id
    }), 200


@monday_bp.route('/sync/board/<board_id>', methods=['GET'])
def sync_board_data(board_id: str):
    """Sync all data from a specific board"""
    workspace_id = request.args.get('workspace_id', 'default')
    token_data = TOKEN_CACHE.get(workspace_id)
    
    if not token_data:
        return jsonify({"error": "Not authenticated with Monday.com"}), 401
    
    api = MondayAPI(token_data['access_token'])
    
    # Get board columns
    columns = api.get_board_columns(board_id)
    
    # Get items
    items = api.get_items(board_id)
    
    return jsonify({
        "board_id": board_id,
        "columns": columns,
        "items": items,
        "item_count": len(items)
    }), 200


@monday_bp.route('/sync/analyze/<board_id>', methods=['POST'])
def analyze_board_schedule(board_id: str):
    """
    Analyze board items as construction schedule and push results back to Monday.
    
    Expects: project data from Feature 2 (Phase 16)
    Returns: Updated Monday.com board with risk scores and recommendations
    """
    workspace_id = request.args.get('workspace_id', 'default')
    token_data = TOKEN_CACHE.get(workspace_id)
    
    if not token_data:
        return jsonify({"error": "Not authenticated with Monday.com"}), 401
    
    try:
        api = MondayAPI(token_data['access_token'])

        # Run schedule analysis and return structured result
        analysis = run_schedule_analysis(api, board_id)

        # Push results back to Monday columns
        push_results_to_board(api, board_id, analysis)

        return jsonify({
            "message": "Board analysis completed",
            "board_id": board_id,
            "items_processed": analysis.get("items_processed", 0),
            "analysis_summary": analysis.get("summary", {}),
        }), 200
    except Exception as e:
        logger.exception("Failed to analyze board")
        return jsonify({"error": str(e)}), 500


def run_schedule_analysis(api: MondayAPI, board_id: str) -> Dict[str, Any]:
    """Build a DependencyGraph from board items, compute critical path,
    propagate delays (deterministic), and return structured results.

    This is intentionally conservative: it does not mutate board data, but
    will call into the core risk engine via the schedule module's hook.
    """
    items = api.get_items(board_id)
    g = DependencyGraph()

    # Map Monday item ids to our graph ids
    for item in items:
        # Try to extract duration from columns; fallback to 10 days
        duration = 10
        for cv in item.get("column_values", []):
            if cv.get("id", "").lower() in ("duration", "days", "duration_days"):
                try:
                    duration = int(cv.get("text") or duration)
                except Exception:
                    duration = duration

        g.add_task(SDTask(id=item["id"], name=item.get("name", ""), duration_days=duration))

    # Attempt to infer simple dependencies from a "depends_on" column
    for item in items:
        depends = None
        for cv in item.get("column_values", []):
            if cv.get("id", "").lower() in ("depends_on", "dependency", "predecessors"):
                depends = cv.get("text")
                break

        if depends:
            # Expect comma-separated item ids in text
            preds = [p.strip() for p in (depends or "").split(",") if p.strip()]
            for p in preds:
                try:
                    g.add_dependency(SDDependency(predecessor=p, successor=item["id"], type=SDDependencyType.FINISH_TO_START))
                except KeyError:
                    # skip unknown predecessor ids
                    continue

    # Compute basic schedule and critical path
    try:
        cp = g.compute_critical_path()
    except Exception:
        # If graph incomplete or cyclic, compute earliest times only
        try:
            g.compute_earliest_times()
            cp = []
        except Exception:
            cp = []

    # For integration, propagate a nominal delay from tasks on critical path
    structured = {}
    if cp:
        # pick the first CP task as source for propagation with a 1-day simulated delay
        src = cp[0]
        structured = g.propagate_delay(task_id=src, delay_days=1)
    else:
        # No critical path; propagate from first task if exists
        if items:
            structured = g.propagate_delay(task_id=items[0]["id"], delay_days=0)
        else:
            structured = {"source_task": None, "delays": {}, "project_impact_days": 0}

    return {"items_processed": len(items), "summary": {"critical_path": cp}, "details": structured}


def push_results_to_board(api: MondayAPI, board_id: str, analysis: Dict[str, Any]) -> None:
    """Push analysis results back to Monday board columns.

    Attempts to find and update:
    - risk_score: mapped to project_impact_days as a decimal
    - predicted_delay: days
    - status_notes: explanation from core risk engine
    """
    items = api.get_items(board_id)
    columns = api.get_board_columns(board_id)

    # Map column names to ids
    col_map = {}
    for col in columns:
        title_lower = col.get("title", "").lower()
        if "risk" in title_lower or "score" in title_lower:
            col_map["risk_score"] = col["id"]
        elif "delay" in title_lower or "predicted" in title_lower:
            col_map["predicted_delay"] = col["id"]
        elif "note" in title_lower or "status" in title_lower:
            col_map["status_notes"] = col["id"]

    # Extract impact metrics from analysis
    impact_days = analysis.get("details", {}).get("project_impact_days", 0)
    delays_by_task = analysis.get("details", {}).get("delays", {})

    # Update each item with its delay estimate
    for item in items:
        task_delays = delays_by_task.get(item["id"], {})
        delay_days = task_delays.get("delay_days", 0)
        severity = task_delays.get("severity", "none")

        # Push risk_score as impact * severity_weight
        if "risk_score" in col_map:
            severity_weight = {"none": 0, "low": 0.33, "medium": 0.66, "high": 1.0}
            score = round(impact_days * severity_weight.get(severity, 0), 2)
            try:
                api.update_item_column(item["id"], col_map["risk_score"], str(score))
            except Exception:
                logger.debug(f"Could not update risk_score for item {item['id']}")

        # Push predicted_delay
        if "predicted_delay" in col_map and delay_days:
            try:
                api.update_item_column(item["id"], col_map["predicted_delay"], str(delay_days))
            except Exception:
                logger.debug(f"Could not update predicted_delay for item {item['id']}")

        # Push status_notes
        if "status_notes" in col_map:
            note = task_delays.get("explanation", "")
            if note:
                try:
                    api.update_item_column(item["id"], col_map["status_notes"], note)
                except Exception:
                    logger.debug(f"Could not update status_notes for item {item['id']}")


# Webhook Endpoint

@monday_bp.route('/webhook/events', methods=['POST'])
def handle_webhook():
    """
    Handle incoming webhooks from Monday.com
    
    Events:
    - item.created - New task in board
    - item.updated - Task modified
    - column.updated - Column value changed
    """
    signature = request.headers.get('X-Monday-Signature')
    
    handler = MondayOAuthHandler()
    if not handler.is_valid_webhook_signature(request.data, signature or ''):
        return jsonify({"error": "Invalid signature"}), 401
    
    event = request.json
    event_type = event.get('type')
    
    logger.info(f"Received Monday webhook: {event_type}")
    
    # Handle different event types
    if event_type == 'item.created':
        # New item created - could trigger analysis
        item_id = event['data']['item']['id']
        logger.info(f"New item created: {item_id}")
    
    elif event_type == 'item.updated':
        # Item updated - could trigger re-analysis
        item_id = event['data']['item']['id']
        logger.info(f"Item updated: {item_id}")
        # Trigger re-analysis for the board if authenticated
        try:
            workspace_id = request.args.get('workspace_id', 'default')
            token_data = TOKEN_CACHE.get(workspace_id)
            if token_data:
                api = MondayAPI(token_data['access_token'])
                board_id = event['data'].get('board', {}).get('id') or event['data'].get('boardId')
                if board_id:
                    run_schedule_analysis(api, board_id)
        except Exception:
            logger.exception("Failed to trigger schedule analysis from webhook")
    
    elif event_type == 'column.updated':
        # Column changed - capture new data
        item_id = event['data']['item']['id']
        logger.info(f"Column updated for item: {item_id}")
        # Column update may affect schedule; trigger re-analysis
        try:
            workspace_id = request.args.get('workspace_id', 'default')
            token_data = TOKEN_CACHE.get(workspace_id)
            if token_data:
                api = MondayAPI(token_data['access_token'])
                board_id = event['data'].get('board', {}).get('id') or event['data'].get('boardId')
                if board_id:
                    run_schedule_analysis(api, board_id)
        except Exception:
            logger.exception("Failed to trigger schedule analysis from column update webhook")
    
    return jsonify({"ok": True}), 200


# Status and Config

@monday_bp.route('/status', methods=['GET'])
def status():
    """Get Monday.com integration status"""
    handler = MondayOAuthHandler()
    
    return jsonify({
        "configured": bool(handler.client_id),
        "authenticated_workspaces": list(TOKEN_CACHE.keys()),
        "features": [
            "OAuth authentication (no API keys!)",
            "Automatic board syncing",
            "Schedule analysis integration",
            "Risk score push-back",
            "Webhook event handling"
        ]
    }), 200


@monday_bp.route('/config', methods=['GET'])
def get_config():
    """Get Monday.com configuration info"""
    handler = MondayOAuthHandler()
    
    return jsonify({
        "app_name": "Construction AI Suite",
        "oauth_configured": bool(handler.client_id),
        "redirect_uri": handler.redirect_uri,
        "auth_endpoint": url_for('monday.start_oauth', _external=True),
        "docs": "https://github.com/AstridBonoan/construction-ai-suite/blob/main/PHASE_17_MONDAY_INTEGRATION.md"
    }), 200
