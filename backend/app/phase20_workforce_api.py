"""Phase 20 - Workforce Reliability API Endpoints

REST API for accessing workforce attendance analysis, reliability scores, and
schedule/cost impact estimates.

Endpoints:
- POST /phase20/analyze - Analyze workforce for a project
- GET /phase20/worker/<worker_id> - Get individual worker reliability
- GET /phase20/project/<project_id> - Get project-level workforce intelligence
"""

from flask import Blueprint, request, jsonify, make_response
import json
from datetime import datetime, timedelta
import random

from phase20_workforce_types import (
    AttendanceRecord,
    WorkerReliabilityScore,
    ProjectWorkforceIntelligence,
    workforce_to_dict,
)
from phase20_workforce_analyzer import WorkforceReliabilityAnalyzer

workforce_bp = Blueprint("phase20_workforce", __name__, url_prefix="/phase20")


def generate_demo_attendance(worker_id: str, days: int = 90) -> list[AttendanceRecord]:
    """Generate synthetic attendance data for demo mode.
    
    Args:
        worker_id: Worker identifier
        days: Number of days to generate
    
    Returns:
        List of attendance records
    """
    records = []
    base_date = datetime.now() - timedelta(days=days)
    
    # Deterministic seed per worker
    random.seed(hash(worker_id) % (2**31))
    
    for i in range(days):
        date = base_date + timedelta(days=i)
        
        # Weekends off (skip Saturday/Sunday for construction)
        if date.weekday() >= 5:
            continue
        
        # Stochastic event
        rand = random.random()
        if rand < 0.85:
            event = 'present'
            hours = 8.0
        elif rand < 0.92:
            event = 'late'
            hours = 7.5
        elif rand < 0.96:
            event = 'absent'
            hours = None
        elif rand < 0.98:
            event = 'early_departure'
            hours = 6.0
        else:
            event = 'inspection_miss'
            hours = None
        
        record = AttendanceRecord(
            worker_id=worker_id,
            worker_name=f"Worker-{worker_id}",
            date=date.isoformat(),
            event_type=event,
            hours_worked=hours,
            minutes_late=15 if event == 'late' else None,
            reason_code='unknown',
            notes=None,
        )
        records.append(record)
    
    return records


@workforce_bp.route("/analyze", methods=["POST", "OPTIONS"])
def analyze_workforce():
    """Analyze workforce reliability for a project.
    
    Request body (JSON):
    {
        "project_id": "PROJ_001",
        "workers": [
            {
                "worker_id": "W001",
                "worker_name": "John Doe",
                "role": "foreman",
                "attendance_records": [...]  // Optional; if missing, demo data generated
            },
            ...
        ]
    }
    
    Response (200 OK):
    {
        "status": "success",
        "project_id": "PROJ_001",
        "workforce_intelligence": {...},
        "worker_scores": [...],
        "impact_factors": {...}
    }
    """
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid JSON payload"}), 400
    
    project_id = payload.get("project_id", "UNKNOWN_PROJECT")
    workers_input = payload.get("workers", [])
    
    analyzer = WorkforceReliabilityAnalyzer(lookback_days=90)
    
    # Process each worker
    worker_scores = []
    for worker_input in workers_input:
        worker_id = worker_input.get("worker_id", "")
        worker_name = worker_input.get("worker_name", f"Worker-{worker_id}")
        role = worker_input.get("role", "laborer")
        
        # Get or generate attendance records
        attendance_input = worker_input.get("attendance_records")
        if attendance_input:
            # Parse from JSON
            records = [
                AttendanceRecord(**rec) if isinstance(rec, dict) else rec
                for rec in attendance_input
            ]
        else:
            # Generate demo data
            records = generate_demo_attendance(worker_id, days=90)
        
        # Calculate reliability
        score = analyzer.calculate_worker_reliability(
            worker_id=worker_id,
            worker_name=worker_name,
            role=role,
            attendance_records=records,
        )
        worker_scores.append(score)
    
    # Estimate impact
    workers_by_role = {}
    for score in worker_scores:
        workers_by_role[score.role] = workers_by_role.get(score.role, 0) + 1
    
    impact_factors = analyzer.estimate_schedule_impact(
        worker_scores=worker_scores,
        project_workers_by_role=workers_by_role,
    )
    impact_factors.project_id = project_id
    
    # Synthesize project intelligence
    intelligence = analyzer.project_workforce_intelligence(
        project_id=project_id,
        worker_scores=worker_scores,
        impact_factors=impact_factors,
    )
    intelligence.workers_by_role = workers_by_role
    
    # Build response
    response = {
        "status": "success",
        "project_id": project_id,
        "workforce_intelligence": workforce_to_dict(intelligence),
        "worker_scores": [workforce_to_dict(s) for s in worker_scores],
        "impact_factors": workforce_to_dict(impact_factors),
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200


@workforce_bp.route("/worker/<worker_id>", methods=["GET", "OPTIONS"])
def get_worker_reliability(worker_id: str):
    """Get reliability score for a specific worker (demo mode).
    
    Response (200 OK):
    {
        "status": "success",
        "worker_score": {...}
    }
    """
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    # Demo: generate synthetic data for this worker
    records = generate_demo_attendance(worker_id, days=90)
    analyzer = WorkforceReliabilityAnalyzer()
    
    score = analyzer.calculate_worker_reliability(
        worker_id=worker_id,
        worker_name=f"Worker-{worker_id}",
        role="laborer",
        attendance_records=records,
    )
    
    response = {
        "status": "success",
        "worker_score": workforce_to_dict(score),
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200


@workforce_bp.route("/project/<project_id>", methods=["GET", "OPTIONS"])
def get_project_workforce_intelligence(project_id: str):
    """Get project-level workforce intelligence (demo mode).
    
    Generates synthetic workforce data for the project and returns analysis.
    
    Response (200 OK):
    {
        "status": "success",
        "workforce_intelligence": {...},
        "worker_scores": [...]
    }
    """
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    # Demo: simulate 5 workers with various roles
    workers_by_role = {"foreman": 1, "laborer": 2, "electrician": 1, "inspector": 1}
    worker_scores = []
    
    worker_counter = 0
    for role, count in workers_by_role.items():
        for i in range(count):
            worker_id = f"{project_id}-{role}-{i}"
            records = generate_demo_attendance(worker_id, days=90)
            
            analyzer = WorkforceReliabilityAnalyzer()
            score = analyzer.calculate_worker_reliability(
                worker_id=worker_id,
                worker_name=f"{role.title()} {i+1}",
                role=role,
                attendance_records=records,
            )
            worker_scores.append(score)
            worker_counter += 1
    
    # Estimate impact
    analyzer = WorkforceReliabilityAnalyzer()
    impact_factors = analyzer.estimate_schedule_impact(
        worker_scores=worker_scores,
        project_workers_by_role=workers_by_role,
    )
    impact_factors.project_id = project_id
    
    # Synthesize project intelligence
    intelligence = analyzer.project_workforce_intelligence(
        project_id=project_id,
        worker_scores=worker_scores,
        impact_factors=impact_factors,
    )
    intelligence.workers_by_role = workers_by_role
    
    response = {
        "status": "success",
        "workforce_intelligence": workforce_to_dict(intelligence),
        "worker_scores": [workforce_to_dict(s) for s in worker_scores],
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200
