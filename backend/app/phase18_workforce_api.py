"""
Phase 18: Workforce Reliability API Endpoints

FastAPI/Flask blueprint for workforce intelligence endpoints.
Exposes /analyze, /worker/<worker_id>, /project/<project_id> endpoints.
"""

import logging
from typing import Optional, List
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# Design for Flask integration
workforce_bp = Blueprint('workforce', __name__, url_prefix='/api/workforce')


@workforce_bp.route('/analyze', methods=['POST'])
def analyze_workforce():
    """
    Analyze workforce from provided attendance data.
    
    Request JSON:
    {
        "project_id": "P001",
        "project_name": "Foundation Project",
        "workers": [
            {"worker_id": "W001", "name": "Alice", "role": "skilled_trades"}
        ],
        "teams": [
            {"team_id": "T001", "name": "Foundation Team", "members": ["W001"]}
        ],
        "attendance_records": [
            {
                "shift_date": "2025-01-01",
                "status": "present",
                "project_id": "P001",
                "task_id": "W001"
            }
        ]
    }
    """
    try:
        from phase18_workforce_types import Worker, Team, AttendanceRecord, WorkerRole, AttendanceStatus
        from phase18_workforce_analyzer import WorkforceReliabilityAnalyzer
        from phase18_workforce_integration import feed_workforce_to_core_risk_engine, create_workforce_risk_update
        
        data = request.get_json()
        
        # Initialize analyzer
        analyzer = WorkforceReliabilityAnalyzer()
        
        # Add workers
        for w_data in data.get('workers', []):
            worker = Worker(
                worker_id=w_data['worker_id'],
                name=w_data['name'],
                role=WorkerRole[w_data.get('role', 'LABORER').upper()],
                email=w_data.get('email'),
                monday_user_id=w_data.get('monday_user_id')
            )
            analyzer.add_worker(worker)
        
        # Add teams
        for t_data in data.get('teams', []):
            team = Team(
                team_id=t_data['team_id'],
                team_name=t_data.get('name', 'Unknown'),
                members=t_data.get('members', [])
            )
            analyzer.add_team(team)
        
        # Add attendance records
        for r_data in data.get('attendance_records', []):
            record = AttendanceRecord(
                shift_date=r_data['shift_date'],
                shift_id=r_data.get('shift_id', ''),
                status=AttendanceStatus[r_data.get('status', 'PRESENT').upper()],
                scheduled_start=r_data.get('scheduled_start', '08:00'),
                actual_start=r_data.get('actual_start'),
                scheduled_end=r_data.get('scheduled_end', '17:00'),
                actual_end=r_data.get('actual_end'),
                minutes_late=r_data.get('minutes_late', 0),
                project_id=r_data.get('project_id', ''),
                task_id=r_data.get('task_id', ''),
                notes=r_data.get('notes', ''),
                monday_task_id=r_data.get('monday_task_id')
            )
            analyzer.add_attendance_record(record)
        
        # Create intelligence
        project_id = data.get('project_id', 'UNKNOWN')
        project_name = data.get('project_name', 'Unknown Project')
        worker_ids = [w['worker_id'] for w in data.get('workers', [])]
        team_ids = [t['team_id'] for t in data.get('teams', [])]
        
        intelligence = analyzer.create_project_intelligence(
            project_id=project_id,
            project_name=project_name,
            worker_ids=worker_ids,
            team_ids=team_ids
        )
        
        # Feed to core risk engine
        feed_workforce_to_core_risk_engine(intelligence)
        
        # Prepare response
        response_data = {
            "project_id": intelligence.project_id,
            "project_name": intelligence.project_name,
            "workforce_risk_score": intelligence.workforce_risk_score,
            "integration_ready": intelligence.integration_ready,
            "worker_summaries": {
                wid: {
                    "worker_id": summary.worker_id,
                    "worker_name": summary.worker_name,
                    "reliability_score": summary.reliability_score,
                    "risk_level": summary.risk_level,
                    "absence_rate": summary.absence_rate,
                    "tardiness_rate": summary.tardiness_rate,
                    "explanation": summary.explanation
                }
                for wid, summary in intelligence.worker_summaries.items()
            },
            "team_summaries": {
                tid: {
                    "team_id": summary.team_id,
                    "team_name": summary.team_name,
                    "avg_reliability_score": summary.avg_reliability_score,
                    "team_risk_level": summary.team_risk_level,
                    "explanation": summary.explanation
                }
                for tid, summary in intelligence.team_summaries.items()
            },
            "project_summary": {
                "total_workers": intelligence.project_summary.total_workers,
                "avg_team_reliability": intelligence.project_summary.avg_team_reliability,
                "high_risk_workers": intelligence.project_summary.high_risk_workers,
                "total_schedule_risk_days": intelligence.project_summary.total_schedule_risk_days,
                "total_cost_impact": intelligence.project_summary.total_cost_impact,
                "key_insights": intelligence.project_summary.key_insights,
                "recommendations": intelligence.project_summary.recommendations
            } if intelligence.project_summary else None
        }
        
        logger.info(f"Workforce analysis complete for {project_name}: risk={intelligence.workforce_risk_score:.2f}")
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.exception(f"Workforce analysis error: {e}")
        return jsonify({"error": str(e), "message": "Failed to analyze workforce"}), 500


@workforce_bp.route('/worker/<worker_id>', methods=['GET'])
def get_worker_summary(worker_id: str):
    """Get summary for a specific worker (requires data in cache or DB lookup)"""
    try:
        # This endpoint would typically fetch from a database or cache
        # For now, return a 404 as this requires persistent storage
        return jsonify({
            "error": "worker_not_found",
            "message": "Worker data not found. Use /analyze endpoint to generate workforce intelligence."
        }), 404
    except Exception as e:
        logger.exception(f"Error fetching worker {worker_id}: {e}")
        return jsonify({"error": str(e)}), 500


@workforce_bp.route('/project/<project_id>', methods=['GET'])
def get_project_workforce_summary(project_id: str):
    """Get workforce summary for a project (requires data in cache or DB lookup)"""
    try:
        # This endpoint would typically fetch from a database or cache
        # For now, return a 404 as this requires persistent storage
        return jsonify({
            "error": "project_not_found",
            "message": "Project data not found. Use /analyze endpoint to generate workforce intelligence."
        }), 404
    except Exception as e:
        logger.exception(f"Error fetching project {project_id}: {e}")
        return jsonify({"error": str(e)}), 500


@workforce_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "workforce-intelligence",
        "version": "1.0.0"
    }), 200
