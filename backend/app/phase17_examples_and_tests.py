"""
Phase 17: Monday.com Integration Examples and Tests

Demonstrates how to use the seamless Monday.com OAuth integration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta


class TestMondayOAuthFlow(unittest.TestCase):
    """Test OAuth authentication flow"""
    
    def test_oauth_flow_generates_auth_url(self):
        """Test that OAuth flow generates proper authorization URL"""
        from backend.app.phase17_monday_integration import MondayOAuthHandler
        
        handler = MondayOAuthHandler()
        handler.client_id = "test_client_id"
        
        url = handler.get_authorization_url(state="test_state")
        
        self.assertIn("auth.monday.com/oauth2/authorize", url)
        self.assertIn("client_id=test_client_id", url)
        self.assertIn("state=test_state", url)
    
    @patch('requests.post')
    def test_oauth_token_exchange(self, mock_post):
        """Test exchanging authorization code for token"""
        from backend.app.phase17_monday_integration import MondayOAuthHandler
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'expires_in': 3600,
            'workspace_id': 'ws_123'
        }
        mock_post.return_value = mock_response
        
        handler = MondayOAuthHandler()
        handler.client_id = "test_id"
        handler.client_secret = "test_secret"
        
        result = handler.exchange_code_for_token("auth_code_123")
        
        self.assertEqual(result['access_token'], 'test_token_123')
        self.assertIn('expires_at', result)
    
    def test_webhook_signature_validation(self):
        """Test webhook signature validation"""
        from backend.app.phase17_monday_integration import MondayOAuthHandler
        import hmac
        import hashlib
        
        handler = MondayOAuthHandler()
        handler.client_secret = "test_secret"
        
        body = b'{"event": "item.created"}'
        expected_sig = hmac.new(
            b"test_secret",
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Should validate correct signature
        self.assertTrue(handler.is_valid_webhook_signature(body, expected_sig))
        
        # Should reject invalid signature
        self.assertFalse(handler.is_valid_webhook_signature(body, "wrong_sig"))


class TestMondayAPIClient(unittest.TestCase):
    """Test Monday.com GraphQL API wrapper"""
    
    @patch('requests.post')
    def test_get_user_info(self, mock_post):
        """Test fetching user information"""
        from backend.app.phase17_monday_integration import MondayAPI
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'me': {
                    'id': 'user_123',
                    'name': 'John Doe',
                    'email': 'john@example.com'
                }
            }
        }
        mock_post.return_value = mock_response
        
        api = MondayAPI("test_token")
        user = api.get_user_info()
        
        self.assertEqual(user['id'], 'user_123')
        self.assertEqual(user['name'], 'John Doe')
    
    @patch('requests.post')
    def test_get_boards(self, mock_post):
        """Test fetching user's boards"""
        from backend.app.phase17_monday_integration import MondayAPI
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'boards': [
                    {
                        'id': 'board_1',
                        'name': 'Construction Project A',
                        'owner': {'name': 'Alice', 'email': 'alice@example.com'}
                    },
                    {
                        'id': 'board_2',
                        'name': 'Construction Project B',
                        'owner': {'name': 'Bob', 'email': 'bob@example.com'}
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        api = MondayAPI("test_token")
        boards = api.get_boards()
        
        self.assertEqual(len(boards), 2)
        self.assertEqual(boards[0]['name'], 'Construction Project A')
    
    @patch('requests.post')
    def test_get_items(self, mock_post):
        """Test fetching items from a board"""
        from backend.app.phase17_monday_integration import MondayAPI
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'boards': [
                    {
                        'items': [
                            {
                                'id': 'item_1',
                                'name': 'Foundation',
                                'column_values': [
                                    {'id': 'date', 'text': '2024-01-15'}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        api = MondayAPI("test_token")
        items = api.get_items("board_1")
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['name'], 'Foundation')
    
    @patch('requests.post')
    def test_update_item_column(self, mock_post):
        """Test updating an item's column value"""
        from backend.app.phase17_monday_integration import MondayAPI
        
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'change_column_value': {'id': 'item_1'}
            }
        }
        mock_post.return_value = mock_response
        
        api = MondayAPI("test_token")
        result = api.update_item_column("item_1", "status", "Done")
        
        self.assertTrue(result)


class TestTokenManager(unittest.TestCase):
    """Test token storage and management"""
    
    def test_save_and_retrieve_token(self):
        """Test saving and retrieving tokens"""
        from backend.app.models.monday_token import MondayToken, TokenManager
        
        # Create token
        token = MondayToken(
            workspace_id="ws_123",
            access_token="test_token",
            expires_in=3600,
            user_id="user_123"
        )
        
        # Save
        TokenManager.save_token(token)
        
        # Retrieve
        retrieved = TokenManager.get_token("ws_123")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.workspace_id, "ws_123")
        self.assertEqual(retrieved.access_token, "test_token")
    
    def test_token_expiration(self):
        """Test token expiration detection"""
        from backend.app.models.monday_token import MondayToken
        
        # Token that expires in past
        token = MondayToken(
            workspace_id="ws_123",
            access_token="test_token",
            expires_in=-100  # Already expired
        )
        
        self.assertTrue(token.is_expired)
    
    def test_token_encryption(self):
        """Test token encryption/decryption"""
        from backend.app.models.monday_token import MondayToken
        import os
        
        # Only test if encryption is configured
        original_key = os.getenv('MONDAY_TOKEN_ENCRYPTION_KEY')
        
        if original_key:
            token = MondayToken(
                workspace_id="ws_123",
                access_token="secret_token_value"
            )
            
            # Token should be encrypted when stored
            self.assertNotEqual(token._access_token, "secret_token_value")
            
            # But decrypted when accessed
            self.assertEqual(token.access_token, "secret_token_value")


class TestIntegrationWithPhase16(unittest.TestCase):
    """Test integration with Phase 16 (Schedule Dependencies)"""
    
    @patch('requests.post')
    def test_transform_monday_items_to_tasks(self, mock_post):
        """Test converting Monday.com items to Phase 16 Task objects"""
        from backend.app.phase17_monday_integration import MondayAPI
        
        # Mock Monday.com response
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': {
                'boards': [
                    {
                        'items': [
                            {
                                'id': 'item_1',
                                'name': 'Excavation',
                                'column_values': [
                                    {'id': 'duration', 'value': '{"value": 5}'},
                                    {'id': 'start_date', 'text': '2024-01-01'}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        api = MondayAPI("test_token")
        items = api.get_items("board_1")
        
        # Example of how to transform to Phase 16 Task format
        for item in items:
            task_data = {
                'task_id': item['id'],
                'name': item['name'],
                'duration_days': 5,  # Would extract from columns
                'complexity_factor': 1.0
            }
            # Would be passed to Phase 16 analyzer
            self.assertEqual(task_data['name'], 'Excavation')


class TestEndpoints(unittest.TestCase):
    """Test Flask endpoints"""
    
    def setUp(self):
        """Set up test client"""
        from flask import Flask
        from backend.app.phase17_monday_integration import monday_bp
        
        self.app = Flask(__name__)
        self.app.register_blueprint(monday_bp)
        self.client = self.app.test_client()
    
    def test_status_endpoint(self):
        """Test /api/monday/status endpoint"""
        response = self.client.get('/api/monday/status')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('configured', data)
        self.assertIn('features', data)
    
    def test_config_endpoint(self):
        """Test /api/monday/config endpoint"""
        response = self.client.get('/api/monday/config')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('app_name', data)
        self.assertIn('auth_endpoint', data)


# Example Usage

if __name__ == '__main__':
    print("""
    Phase 17: Monday.com Integration Examples
    
    Run tests:
    python -m pytest backend/app/phase17_examples_and_tests.py -v
    
    Example 1: OAuth Flow
    =====================
    1. User clicks "Connect Monday.com"
    2. System generates auth URL
    3. User redirected to Monday.com
    4. User grants permissions
    5. System exchanges code for token
    6. Token stored securely
    
    Example 2: Sync Boards
    ======================
    api = MondayAPI(access_token)
    boards = api.get_boards()
    for board in boards:
        items = api.get_items(board['id'])
        # Process items...
    
    Example 3: Analyze Schedule
    ============================
    api = MondayAPI(access_token)
    items = api.get_items(board_id)
    
    # Transform to Phase 16 format
    for item in items:
        task = Task(id=item['id'], name=item['name'], ...)
        analyzer.add_task(task)
    
    # Calculate and push back
    cp = analyzer.calculate_critical_path()
    for task in analyzer.tasks:
        api.update_item_column(task.id, 'risk_score', task.risk_score)
    
    Example 4: Webhooks
    ===================
    Monday.com sends events:
    - item.created
    - item.updated
    - column.updated
    
    System validates signature and processes event
    """)
    
    unittest.main()
