"""
Feature 11: API Routes and Endpoints
Exposes resource allocation capabilities via REST API
"""
from flask import Blueprint, request, jsonify
from datetime import date
import logging

from phase11_resource_types import (
    AllocationRequest, ResourceAllocationResult,
    ResourceAllocationContext
)
from phase11_resource_integration import (
    create_resource_allocation_integration,
    analyze_project_resources,
    generate_allocation_recommendations
)

logger = logging.getLogger(__name__)

# Create blueprint
phase11_bp = Blueprint('phase11', __name__, url_prefix='/api/v1/features/feature11')


@phase11_bp.route('/projects/<project_id>/analyze', methods=['POST'])
def analyze_resources(project_id):
    """
    Analyze and optimize resources for a project
    
    Request:
    {
        "optimization_goal": "minimize_delay|minimize_cost|balance",
        "max_recommendations": 10,
        "allow_subcontractor_substitution": true
    }
    
    Response:
    {
        "project_id": "PRJ001",
        "analysis_timestamp": "2024-01-15T10:30:00",
        "resource_status": {...},
        "optimization_goal": "minimize_delay",
        "confidence_score": 0.85,
        "recommendations": [...]
    }
    """
    try:
        payload = request.json or {}
        
        # Create allocation request
        allocation_request = AllocationRequest(
            project_id=project_id,
            optimization_goal=payload.get('optimization_goal', 'balance'),
            max_recommendations=payload.get('max_recommendations', 10),
            allow_subcontractor_substitution=payload.get('allow_subcontractor_substitution', True),
        )
        
        # Get integration
        integration = create_resource_allocation_integration(project_id)
        
        # Analyze resources
        result = analyze_project_resources(integration, allocation_request)
        
        return jsonify({
            'success': True,
            'project_id': result.project_id,
            'analysis_timestamp': result.analysis_timestamp.isoformat(),
            'resource_status': result.resource_status_summary,
            'optimization_goal': result.optimization_goal,
            'confidence_score': result.confidence_score,
            'total_recommendations': len(result.recommendations),
            'recommendations': [
                {
                    'id': rec.get('id'),
                    'title': rec.get('title'),
                    'impact': rec.get('impact'),
                    'priority': rec.get('priority'),
                    'estimated_impact': rec.get('estimated_impact'),
                }
                for rec in result.recommendations[:5]  # Top 5
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error analyzing resources for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/recommendations', methods=['GET'])
def get_recommendations(project_id):
    """
    Get detailed allocation recommendations for a project
    
    Query params:
    - limit: max recommendations to return (default 10)
    - priority: filter by priority (high|medium|low)
    - type: filter by type (allocation|subcontractor|crew|skill_training|etc)
    
    Response:
    {
        "project_id": "PRJ001",
        "recommendations": [
            {
                "id": "REC-001",
                "type": "allocation",
                "title": "Allocate Worker W001 to Task TASK-001",
                "description": "...",
                "impact": "Reduces critical path by 2 days",
                "priority": "high",
                "confidence": 0.92,
                "estimated_impact": {"delay_reduction_days": 2, "cost_change": 500},
                "implementation_steps": ["...", "..."],
                "monday_com_actions": [...]
            },
            ...
        ]
    }
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        priority = request.args.get('priority', None)
        rec_type = request.args.get('type', None)
        
        # Get integration
        integration = create_resource_allocation_integration(project_id)
        
        # Generate recommendations
        recommendations = generate_allocation_recommendations(
            integration,
            project_id=project_id,
            max_recommendations=limit
        )
        
        # Filter if needed
        if priority:
            recommendations = [r for r in recommendations if r.get('priority') == priority]
        if rec_type:
            recommendations = [r for r in recommendations if r.get('type') == rec_type]
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'total_recommendations': len(recommendations),
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommendations for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/resources', methods=['GET'])
def get_project_resources(project_id):
    """
    Get all resources available for a project
    
    Response:
    {
        "project_id": "PRJ001",
        "workers": [
            {
                "worker_id": "W001",
                "name": "John Doe",
                "skills": ["carpentry:senior", "site_management:intermediate"],
                "availability": {...},
                "hourly_rate": 50,
                "reliability": 0.85
            }
        ],
        "crews": [...],
        "subcontractors": [...]
    }
    """
    try:
        integration = create_resource_allocation_integration(project_id)
        
        monday_data = integration.get_monday_com_data()
        
        workers = monday_data.get('workers', [])
        crews = monday_data.get('crews', [])
        subcontractors = monday_data.get('subcontractors', [])
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'total_workers': len(workers),
            'total_crews': len(crews),
            'total_subcontractors': len(subcontractors),
            'workers': workers[:20],  # Paginate
            'crews': crews[:10],
            'subcontractors': subcontractors[:10]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting resources for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/tasks', methods=['GET'])
def get_project_tasks(project_id):
    """
    Get all tasks needing resource allocation
    
    Response:
    {
        "project_id": "PRJ001",
        "tasks": [
            {
                "task_id": "TASK-001",
                "title": "Foundation Work",
                "required_role": "carpentry",
                "workers_needed": 3,
                "duration_days": 5,
                "start_date": "2024-02-01",
                "end_date": "2024-02-06",
                "status": "unallocated|partially_allocated|allocated|completed"
            }
        ]
    }
    """
    try:
        integration = create_resource_allocation_integration(project_id)
        
        # Get task data from Feature 4
        f4_data = integration.get_feature_4_input()
        tasks = f4_data.get('tasks', [])
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'total_tasks': len(tasks),
            'tasks': tasks
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting tasks for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/allocations', methods=['GET'])
def get_current_allocations(project_id):
    """
    Get current resource allocations for a project
    
    Response:
    {
        "project_id": "PRJ001",
        "allocations": [
            {
                "allocation_id": "ALLOC-001",
                "task_id": "TASK-001",
                "worker_id": "W001",
                "start_date": "2024-02-01",
                "end_date": "2024-02-06",
                "hours": 40,
                "status": "active|pending|completed"
            }
        ]
    }
    """
    try:
        integration = create_resource_allocation_integration(project_id)
        
        # Get Feature 10 input (current allocations)
        f10_data = integration.get_feature_10_input()
        allocations = f10_data.get('current_allocations', [])
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'total_allocations': len(allocations),
            'allocations': allocations
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting allocations for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/allocations', methods=['POST'])
def apply_allocation(project_id):
    """
    Apply an allocation recommendation
    
    Request:
    {
        "task_id": "TASK-001",
        "worker_id": "W001",
        "duration_days": 5,
        "start_date": "2024-02-01"
    }
    
    Response:
    {
        "success": true,
        "allocation_id": "ALLOC-NEW-001",
        "summary": "..."
    }
    """
    try:
        payload = request.json or {}
        
        task_id = payload.get('task_id')
        worker_id = payload.get('worker_id')
        
        if not task_id or not worker_id:
            return jsonify({
                'success': False,
                'error': 'task_id and worker_id required'
            }), 400
        
        integration = create_resource_allocation_integration(project_id)
        
        # Apply allocation
        result = integration.apply_allocation(
            task_id=task_id,
            worker_id=worker_id,
            start_date=payload.get('start_date'),
            duration_days=payload.get('duration_days')
        )
        
        return jsonify({
            'success': True,
            'allocation_id': result.get('allocation_id'),
            'summary': result.get('summary')
        }), 201
        
    except Exception as e:
        logger.error(f"Error applying allocation for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/conflicts', methods=['GET'])
def get_resource_conflicts(project_id):
    """
    Get resource conflicts and issues
    
    Response:
    {
        "project_id": "PRJ001",
        "conflicts": [
            {
                "conflict_id": "CONFLICT-001",
                "type": "overallocation|skill_mismatch|availability_gap|etc",
                "severity": "critical|high|medium|low",
                "details": "...",
                "affected_resources": ["W001", "TASK-001"],
                "suggested_resolution": "..."
            }
        ]
    }
    """
    try:
        integration = create_resource_allocation_integration(project_id)
        
        conflicts = integration.get_resource_conflicts()
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'total_conflicts': len(conflicts),
            'conflicts': conflicts
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting conflicts for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/projects/<project_id>/metrics', methods=['GET'])
def get_allocation_metrics(project_id):
    """
    Get resource allocation metrics and KPIs
    
    Response:
    {
        "project_id": "PRJ001",
        "metrics": {
            "total_workers": 15,
            "total_crew": 3,
            "average_utilization": 0.82,
            "unallocated_hours": 120,
            "estimated_delay_risk": 0.25,
            "estimated_cost_variance": 0.08,
            "critical_skills_gap": ["electrical:senior"],
            "compliance_status": "on_track|at_risk|critical"
        }
    }
    """
    try:
        integration = create_resource_allocation_integration(project_id)
        
        metrics = integration.get_allocation_metrics()
        
        return jsonify({
            'success': True,
            'project_id': project_id,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting metrics for {project_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@phase11_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Feature 11 - Resource Allocation',
        'version': '1.0.0'
    }), 200


def register_phase11_routes(app):
    """Register Phase 11 routes with Flask app"""
    app.register_blueprint(phase11_bp)
    logger.info("Phase 11 routes registered")
