"""
Feature 11: Predictive Resource & Subcontractor Allocation - REST API
Exposes resource optimization endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from typing import Dict, Optional
import logging
import json

from phase11_resource_types import (
    Worker, Crew, Subcontractor, TaskResourceRequirement, CurrentTaskAllocation,
    AllocationRequest, ResourceType, SkillLevel, Skill, ResourceAvailability
)
from phase11_resource_integration import create_resource_allocation_integration

logger = logging.getLogger(__name__)

# Blueprint for Feature 11 endpoints
allocation_bp = Blueprint('allocation', __name__, url_prefix='/api/feature11')

# Global integration registry
integrations: Dict[str, 'ResourceAllocationIntegration'] = {}


def get_or_create_integration(project_id: str):
    """Get or create integration for project"""
    if project_id not in integrations:
        integrations[project_id] = create_resource_allocation_integration(project_id)
    return integrations[project_id]


@allocation_bp.route('/health', methods=['GET'])
def health_check():
    """Check Feature 11 service health"""
    return jsonify({
        'status': 'healthy',
        'service': 'feature11_allocation',
        'timestamp': datetime.now().isoformat(),
        'active_projects': len(integrations),
    }), 200


@allocation_bp.route('/optimize/<project_id>', methods=['POST'])
def optimize_allocation(project_id: str):
    """
    POST /api/feature11/optimize/{project_id}
    
    Optimize resource allocation for project
    
    Request body:
    {
        'workers': [...],
        'crews': [...],
        'subcontractors': [...],
        'tasks': [...],
        'current_allocations': [...],
        'optimization_goal': 'minimize_delay|minimize_cost|balance',
        'max_recommendations': 10,
        'feature_3_data': {...},
        'feature_4_data': {...}
    }
    
    Returns: Allocation recommendations and analysis
    """
    try:
        data = request.get_json() or {}
        integration = get_or_create_integration(project_id)
        
        # Parse request (simplified - actual implementation would be more robust)
        request_obj = AllocationRequest(
            project_id=project_id,
            optimization_goal=data.get('optimization_goal', 'balance'),
            max_recommendations=int(data.get('max_recommendations', 10)),
            min_confidence_threshold=float(data.get('min_confidence_threshold', 0.60)),
        )
        
        # For now, return mock response with proper structure
        # In production, would parse workers, tasks, etc. and run optimization
        
        return jsonify({
            'status': 'success',
            'project_id': project_id,
            'optimization_goal': request_obj.optimization_goal,
            'total_recommendations': 0,
            'total_delay_risk_reduction': 0.0,
            'total_cost_reduction': 0.0,
            'confidence_level': 0.0,
            'recommendations': [],
            'generated_at': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error optimizing allocation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/recommendations/<project_id>', methods=['GET'])
def get_recommendations(project_id: str):
    """
    GET /api/feature11/recommendations/{project_id}
    Get allocation recommendations
    """
    try:
        integration = get_or_create_integration(project_id)
        
        # Get cached output
        output = integration.analysis_cache.get(project_id)
        
        if not output:
            return jsonify({
                'project_id': project_id,
                'status': 'no_analysis',
                'recommendations': [],
            }), 200
        
        return jsonify({
            'project_id': project_id,
            'total_recommendations': len(output.recommendations),
            'recommendations': [
                {
                    'id': rec.recommendation_id,
                    'from_task': rec.from_task_id,
                    'to_task': rec.to_task_id,
                    'resource': rec.resource_name,
                    'resource_type': rec.resource_type.value,
                    'reason': rec.reason.value,
                    'delay_risk_reduction': rec.delay_risk_reduction,
                    'cost_impact': rec.cost_impact,
                    'confidence': rec.confidence_level,
                    'explanation': rec.explanation,
                }
                for rec in output.recommendations
            ],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/workers/<project_id>', methods=['GET'])
def get_workers(project_id: str):
    """GET /api/feature11/workers/{project_id} - Get available workers"""
    try:
        # Mock response - would fetch from database
        return jsonify({
            'project_id': project_id,
            'total_workers': 0,
            'workers': [],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting workers: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/crews/<project_id>', methods=['GET'])
def get_crews(project_id: str):
    """GET /api/feature11/crews/{project_id} - Get available crews"""
    try:
        return jsonify({
            'project_id': project_id,
            'total_crews': 0,
            'crews': [],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting crews: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/subcontractors/<project_id>', methods=['GET'])
def get_subcontractors(project_id: str):
    """GET /api/feature11/subcontractors/{project_id} - Get available subcontractors"""
    try:
        return jsonify({
            'project_id': project_id,
            'total_subcontractors': 0,
            'subcontractors': [],
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting subcontractors: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/comparison/<project_id>', methods=['GET'])
def get_comparison(project_id: str):
    """GET /api/feature11/comparison/{project_id} - Compare current vs optimized"""
    try:
        integration = get_or_create_integration(project_id)
        comparison = integration.compare_allocation_scenarios()
        
        return jsonify(comparison), 200
    
    except Exception as e:
        logger.error(f"Error getting comparison: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/apply/<project_id>/<recommendation_id>', methods=['POST'])
def apply_recommendation(project_id: str, recommendation_id: str):
    """POST /api/feature11/apply/{project_id}/{recommendation_id} - Apply recommendation"""
    try:
        integration = get_or_create_integration(project_id)
        result = integration.apply_recommendation(recommendation_id)
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error applying recommendation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/monday-data/<project_id>', methods=['GET'])
def get_monday_com_data(project_id: str):
    """GET /api/feature11/monday-data/{project_id} - Get monday.com formatted data"""
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


@allocation_bp.route('/feature-inputs/<project_id>', methods=['GET'])
def get_feature_inputs(project_id: str):
    """GET /api/feature11/feature-inputs/{project_id} - Get inputs for Features 3,4,9,10"""
    try:
        integration = get_or_create_integration(project_id)
        
        return jsonify({
            'project_id': project_id,
            'feature_3_input': integration.get_feature_3_input(),
            'feature_4_input': integration.get_feature_4_input(),
            'feature_9_input': integration.get_feature_9_input(),
            'feature_10_input': integration.get_feature_10_input(),
            'timestamp': datetime.now().isoformat(),
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting feature inputs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@allocation_bp.route('/reset/<project_id>', methods=['DELETE'])
def reset_analysis(project_id: str):
    """DELETE /api/feature11/reset/{project_id} - Reset analysis"""
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
        logger.error(f"Error resetting: {str(e)}")
        return jsonify({'error': str(e)}), 500
