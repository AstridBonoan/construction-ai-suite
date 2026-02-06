"""
Feature 10: REST API Endpoints
Exposes recommendations and what-if scenario analysis
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Optional
import logging

from phase10_recommendation_types import (
    RecommendationContext,
    RecommendationRequest,
    ScenarioRequest,
)
from phase10_recommendation_integration import create_feature10_integration

logger = logging.getLogger(__name__)

# Blueprint for Feature 10 endpoints
recommendations_bp = Blueprint('recommendations', __name__, url_prefix='/api/feature10')

# Global integration registry
integrations: Dict[str, 'Feature10Integration'] = {}


def get_or_create_integration(project_id: str):
    """Get or create Feature 10 integration for project"""
    if project_id not in integrations:
        integrations[project_id] = create_feature10_integration(project_id)
    return integrations[project_id]


@recommendations_bp.route('/health', methods=['GET'])
def health_check():
    """Check Feature 10 service health"""
    return jsonify({
        'status': 'healthy',
        'service': 'feature10_recommendations',
        'timestamp': datetime.now().isoformat(),
        'active_projects': len(integrations),
    }), 200


@recommendations_bp.route('/analyze/<project_id>', methods=['POST'])
def analyze_project(project_id: str):
    """
    POST /api/feature10/analyze/<project_id>
    
    Analyze project and generate recommendations + scenarios
    
    Request body:
    {
        'task_id': str (optional),
        'current_overall_risk': 0.0-1.0,
        'current_total_cost': float,
        'current_duration_days': int,
        'cost_risk': 0.0-1.0,
        'schedule_risk': 0.0-1.0,
        'workforce_risk': 0.0-1.0,
        ... (other risks),
        'project_phase': 'planning|execution|closing',
        'days_into_project': int,
        'days_remaining': int,
        'percent_complete': 0.0-1.0,
        'budget_headroom_available': float,
        'schedule_headroom_available_days': int,
        'risk_trend': 'increasing|stable|decreasing',
        'cost_variance': float,
        'schedule_variance': float,
        'similar_projects_count': int,
        'success_rate_percent': float,
        'recommendation_request': {... optional},
        'scenario_request': {... optional}
    }
    
    Returns: Analysis with recommendations and scenarios
    """
    try:
        data = request.get_json() or {}
        integration = get_or_create_integration(project_id)
        
        # Build context
        context = RecommendationContext(
            project_id=project_id,
            task_id=data.get('task_id'),
            current_overall_risk=float(data.get('current_overall_risk', 0.5)),
            current_total_cost=float(data.get('current_total_cost', 1000000)),
            current_duration_days=int(data.get('current_duration_days', 180)),
            cost_risk=float(data.get('cost_risk', 0.5)),
            schedule_risk=float(data.get('schedule_risk', 0.5)),
            workforce_risk=float(data.get('workforce_risk', 0.4)),
            subcontractor_risk=float(data.get('subcontractor_risk', 0.4)),
            equipment_risk=float(data.get('equipment_risk', 0.3)),
            materials_risk=float(data.get('materials_risk', 0.3)),
            compliance_risk=float(data.get('compliance_risk', 0.3)),
            environmental_risk=float(data.get('environmental_risk', 0.2)),
            project_phase=data.get('project_phase', 'execution'),
            days_into_project=int(data.get('days_into_project', 60)),
            days_remaining=int(data.get('days_remaining', 120)),
            percent_complete=float(data.get('percent_complete', 0.33)),
            budget_headroom_available=float(data.get('budget_headroom_available', 100000)),
            schedule_headroom_available_days=int(data.get('schedule_headroom_available_days', 14)),
            resource_availability=data.get('resource_availability', {}),
            risk_trend=data.get('risk_trend', 'stable'),
            cost_variance=float(data.get('cost_variance', 0.05)),
            schedule_variance=float(data.get('schedule_variance', 0.0)),
            similar_projects_count=int(data.get('similar_projects_count', 5)),
            success_rate_percent=float(data.get('success_rate_percent', 0.75)),
        )
        
        # Get optional requests
        rec_req = data.get('recommendation_request')
        scenario_req = data.get('scenario_request')
        
        # Analyze
        output = integration.analyze_project(context, rec_req, scenario_req)
        
        return jsonify({
            'project_id': output.project_id,
            'task_id': output.task_id,
            'total_recommendations': len(output.recommendations),
            'total_scenarios': len(output.scenarios) if output.scenarios else 0,
            'top_recommendation': {
                'title': output.top_recommendation.title,
                'type': output.top_recommendation.recommendation_type.value,
                'severity': output.top_recommendation.severity.value,
                'risk_delta': output.top_recommendation.impact.risk_impact.overall_risk_delta,
                'cost_delta': output.top_recommendation.impact.cost_impact.total_cost_delta,
                'schedule_delta': output.top_recommendation.impact.schedule_impact.duration_delta_days,
            } if output.top_recommendation else None,
            'recommended_scenario': {
                'name': output.recommended_scenario.name,
                'type': output.recommended_scenario.scenario_type.value,
                'risk_projection': output.recommended_scenario.estimated_risk_score,
                'cost_projection': output.recommended_scenario.estimated_total_cost,
                'schedule_projection': output.recommended_scenario.estimated_completion_days,
            } if output.recommended_scenario else None,
            'cost_reduction_potential': output.total_cost_reduction_potential,
            'risk_reduction_potential': output.total_risk_reduction_potential,
            'schedule_improvement': output.total_schedule_improvement,
            'confidence_level': output.confidence_level,
            'generated_at': output.generated_at,
        }), 200
    
    except Exception as e:
        logger.error(f"Error analyzing project: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/recommendations/<project_id>', methods=['GET'])
def get_recommendations(project_id: str):
    """
    GET /api/feature10/recommendations/<project_id>
    
    Get all recommendations for project
    
    Query parameters:
    - task_id: Filter by task
    - limit: Maximum records (default 10)
    
    Returns: List of recommendations with details
    """
    try:
        limit = int(request.args.get('limit', 10))
        task_id = request.args.get('task_id')
        integration = get_or_create_integration(project_id)
        
        # Get recommendations
        recs = integration.recommendation_engine.get_top_recommendations(project_id, limit)
        
        return jsonify({
            'project_id': project_id,
            'task_id': task_id,
            'total_recommendations': len(recs),
            'recommendations': [
                {
                    'id': r.recommendation_id,
                    'title': r.title,
                    'type': r.recommendation_type.value,
                    'severity': r.severity.value,
                    'description': r.description,
                    'risk_impact': r.impact.risk_impact.overall_risk_delta,
                    'cost_impact': r.impact.cost_impact.total_cost_delta,
                    'schedule_impact': r.impact.schedule_impact.duration_delta_days,
                    'confidence': r.confidence_level,
                    'reasoning': r.reasoning,
                }
                for r in recs
            ],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/scenarios/<project_id>', methods=['GET'])
def get_scenarios(project_id: str):
    """
    GET /api/feature10/scenarios/<project_id>
    
    Get all scenarios for project
    
    Returns: List of scenarios with comparison
    """
    try:
        integration = get_or_create_integration(project_id)
        
        scenarios = integration.scenario_simulator.scenarios_history.get(project_id, [])
        
        return jsonify({
            'project_id': project_id,
            'total_scenarios': len(scenarios),
            'scenarios': [
                {
                    'id': s.scenario_id,
                    'name': s.name,
                    'type': s.scenario_type.value,
                    'description': s.description,
                    'risk_projection': s.estimated_risk_score,
                    'cost_projection': s.estimated_total_cost,
                    'schedule_projection': s.estimated_completion_days,
                    'viability_score': s.viability_score,
                    'confidence': s.confidence_level,
                    'recommended': s.recommended,
                }
                for s in scenarios
            ],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting scenarios: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/scenario-comparison/<project_id>', methods=['GET'])
def get_scenario_comparison(project_id: str):
    """
    GET /api/feature10/scenario-comparison/<project_id>
    
    Get scenario comparison and rankings
    
    Returns: Comparison matrix with best/worst scenarios
    """
    try:
        integration = get_or_create_integration(project_id)
        
        scenarios = integration.scenario_simulator.scenarios_history.get(project_id, [])
        if not scenarios:
            return jsonify({'error': 'No scenarios available'}), 400
        
        # Find bests
        best_risk = min(scenarios, key=lambda s: s.estimated_risk_score)
        best_cost = min(scenarios, key=lambda s: s.estimated_total_cost)
        best_schedule = min(scenarios, key=lambda s: s.estimated_completion_days)
        
        return jsonify({
            'project_id': project_id,
            'total_scenarios': len(scenarios),
            'best_for_risk': {
                'scenario_id': best_risk.scenario_id,
                'name': best_risk.name,
                'risk_score': best_risk.estimated_risk_score,
            },
            'best_for_cost': {
                'scenario_id': best_cost.scenario_id,
                'name': best_cost.name,
                'cost': best_cost.estimated_total_cost,
            },
            'best_for_schedule': {
                'scenario_id': best_schedule.scenario_id,
                'name': best_schedule.name,
                'duration_days': best_schedule.estimated_completion_days,
            },
            'scenario_details': [
                {
                    'id': s.scenario_id,
                    'name': s.name,
                    'type': s.scenario_type.value,
                    'risk': s.estimated_risk_score,
                    'cost': s.estimated_total_cost,
                    'schedule': s.estimated_completion_days,
                    'viability': s.viability_score,
                }
                for s in scenarios
            ],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting scenario comparison: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/apply-recommendation/<project_id>/<recommendation_id>', methods=['POST'])
def apply_recommendation(project_id: str, recommendation_id: str):
    """
    POST /api/feature10/apply-recommendation/<project_id>/<recommendation_id>
    
    Apply a recommendation to the project
    
    Returns: Confirmation and updated projections
    """
    try:
        integration = get_or_create_integration(project_id)
        result = integration.apply_recommendation(recommendation_id)
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error applying recommendation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/apply-scenario/<project_id>/<scenario_id>', methods=['POST'])
def apply_scenario(project_id: str, scenario_id: str):
    """
    POST /api/feature10/apply-scenario/<project_id>/<scenario_id>
    
    Apply a scenario to the project
    
    Returns: Confirmation and scenario details
    """
    try:
        integration = get_or_create_integration(project_id)
        result = integration.apply_scenario(scenario_id)
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error applying scenario: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/monday-data/<project_id>', methods=['GET'])
def get_monday_com_data(project_id: str):
    """
    GET /api/feature10/monday-data/<project_id>
    
    Get Feature 10 data formatted for monday.com integration
    
    Returns: monday.com-compatible field mappings
    """
    try:
        integration = get_or_create_integration(project_id)
        monday_data = integration.get_monday_com_data()
        
        return jsonify({
            'project_id': project_id,
            'monday_fields': monday_data.get('monday_fields', {}),
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting monday data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/feature1-input/<project_id>', methods=['GET'])
def get_feature1_input(project_id: str):
    """
    GET /api/feature10/feature1-input/<project_id>
    
    Get Feature 10 output formatted for Feature 1 (Core Risk Engine)
    
    Returns: Feature 1-compatible risk input
    """
    try:
        integration = get_or_create_integration(project_id)
        feature1_input = integration.get_feature1_input()
        
        return jsonify({
            'project_id': project_id,
            'feature10_input': feature1_input,
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting Feature 1 input: {str(e)}")
        return jsonify({'error': str(e)}), 500


@recommendations_bp.route('/reset/<project_id>', methods=['DELETE'])
def reset_analysis(project_id: str):
    """
    DELETE /api/feature10/reset/<project_id>
    
    Reset all analysis for project (for testing)
    
    Returns: Confirmation of reset
    """
    try:
        if project_id in integrations:
            integrations[project_id].reset_project()
            del integrations[project_id]
        
        return jsonify({
            'status': 'reset',
            'project_id': project_id,
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error resetting analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500
