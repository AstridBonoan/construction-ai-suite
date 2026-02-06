"""
Feature 9: REST API Endpoints for Multi-Factor Risk Synthesis
Exposes risk synthesis, analysis, and monday.com integration endpoints
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Optional
import logging

from phase9_risk_types import (
    RiskFactorInput,
    RiskCategory,
    AggregationMethod,
)
from phase9_risk_integration import create_feature9_integration

logger = logging.getLogger(__name__)

# Blueprint for Feature 9 endpoints
synthesis_bp = Blueprint('synthesis', __name__, url_prefix='/api/feature9')

# Global integration registry
integrations: Dict[str, 'Feature9Integration'] = {}


def get_or_create_integration(project_id: str):
    """Get or create Feature 9 integration for project"""
    if project_id not in integrations:
        integrations[project_id] = create_feature9_integration(project_id)
    return integrations[project_id]


@synthesis_bp.route('/health', methods=['GET'])
def health_check():
    """Check Feature 9 service health"""
    return jsonify({
        'status': 'healthy',
        'service': 'feature9_risk_synthesis',
        'timestamp': datetime.now().isoformat(),
        'active_projects': len(integrations),
    }), 200


@synthesis_bp.route('/synthesize/<project_id>', methods=['POST'])
def synthesize_risks(project_id: str):
    """
    POST /api/feature9/synthesize/<project_id>
    
    Synthesize multi-factor risks from Features 1-8.
    
    Request body:
    {
        'task_id': str (optional),
        'cost_risk': {
            'score': 0.0-1.0,
            'severity': 'low|medium|high|critical',
            'confidence': 0.0-1.0,
            'contributing_issues': [str],
            'trend': 'stable|increasing|decreasing'
        },
        'schedule_risk': {...},
        'workforce_risk': {...},
        'subcontractor_risk': {...},
        'equipment_risk': {...},
        'materials_risk': {...},
        'compliance_risk': {...},
        'environmental_risk': {...},
        'project_phase': 'planning|execution|closing',
        'criticality': 'low|medium|high|critical',
        'dependencies_count': int
    }
    
    Returns: Synthesized risk output with complete analysis
    """
    try:
        data = request.get_json() or {}
        integration = get_or_create_integration(project_id)

        # Extract risk factors
        def parse_risk_factor(risk_data):
            if not risk_data:
                return None
            return RiskFactorInput(
                category=RiskCategory[risk_data.get('category', '').upper()],
                score=float(risk_data.get('score', 0.0)),
                severity=risk_data.get('severity'),
                confidence=float(risk_data.get('confidence', 1.0)),
                contributing_issues=risk_data.get('contributing_issues', []),
                trend=risk_data.get('trend', 'stable'),
                timestamp=risk_data.get('timestamp', datetime.now().isoformat()),
            )

        # Build risk inputs
        cost_risk = parse_risk_factor(data.get('cost_risk'))
        schedule_risk = parse_risk_factor(data.get('schedule_risk'))
        workforce_risk = parse_risk_factor(data.get('workforce_risk'))
        subcontractor_risk = parse_risk_factor(data.get('subcontractor_risk'))
        equipment_risk = parse_risk_factor(data.get('equipment_risk'))
        materials_risk = parse_risk_factor(data.get('materials_risk'))
        compliance_risk = parse_risk_factor(data.get('compliance_risk'))
        environmental_risk = parse_risk_factor(data.get('environmental_risk'))

        # Synthesize
        synthesis = integration.register_feature_risks(
            cost_risk=cost_risk,
            schedule_risk=schedule_risk,
            workforce_risk=workforce_risk,
            subcontractor_risk=subcontractor_risk,
            equipment_risk=equipment_risk,
            materials_risk=materials_risk,
            compliance_risk=compliance_risk,
            environmental_risk=environmental_risk,
            task_id=data.get('task_id'),
            project_phase=data.get('project_phase', 'execution'),
            criticality=data.get('criticality', 'medium'),
            dependencies_count=int(data.get('dependencies_count', 0)),
        )

        return jsonify({
            'synthesis_id': synthesis.synthesis_id,
            'project_id': synthesis.project_id,
            'task_id': synthesis.task_id,
            'timestamp': synthesis.timestamp,
            'overall_risk_score': synthesis.overall_risk_score,
            'overall_severity': synthesis.overall_severity.value,
            'overall_confidence': synthesis.overall_confidence,
            'primary_risk_drivers': synthesis.primary_risk_drivers,
            'secondary_risk_drivers': synthesis.secondary_risk_drivers,
            'executive_summary': synthesis.executive_summary,
            'risk_mitigation_plan': synthesis.risk_mitigation_plan,
            'short_term_outlook': synthesis.short_term_outlook,
            'medium_term_outlook': synthesis.medium_term_outlook,
            'input_count': synthesis.input_count,
            'missing_factors': synthesis.missing_factors,
        }), 200

    except ValueError as e:
        logger.error(f"Error synthesizing risks: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error synthesizing risks: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/core-engine/<project_id>', methods=['GET'])
def get_core_engine_input(project_id: str):
    """
    GET /api/feature9/core-engine/<project_id>
    
    Get Feature 9 output formatted for Feature 1 (Core Risk Engine).
    
    Returns: Dictionary with all risk metrics and explanations
    """
    try:
        task_id = request.args.get('task_id')
        integration = get_or_create_integration(project_id)

        core_input = integration.get_core_engine_input(task_id)

        return jsonify(core_input), 200

    except Exception as e:
        logger.error(f"Error getting core engine input: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/risk-breakdown/<project_id>', methods=['GET'])
def get_risk_breakdown(project_id: str):
    """
    GET /api/feature9/risk-breakdown/<project_id>
    
    Get factor contribution breakdown and recommendations.
    
    Query parameters:
    - task_id: Optional task-level breakdown
    
    Returns: Detailed factor contributions with recommendations
    """
    try:
        task_id = request.args.get('task_id')
        integration = get_or_create_integration(project_id)

        core_data = integration.get_core_engine_input(task_id)
        
        # Extract factor data
        factors = {
            'Cost Risk': core_data.get('feature9_cost_risk'),
            'Schedule Risk': core_data.get('feature9_schedule_risk'),
            'Workforce Risk': core_data.get('feature9_workforce_risk'),
            'Subcontractor Risk': core_data.get('feature9_subcontractor_risk'),
            'Equipment Risk': core_data.get('feature9_equipment_risk'),
            'Materials Risk': core_data.get('feature9_materials_risk'),
            'Compliance Risk': core_data.get('feature9_compliance_risk'),
            'Environmental Risk': core_data.get('feature9_environmental_risk'),
        }

        # Filter out None values
        factors = {k: v for k, v in factors.items() if v is not None}

        return jsonify({
            'project_id': project_id,
            'task_id': task_id,
            'factor_breakdown': factors,
            'primary_drivers': core_data.get('feature9_primary_drivers'),
            'mitigation_plan': core_data.get('feature9_mitigation_plan'),
            'timestamp': core_data.get('feature9_synthesis_timestamp'),
        }), 200

    except Exception as e:
        logger.error(f"Error getting risk breakdown: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/risk-trend/<project_id>', methods=['GET'])
def get_risk_trend(project_id: str):
    """
    GET /api/feature9/risk-trend/<project_id>
    
    Get risk trend analysis (increasing/decreasing/stable).
    
    Query parameters:
    - task_id: Optional task-level trend
    
    Returns: Trend direction, velocity, and historical range
    """
    try:
        task_id = request.args.get('task_id')
        integration = get_or_create_integration(project_id)

        trend = integration.get_risk_trend(task_id)

        return jsonify({
            'project_id': project_id,
            'task_id': task_id,
            'trend': trend,
            'timestamp': datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error getting risk trend: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/history/<project_id>', methods=['GET'])
def get_synthesis_history(project_id: str):
    """
    GET /api/feature9/history/<project_id>
    
    Get historical synthesis records.
    
    Query parameters:
    - task_id: Filter by task
    - limit: Maximum records (default 10)
    
    Returns: List of historical synthesis records
    """
    try:
        task_id = request.args.get('task_id')
        limit = int(request.args.get('limit', 10))
        integration = get_or_create_integration(project_id)

        history = integration.get_synthesis_history(task_id, limit)

        return jsonify({
            'project_id': project_id,
            'task_id': task_id,
            'total_records': len(history),
            'records': [
                {
                    'synthesis_id': record.synthesis_id,
                    'timestamp': record.timestamp,
                    'overall_risk_score': record.overall_risk_score,
                    'overall_severity': record.overall_severity.value,
                    'executive_summary': record.executive_summary,
                }
                for record in history
            ],
        }), 200

    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/monday-data/<project_id>', methods=['GET'])
def get_monday_com_data(project_id: str):
    """
    GET /api/feature9/monday-data/<project_id>
    
    Get synthesis data formatted for monday.com integration.
    
    Query parameters:
    - task_id: Format for specific task
    
    Returns: monday.com-compatible field mappings
    """
    try:
        task_id = request.args.get('task_id')
        integration = get_or_create_integration(project_id)

        monday_data = integration.get_monday_com_data(task_id)

        return jsonify({
            'project_id': project_id,
            'task_id': task_id,
            'monday_fields': monday_data,
            'timestamp': datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error getting monday data: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/alerts/<project_id>', methods=['GET'])
def get_active_alerts(project_id: str):
    """
    GET /api/feature9/alerts/<project_id>
    
    Get all active risk alerts for project.
    
    Returns: List of triggered alerts with severity and recommendations
    """
    try:
        integration = get_or_create_integration(project_id)

        alerts = [
            {
                'alert_id': alert.alert_id,
                'task_id': alert.task_id,
                'risk_category': alert.risk_category.value,
                'alert_type': alert.alert_type,
                'severity': alert.severity.value,
                'triggered_at': alert.triggered_at,
                'message': alert.message,
                'recommended_action': alert.recommended_action,
                'escalation_level': alert.escalation_level,
            }
            for alert in integration.alert_history
        ]

        return jsonify({
            'project_id': project_id,
            'total_alerts': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500


@synthesis_bp.route('/reset/<project_id>', methods=['DELETE'])
def reset_synthesis(project_id: str):
    """
    DELETE /api/feature9/reset/<project_id>
    
    Reset synthesis data for project (for testing).
    
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
        logger.error(f"Error resetting synthesis: {str(e)}")
        return jsonify({'error': str(e)}), 500
