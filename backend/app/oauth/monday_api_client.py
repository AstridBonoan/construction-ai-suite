"""
Monday.com API Client

Wrapper for Monday.com GraphQL API with caching and error handling.
"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

MONDAY_API_URL = "https://api.monday.com/v2"

# Demo mode - use realistic synthetic data
DEMO_MODE = os.getenv("MONDAY_DEMO_MODE", "true").lower() == "true"


class MondayAPIError(Exception):
    """Monday.com API error."""
    pass


class MondayAPIClient:
    """GraphQL client for Monday.com API."""
    
    def __init__(self, access_token: str):
        """Initialize with access token."""
        self.access_token = access_token
        self.headers = {
            "Authorization": access_token,
            "Content-Type": "application/json",
        }
    
    def query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query."""
        if DEMO_MODE:
            return self._demo_query(query, variables)
        
        try:
            response = requests.post(
                MONDAY_API_URL,
                headers=self.headers,
                json={"query": query, "variables": variables or {}},
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                raise MondayAPIError(f"GraphQL error: {data['errors']}")
            
            return data.get("data", {})
        
        except requests.RequestException as e:
            raise MondayAPIError(f"API request failed: {e}")
    
    def get_boards(self) -> List[Dict[str, Any]]:
        """Get user's boards."""
        if DEMO_MODE:
            return [
                {
                    "id": "board_123",
                    "name": "Downtown Development Project",
                    "description": "Multi-phase urban development",
                    "board_kind": "project",
                    "owner": {"id": "user_1", "name": "John Developer"},
                    "groups": [
                        {"id": "group_1", "title": "Planning & Design"},
                        {"id": "group_2", "title": "Foundation & Structure"},
                        {"id": "group_3", "title": "Finishings"},
                    ],
                },
                {
                    "id": "board_456",
                    "name": "Equipment Maintenance",
                    "description": "Equipment tracking and maintenance",
                    "board_kind": "project",
                    "owner": {"id": "user_2", "name": "Jane Manager"},
                    "groups": [
                        {"id": "group_4", "title": "Scheduled Maintenance"},
                        {"id": "group_5", "title": "Emergency Repairs"},
                    ],
                },
            ]
        
        query = """
        {
            boards(limit: 50) {
                id
                name
                description
                board_kind
                owner {
                    id
                    name
                }
                groups {
                    id
                    title
                }
            }
        }
        """
        result = self.query(query)
        return result.get("boards", [])
    
    def get_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Get items (tasks) from a board."""
        if DEMO_MODE:
            return [
                {
                    "id": "item_1",
                    "name": "Site Preparation & Clearing",
                    "group": {"id": "group_1", "title": "Planning & Design"},
                    "status": {"label": "In Progress"},
                    "date": {"date": "2026-02-15"},
                    "end_date": {"date": "2026-03-01"},
                    "budget": {"text": "45000"},
                    "assigned_to": [{"id": "user_1", "name": "John Developer"}],
                    "column_values": [
                        {"id": "col_risk", "text": "Medium"},
                        {"id": "col_delay", "text": "3 days"},
                    ],
                },
                {
                    "id": "item_2",
                    "name": "Foundation Excavation",
                    "group": {"id": "group_2", "title": "Foundation & Structure"},
                    "status": {"label": "Not Started"},
                    "date": {"date": "2026-03-02"},
                    "end_date": {"date": "2026-04-10"},
                    "budget": {"text": "125000"},
                    "assigned_to": [{"id": "user_3", "name": "Bob Engineer"}],
                    "column_values": [
                        {"id": "col_risk", "text": "High"},
                        {"id": "col_delay", "text": "0 days"},
                    ],
                },
                {
                    "id": "item_3",
                    "name": "Concrete Pour & Curing",
                    "group": {"id": "group_2", "title": "Foundation & Structure"},
                    "status": {"label": "Not Started"},
                    "date": {"date": "2026-04-11"},
                    "end_date": {"date": "2026-05-15"},
                    "budget": {"text": "98000"},
                    "assigned_to": [{"id": "user_3", "name": "Bob Engineer"}],
                    "column_values": [
                        {"id": "col_risk", "text": "Critical"},
                        {"id": "col_delay", "text": "5 days"},
                    ],
                },
            ]
        
        query = """
        query($board_id: [Int!]!) {
            boards(ids: $board_id) {
                items_page(limit: 100, query_params: {order_by: [{column_id: "created_at", direction: "desc"}]}) {
                    items {
                        id
                        name
                        group {
                            id
                            title
                        }
                        status: column_values(ids: ["status"]) {
                            label: text
                        }
                        date: column_values(ids: ["date"]) {
                            date
                        }
                        end_date: column_values(ids: ["end_date"]) {
                            date
                        }
                        budget: column_values(ids: ["budget"]) {
                            text
                        }
                        assigned_to: column_values(ids: ["person"]) {
                            id
                            name
                        }
                        column_values {
                            id
                            text
                        }
                    }
                }
            }
        }
        """
        
        result = self.query(query, {"board_id": int(board_id)})
        boards = result.get("boards", [])
        if boards:
            return boards[0].get("items_page", {}).get("items", [])
        return []
    
    def update_item_column(self, item_id: str, column_id: str, value: str) -> bool:
        """Update item column value."""
        if DEMO_MODE:
            print(f"📝 DEMO: Updated item {item_id} column {column_id} = {value}")
            return True
        
        query = """
        mutation($item_id: Int!, $column_id: String!, $value: JSON!) {
            change_column_value(item_id: $item_id, column_id: $column_id, value: $value) {
                id
            }
        }
        """
        
        result = self.query(query, {
            "item_id": int(item_id),
            "column_id": column_id,
            "value": value,
        })
        
        return "change_column_value" in result
    
    def create_webhook(self, board_id: str, event: str, url: str) -> Optional[str]:
        """Create webhook for board events."""
        if DEMO_MODE:
            print(f"🔗 DEMO: Created webhook for board {board_id} event {event}")
            return f"webhook_{board_id}_{event}"
        
        query = """
        mutation($board_id: Int!, $url: String!, $event: WebhookEventType!) {
            create_webhook(board_id: $board_id, url: $url, event: $event) {
                id
            }
        }
        """
        
        result = self.query(query, {
            "board_id": int(board_id),
            "url": url,
            "event": event,
        })
        
        webhook = result.get("create_webhook", {})
        return webhook.get("id")
    
    def _demo_query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return demo data for GraphQL queries."""
        # Simple demo mode - return cached structures
        if "boards" in query:
            return {"boards": self.get_boards()}
        return {}


class MondayDataMapper:
    """Map Monday.com data structures to AI Construction Suite models."""
    
    @staticmethod
    def board_to_project(board: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Monday.com board to project."""
        return {
            "project_id": board["id"],
            "project_name": board["name"],
            "description": board.get("description", ""),
            "owner": board.get("owner", {}).get("name", "Unknown"),
            "created_at": datetime.utcnow().isoformat(),
            "is_synced": True,
        }
    
    @staticmethod
    def item_to_task(item: Dict[str, Any], project_id: str) -> Dict[str, Any]:
        """Convert Monday.com item to task."""
        return {
            "task_id": item["id"],
            "task_name": item["name"],
            "project_id": project_id,
            "phase": item.get("group", {}).get("title", "Unknown"),
            "status": item.get("status", {}).get("label", "Not Started"),
            "start_date": item.get("date", {}).get("date"),
            "end_date": item.get("end_date", {}).get("date"),
            "budget": float(item.get("budget", {}).get("text", "0") or "0"),
            "assigned_to": [u.get("name", "Unknown") for u in item.get("assigned_to", [])],
            "synced_at": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def get_risk_columns() -> Dict[str, str]:
        """Columns that receive AI risk data from Construction Suite."""
        return {
            "risk_score": "Risk Level (AI)",
            "delay_probability": "Delay Probability (AI)",
            "critical_path": "On Critical Path (AI)",
            "schedule_impact": "Schedule Impact (AI)",
        }
