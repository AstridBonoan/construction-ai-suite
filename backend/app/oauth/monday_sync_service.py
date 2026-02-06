"""
Monday.com Data Sync Service

Handles two-way synchronization between Monday.com and AI Construction Suite.
Supports polling and webhook-driven updates.
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from .monday_api_client import MondayAPIClient, MondayDataMapper

# In-memory sync status (replace with database in production)
SYNC_HISTORY = {}
BOARD_MAPPINGS = {}


class SyncError(Exception):
    """Sync service error."""
    pass


class MondayDataSyncService:
    """Two-way sync between Monday.com and AI Construction Suite."""
    
    @staticmethod
    def configure_board_sync(tenant_id: str, board_id: str, project_name: str) -> Dict[str, Any]:
        """Configure sync mapping for a board."""
        mapping_key = f"{tenant_id}:{board_id}"
        
        BOARD_MAPPINGS[mapping_key] = {
            "tenant_id": tenant_id,
            "board_id": board_id,
            "monday_board_name": project_name,
            "configured_at": datetime.utcnow().isoformat(),
            "last_synced": None,
            "sync_status": "configured",
            "sync_direction": "two-way",  # one-way-import, one-way-export, two-way
        }
        
        print(f"✅ Sync: Configured board {board_id} → project {project_name}")
        return BOARD_MAPPINGS[mapping_key]
    
    @staticmethod
    def sync_board_items(tenant_id: str, board_id: str, api_client: MondayAPIClient) -> Dict[str, Any]:
        """Sync items from Monday board into Construction Suite."""
        try:
            # Fetch items from Monday.com
            items = api_client.get_board_items(board_id)
            
            # Convert to Construction Suite format
            tasks = []
            for item in items:
                task = MondayDataMapper.item_to_task(item, board_id)
                tasks.append(task)
            
            # Store sync history
            sync_key = f"{tenant_id}:{board_id}"
            SYNC_HISTORY[sync_key] = {
                "synced_at": datetime.utcnow().isoformat(),
                "items_count": len(tasks),
                "items": tasks,
                "status": "success",
            }
            
            print(f"✅ Sync: Imported {len(tasks)} items from board {board_id}")
            return {
                "status": "success",
                "items_synced": len(tasks),
                "tasks": tasks[:5],  # Return first 5 for preview
            }
        
        except Exception as e:
            print(f"❌ Sync: Import failed for board {board_id}: {e}")
            return {
                "status": "error",
                "message": str(e),
            }
    
    @staticmethod
    def push_risk_scores_to_monday(
        tenant_id: str, 
        board_id: str, 
        task_id: str,
        risk_score: float,
        delay_probability: float,
        api_client: MondayAPIClient
    ) -> bool:
        """Push AI-computed risk scores back to Monday.com columns."""
        try:
            # Map risk data to Monday columns
            risk_label = "Low" if risk_score < 0.33 else "Medium" if risk_score < 0.67 else "High"
            delay_label = f"{int(delay_probability * 100)}%"
            
            # Update columns in Monday.com (mock for demo)
            mapping = MondayDataMapper.get_risk_columns()
            for col_name, col_label in mapping.items():
                if col_name == "risk_score":
                    api_client.update_item_column(task_id, "risk", risk_label)
                elif col_name == "delay_probability":
                    api_client.update_item_column(task_id, "delay", delay_label)
            
            print(f"✅ Sync: Pushed risk scores for item {task_id}")
            return True
        
        except Exception as e:
            print(f"❌ Sync: Push failed for item {task_id}: {e}")
            return False
    
    @staticmethod
    def handle_webhook_event(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Monday.com webhook events."""
        event_type = webhook_data.get("event", {}).get("type")
        item_id = webhook_data.get("event", {}).get("item_id")
        board_id = webhook_data.get("event", {}).get("board_id")
        
        print(f"🔔 Webhook: {event_type} for item {item_id} on board {board_id}")
        
        # Trigger sync on relevant events
        if event_type in ["create_item", "change_simple_column_value", "change_status_column_value"]:
            return {
                "status": "acknowledged",
                "action": "sync_triggered",
                "item_id": item_id,
                "board_id": board_id,
            }
        
        return {
            "status": "acknowledged",
            "action": "no_action",
        }
    
    @staticmethod
    def get_sync_status(tenant_id: str, board_id: str) -> Dict[str, Any]:
        """Get sync status for a board."""
        mapping_key = f"{tenant_id}:{board_id}"
        
        status = BOARD_MAPPINGS.get(mapping_key, {})
        history = SYNC_HISTORY.get(mapping_key, {})
        
        return {
            "mapping": status,
            "last_sync": history.get("synced_at"),
            "items_synced": history.get("items_count", 0),
            "status": history.get("status", "never"),
        }
    
    @staticmethod
    def list_sync_mappings(tenant_id: str) -> List[Dict[str, Any]]:
        """List all active sync mappings for tenant."""
        return [
            mapping
            for key, mapping in BOARD_MAPPINGS.items()
            if key.startswith(f"{tenant_id}:")
        ]
    
    @staticmethod
    def disable_sync(tenant_id: str, board_id: str) -> bool:
        """Disable sync for a board."""
        mapping_key = f"{tenant_id}:{board_id}"
        if mapping_key in BOARD_MAPPINGS:
            BOARD_MAPPINGS[mapping_key]["sync_status"] = "disabled"
            print(f"🔒 Sync: Disabled sync for board {board_id}")
            return True
        return False
