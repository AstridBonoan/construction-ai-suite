"""
Phase 16: API Endpoints - Schedule Dependencies & Delay Propagation

REST API endpoints for accessing schedule intelligence.
Integrates with Feature 1 (Phase 15) for project risk scoring.
"""

from flask import Blueprint, request, jsonify
from phase16_schedule_dependencies import ScheduleDependencyAnalyzer
from phase16_delay_propagation import DelayPropagationEngine
from phase16_types import (
    Task, TaskDependency, DependencyType, TaskStatus
)
import logging

logger = logging.getLogger(__name__)

schedule_bp = Blueprint('schedule', __name__, url_prefix='/api/schedule')
# Simple in-memory cache for analyzed schedules (project_id -> dict)
SCHEDULE_CACHE = {}


@schedule_bp.route('/analyze', methods=['POST'])
def analyze_schedule():
    """
    Analyze project schedule and return intelligence.
    
    Request JSON:
    {
        "project_id": "PROJ_001",
        "project_name": "Project Name",
        "tasks": [
            {
                "task_id": "task1",
                "name": "Foundation",
                "duration_days": 10,
                "complexity_factor": 1.5,
                "weather_dependency": true,
                "resource_constrained": false
            },
            ...
        ],
        "dependencies": [
            {
                "dependency_id": "dep1",
                "predecessor_task_id": "task1",
                "successor_task_id": "task2",
                "dependency_type": "finish_to_start",
                "lag_days": 1
            },
            ...
        ]
    }
    
    Response JSON:
    {
        "success": true,
        "project_id": "PROJ_001",
        "schedule_intelligence": {
            "critical_path": [...],
            "project_duration_days": 120,
            "schedule_resilience_score": 0.65,
            "integration_risk_score": 0.35,
            "recommended_buffer_days": 15,
            "task_risk_count": 5,
            ...
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        project_id = data.get('project_id', 'UNKNOWN')
        project_name = data.get('project_name', 'Unknown Project')
        tasks_data = data.get('tasks', [])
        deps_data = data.get('dependencies', [])
        
        if not tasks_data:
            return jsonify({"error": "No tasks provided"}), 400
        
        # Build schedule
        analyzer = ScheduleDependencyAnalyzer()
        
        for task_dict in tasks_data:
            task = Task(
                task_id=task_dict['task_id'],
                name=task_dict.get('name', 'Unknown'),
                duration_days=int(task_dict['duration_days']),
                complexity_factor=float(task_dict.get('complexity_factor', 1.0)),
                weather_dependency=bool(task_dict.get('weather_dependency', False)),
                resource_constrained=bool(task_dict.get('resource_constrained', False))
            )
            analyzer.add_task(task)
        
        for dep_dict in deps_data:
            dep_type_str = dep_dict.get('dependency_type', 'finish_to_start').lower()
            dep_type = DependencyType[dep_type_str.upper()] if hasattr(DependencyType, dep_type_str.upper()) else DependencyType.FINISH_TO_START
            
            dep = TaskDependency(
                dependency_id=dep_dict['dependency_id'],
                predecessor_task_id=dep_dict['predecessor_task_id'],
                successor_task_id=dep_dict['successor_task_id'],
                dependency_type=dep_type,
                lag_days=int(dep_dict.get('lag_days', 0))
            )
            analyzer.add_dependency(dep)
        
        # Analyze
        cp = analyzer.calculate_critical_path()
        
        # Calculate risk factors for all tasks
        risk_factors = {}
        for task_id in analyzer.tasks:
            risk_factors[task_id] = analyzer.calculate_risk_factors(task_id)
        
        # Generate delay scenarios
        engine = DelayPropagationEngine(analyzer)
        scenarios = engine.generate_delay_scenarios(cp.critical_path)
        
        # Create intelligence report
        intelligence = engine.create_project_intelligence(
            project_id=project_id,
            project_name=project_name,
            critical_path_analysis=cp,
            risk_factors=risk_factors,
            scenarios=scenarios
        )

        # Cache the intelligence (store as serializable dict)
        try:
            SCHEDULE_CACHE[project_id] = {
                "schedule_intelligence": intelligence.to_dict(),
                "critical_path": cp.critical_path,
                "project_duration_days": cp.project_duration_days,
                "integration_risk_score": intelligence.integration_risk_score,
            }
        except Exception:
            logger.exception("Failed to cache schedule intelligence")
        
        # Format response
        response = {
            "success": True,
            "project_id": project_id,
            "project_name": project_name,
            "schedule_intelligence": intelligence.to_dict(),
            "critical_path": cp.critical_path,
            "project_duration_days": cp.project_duration_days,
            "schedule_resilience_score": round(intelligence.schedule_resilience_score, 3),
            "integration_risk_score": round(intelligence.integration_risk_score, 3),
            "recommended_buffer_days": intelligence.recommended_buffer_days,
            "high_risk_task_count": len(intelligence.high_risk_dependencies),
            "scenarios_generated": len(scenarios)
        }
        
        logger.info(f"Schedule analyzed: {project_name} (resilience={intelligence.schedule_resilience_score:.2f})")
        
        return jsonify(response), 200
    
    except KeyError as e:
        return jsonify({"error": f"Missing required field: {str(e)}"}), 400
    except ValueError as e:
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error analyzing schedule: {e}")
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@schedule_bp.route('/critical-path/<project_id>', methods=['GET'])
def get_critical_path(project_id):
    """
    Get critical path for a cached project (placeholder for Monday.com integration).
    """
    # Return cached critical path if available
    cached = SCHEDULE_CACHE.get(project_id)
    if cached:
        return jsonify({
            "project_id": project_id,
            "critical_path": cached.get("critical_path"),
            "project_duration_days": cached.get("project_duration_days")
        }), 200

    return jsonify({
        "message": "Critical path endpoint - no cached analysis available",
        "project_id": project_id
    }), 404


@schedule_bp.route('/integration-risk/<project_id>', methods=['GET'])
def get_integration_risk(project_id):
    """
    Get schedule integration risk score for Feature 1 risk engine.
    
    Returns risk contribution to add to project's overall risk score.
    """
    cached = SCHEDULE_CACHE.get(project_id)
    if cached:
        return jsonify({
            "project_id": project_id,
            "integration_risk_score": round(cached.get("integration_risk_score", 0.0), 3)
        }), 200

    return jsonify({
        "message": "Integration risk endpoint - no cached analysis available",
        "project_id": project_id
    }), 404
