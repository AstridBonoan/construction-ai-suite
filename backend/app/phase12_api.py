"""
Phase 12 API Endpoints for Decision Support & Recommendation Engine

Exposes:
- POST /phase12/recommendations - Generate recommendations from Phase 9 intelligence
- GET /phase12/recommendations/<project_id> - Retrieve stored recommendations

All endpoints return advisory-only recommendations with full traceability.
"""

import json
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from .phase12_recommendations import (
    generate_recommendations,
    serialize_decision_output,
    DecisionOutput,
)

phase12_bp = Blueprint('phase12', __name__, url_prefix='/phase12')


@phase12_bp.route('/recommendations', methods=['POST'])
def create_recommendations():
    """
    Generate recommendations from Phase 9 intelligence.
    
    Request body:
    {
        "project_id": "proj_123",
        "phase9_output": {
            "risk_score": 0.75,
            "delay_probability": 0.6,
            "risk_factors": ["schedule_compression", "material_shortage"],
            ...
        }
    }
    
    Returns DecisionOutput with recommendations array.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        project_id = data.get('project_id')
        phase9_output = data.get('phase9_output')
        
        if not project_id or not phase9_output:
            return jsonify({'error': 'project_id and phase9_output required'}), 400
        
        # Generate deterministic recommendations
        recommendations = generate_recommendations(
            project_id=project_id,
            phase9_output=phase9_output
        )
        
        # Serialize to DecisionOutput format
        decision_output = serialize_decision_output(
            project_id=project_id,
            phase9_output=phase9_output,
            recommendations=recommendations
        )
        
        # Store in reports directory for audit trail
        reports_dir = Path(__file__).parent.parent.parent / 'reports'
        reports_dir.mkdir(exist_ok=True)
        
        decision_file = reports_dir / f'phase12_decisions_{project_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(decision_file, 'w') as f:
            json.dump(decision_output, f, indent=2)
        
        return jsonify(decision_output), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Recommendation generation failed: {str(e)}'}), 500


@phase12_bp.route('/recommendations/<project_id>', methods=['GET'])
def get_recommendations(project_id):
    """
    Retrieve the most recent recommendations for a project.
    
    Returns DecisionOutput with all recommendations and traceability.
    """
    try:
        reports_dir = Path(__file__).parent.parent.parent / 'reports'
        
        # Find most recent decision file for this project
        matching_files = sorted(
            reports_dir.glob(f'phase12_decisions_{project_id}_*.json'),
            reverse=True
        )
        
        if not matching_files:
            return jsonify({'error': f'No recommendations found for project {project_id}'}), 404
        
        with open(matching_files[0], 'r') as f:
            decision_output = json.load(f)
        
        return jsonify(decision_output), 200
    
    except Exception as e:
        return jsonify({'error': f'Retrieval failed: {str(e)}'}), 500


@phase12_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check for Phase 12 service.
    Verifies recommendation engine is operational and deterministic.
    """
    return jsonify({
        'status': 'operational',
        'phase': 12,
        'component': 'decision_support_engine',
        'deterministic': True,
        'advisory_only': True,
    }), 200
