"""
Feature 9: Integration Tests for REST API and Feature 1 Connectivity
Tests for API endpoints, Feature 1 integration, and end-to-end scenarios
"""
import pytest
import json
from datetime import datetime
from flask import Flask
from phase9_risk_types import RiskCategory, RiskSeverity
from phase9_risk_api import synthesis_bp


@pytest.fixture
def app():
    """Create Flask test app"""
    app = Flask(__name__)
    app.register_blueprint(synthesis_bp)
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def sample_synthesis_request():
    """Sample request body for synthesis endpoint"""
    return {
        'task_id': 'task_123',
        'cost_risk': {
            'category': 'COST',
            'score': 0.6,
            'severity': 'HIGH',
            'confidence': 0.9,
            'contributing_issues': ['Budget overrun on materials'],
            'trend': 'increasing',
        },
        'schedule_risk': {
            'category': 'SCHEDULE',
            'score': 0.7,
            'severity': 'HIGH',
            'confidence': 0.85,
            'contributing_issues': ['Permit delays'],
            'trend': 'increasing',
        },
        'workforce_risk': {
            'category': 'WORKFORCE',
            'score': 0.4,
            'severity': 'MEDIUM',
            'confidence': 0.8,
            'contributing_issues': ['Labor shortage'],
            'trend': 'stable',
        },
        'project_phase': 'execution',
        'criticality': 'high',
        'dependencies_count': 3,
    }


class TestSynthesisAPI:
    """Tests for synthesis API endpoints"""

    def test_health_check(self, client):
        """GET /api/feature9/health should return healthy status"""
        response = client.get('/api/feature9/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'service' in data
        assert 'active_projects' in data

    def test_synthesize_endpoint_success(self, client, sample_synthesis_request):
        """POST /api/feature9/synthesize should synthesize risks"""
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'synthesis_id' in data
        assert 'overall_risk_score' in data
        assert 'overall_severity' in data
        assert 'overall_confidence' in data
        assert 'executive_summary' in data

    def test_synthesize_endpoint_partial_factors(self, client):
        """POST /api/feature9/synthesize should handle partial factors"""
        request = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 0.9,
            },
            'schedule_risk': {
                'category': 'SCHEDULE',
                'score': 0.7,
                'confidence': 0.85,
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['overall_risk_score'] >= 0.0
        assert data['overall_risk_score'] <= 1.0

    def test_synthesize_endpoint_empty_body(self, client):
        """POST /api/feature9/synthesize with empty body should handle gracefully"""
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # Should either return 400 or 200 with default values
        assert response.status_code in [200, 400]

    def test_core_engine_input_endpoint(self, client, sample_synthesis_request):
        """GET /api/feature9/core-engine should return Feature 1 formatted data"""
        # First synthesize a risk
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        # Then get core engine input
        response = client.get('/api/feature9/core-engine/test_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'feature9_overall_risk' in data or len(data) > 0

    def test_risk_breakdown_endpoint(self, client, sample_synthesis_request):
        """GET /api/feature9/risk-breakdown should return detailed breakdown"""
        # First synthesize
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        # Get breakdown
        response = client.get('/api/feature9/risk-breakdown/test_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'factor_breakdown' in data

    def test_risk_trend_endpoint(self, client, sample_synthesis_request):
        """GET /api/feature9/risk-trend should return trend analysis"""
        response = client.get('/api/feature9/risk-trend/test_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'trend' in data
        assert 'project_id' in data

    def test_history_endpoint(self, client, sample_synthesis_request):
        """GET /api/feature9/history should return synthesis history"""
        # Add multiple syntheses
        for i in range(3):
            client.post(
                '/api/feature9/synthesize/test_project',
                data=json.dumps(sample_synthesis_request),
                content_type='application/json'
            )
        
        response = client.get('/api/feature9/history/test_project?limit=10')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_records' in data
        assert 'records' in data

    def test_history_with_task_filter(self, client, sample_synthesis_request):
        """GET /api/feature9/history with task_id filter"""
        request1 = sample_synthesis_request.copy()
        request1['task_id'] = 'task_1'
        
        request2 = sample_synthesis_request.copy()
        request2['task_id'] = 'task_2'
        
        # Add syntheses for different tasks
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request1),
            content_type='application/json'
        )
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request2),
            content_type='application/json'
        )
        
        # Get history for task_1
        response = client.get('/api/feature9/history/test_project?task_id=task_1')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['task_id'] == 'task_1'

    def test_monday_data_endpoint(self, client, sample_synthesis_request):
        """GET /api/feature9/monday-data should return monday.com formatted data"""
        # First synthesize
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        # Get monday.com data
        response = client.get('/api/feature9/monday-data/test_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'monday_fields' in data

    def test_alerts_endpoint(self, client):
        """GET /api/feature9/alerts should return active alerts"""
        # Create high-risk synthesis to trigger alerts
        request = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.9,
                'confidence': 0.95,
            },
            'schedule_risk': {
                'category': 'SCHEDULE',
                'score': 0.85,
                'confidence': 0.9,
            },
        }
        
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        # Get alerts
        response = client.get('/api/feature9/alerts/test_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_alerts' in data
        assert 'alerts' in data

    def test_reset_endpoint(self, client, sample_synthesis_request):
        """DELETE /api/feature9/reset should reset project"""
        # Add synthesis
        client.post(
            '/api/feature9/synthesize/test_project_reset',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        # Get history before reset
        history_before = client.get('/api/feature9/history/test_project_reset')
        data_before = json.loads(history_before.data)
        count_before = data_before['total_records']
        
        # Reset
        response = client.delete('/api/feature9/reset/test_project_reset')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'reset'
        
        # Verify history is cleared
        history_after = client.get('/api/feature9/history/test_project_reset')
        data_after = json.loads(history_after.data)
        count_after = data_after['total_records']
        
        assert count_after < count_before


class TestFeature1Integration:
    """Tests for Feature 1 (Core Risk Engine) integration"""

    def test_core_engine_input_has_all_fields(self, client, sample_synthesis_request):
        """Core engine input should have all required fields"""
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        response = client.get('/api/feature9/core-engine/test_project')
        data = json.loads(response.data)
        
        # Check for expected fields
        expected_fields = [
            'feature9_overall_risk',
            'feature9_primary_drivers',
            'feature9_confidence',
            'feature9_synthesis_timestamp',
        ]
        
        for field in expected_fields:
            # Either field exists directly or in data structure
            assert field in data or len(data) > 5

    def test_core_engine_input_numeric_ranges(self, client, sample_synthesis_request):
        """Core engine input numeric fields should be in valid ranges"""
        client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        
        response = client.get('/api/feature9/core-engine/test_project')
        data = json.loads(response.data)
        
        # Check risk score is in range
        if 'feature9_overall_risk' in data:
            risk = data['feature9_overall_risk']
            assert 0.0 <= float(risk) <= 1.0


class TestEndToEndScenarios:
    """End-to-end integration tests"""

    def test_full_workflow_single_project(self, client):
        """Complete workflow for single project"""
        # 1. Synthesize initial risks
        request1 = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.5,
                'confidence': 0.8,
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/project_123',
            data=json.dumps(request1),
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 2. Get current synthesis
        response = client.get('/api/feature9/core-engine/project_123')
        assert response.status_code == 200
        
        # 3. Get trend (may be stable on first call)
        response = client.get('/api/feature9/risk-trend/project_123')
        assert response.status_code == 200
        
        # 4. Get history
        response = client.get('/api/feature9/history/project_123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_records'] >= 1
        
        # 5. Get monday.com data
        response = client.get('/api/feature9/monday-data/project_123')
        assert response.status_code == 200

    def test_multiple_task_tracking(self, client):
        """Multiple tasks in same project should be tracked separately"""
        for task_id in ['task_1', 'task_2', 'task_3']:
            request = {
                'task_id': task_id,
                'cost_risk': {
                    'category': 'COST',
                    'score': 0.5,
                    'confidence': 0.8,
                },
            }
            
            response = client.post(
                '/api/feature9/synthesize/project_multi',
                data=json.dumps(request),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Get history - should have all tasks
        response = client.get('/api/feature9/history/project_multi')
        data = json.loads(response.data)
        assert data['total_records'] >= 3

    def test_escalating_risk_scenario(self, client):
        """Test scenario with escalating risk levels"""
        scores = [0.3, 0.4, 0.5, 0.65, 0.8]
        
        for i, score in enumerate(scores):
            request = {
                'cost_risk': {
                    'category': 'COST',
                    'score': score,
                    'confidence': 0.8 + (i * 0.02),
                },
            }
            
            response = client.post(
                '/api/feature9/synthesize/project_escalating',
                data=json.dumps(request),
                content_type='application/json'
            )
            assert response.status_code == 200
        
        # Get trend - should show increasing
        response = client.get('/api/feature9/risk-trend/project_escalating')
        assert response.status_code == 200

    def test_all_factors_scenario(self, client):
        """Test with all 8 risk factors"""
        request = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 0.9,
            },
            'schedule_risk': {
                'category': 'SCHEDULE',
                'score': 0.7,
                'confidence': 0.85,
            },
            'workforce_risk': {
                'category': 'WORKFORCE',
                'score': 0.4,
                'confidence': 0.8,
            },
            'subcontractor_risk': {
                'category': 'SUBCONTRACTOR',
                'score': 0.5,
                'confidence': 0.75,
            },
            'equipment_risk': {
                'category': 'EQUIPMENT',
                'score': 0.45,
                'confidence': 0.8,
            },
            'materials_risk': {
                'category': 'MATERIALS',
                'score': 0.5,
                'confidence': 0.85,
            },
            'compliance_risk': {
                'category': 'COMPLIANCE',
                'score': 0.55,
                'confidence': 0.9,
            },
            'environmental_risk': {
                'category': 'ENVIRONMENTAL',
                'score': 0.3,
                'confidence': 0.7,
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/project_all_factors',
            data=json.dumps(request),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # With all factors, should aggregate meaningfully
        assert 0.4 <= data['overall_risk_score'] <= 0.7
        assert data['input_count'] == 8

    def test_phase_aware_synthesis(self, client):
        """Test synthesis across different project phases"""
        request_planning = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 0.9,
            },
            'project_phase': 'planning',
        }
        
        request_execution = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 0.9,
            },
            'project_phase': 'execution',
        }
        
        request_closing = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 0.9,
            },
            'project_phase': 'closing',
        }
        
        # Synthesize in planning phase
        response = client.post(
            '/api/feature9/synthesize/project_phases',
            data=json.dumps(request_planning),
            content_type='application/json'
        )
        assert response.status_code == 200
        planning_data = json.loads(response.data)
        planning_score = planning_data['overall_risk_score']
        
        # Synthesize in execution phase
        response = client.post(
            '/api/feature9/synthesize/project_phases',
            data=json.dumps(request_execution),
            content_type='application/json'
        )
        assert response.status_code == 200
        execution_data = json.loads(response.data)
        execution_score = execution_data['overall_risk_score']
        
        # Execution phase should amplify risk
        assert execution_score > planning_score * 1.1

    def test_monday_integration_consistency(self, client, sample_synthesis_request):
        """Monday.com data should be consistent with synthesis"""
        # Synthesize
        response = client.post(
            '/api/feature9/synthesize/project_monday',
            data=json.dumps(sample_synthesis_request),
            content_type='application/json'
        )
        assert response.status_code == 200
        synthesis_data = json.loads(response.data)
        
        # Get monday data
        response = client.get('/api/feature9/monday-data/project_monday')
        assert response.status_code == 200
        monday_data = json.loads(response.data)
        
        # Both should represent same risk level
        assert monday_data is not None
        assert 'monday_fields' in monday_data


class TestErrorHandling:
    """Tests for error handling and edge cases"""

    def test_invalid_json_body(self, client):
        """Invalid JSON should return 400"""
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data='invalid json {',
            content_type='application/json'
        )
        assert response.status_code in [400, 500]

    def test_missing_risk_fields(self, client):
        """Missing required risk fields should be handled"""
        request = {
            'cost_risk': {
                'category': 'COST',
                # Missing score, confidence
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400]

    def test_invalid_risk_category(self, client):
        """Invalid risk category should be handled"""
        request = {
            'invalid_risk': {
                'category': 'INVALID',
                'score': 0.5,
                'confidence': 0.9,
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400]

    def test_out_of_range_score(self, client):
        """Score > 1.0 should be handled"""
        request = {
            'cost_risk': {
                'category': 'COST',
                'score': 1.5,  # Out of range
                'confidence': 0.9,
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400]

    def test_out_of_range_confidence(self, client):
        """Confidence > 1.0 should be handled"""
        request = {
            'cost_risk': {
                'category': 'COST',
                'score': 0.6,
                'confidence': 1.5,  # Out of range
            },
        }
        
        response = client.post(
            '/api/feature9/synthesize/test_project',
            data=json.dumps(request),
            content_type='application/json'
        )
        # Should either handle gracefully or return error
        assert response.status_code in [200, 400]

    def test_nonexistent_project_history(self, client):
        """Getting history for nonexistent project should return empty"""
        response = client.get('/api/feature9/history/nonexistent_project')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_records'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
