"""Phase 21 - Compliance & Safety API Endpoints

REST API for accessing compliance assessments, safety incident analysis, and
regulatory risk scoring.

Endpoints:
- POST /phase21/analyze - Analyze compliance and safety for a project
- GET /phase21/project/<project_id> - Get project-level compliance/safety intelligence
"""

from flask import Blueprint, request, jsonify, make_response
import json
from datetime import datetime

from phase21_compliance_types import compliance_to_dict
from phase21_compliance_analyzer import ComplianceSafetyAnalyzer

compliance_bp = Blueprint("phase21_compliance", __name__, url_prefix="/phase21")


@compliance_bp.route("/analyze", methods=["POST", "OPTIONS"])
def analyze_compliance():
    """Analyze compliance and safety for a project.
    
    Request body (JSON):
    {
        "project_id": "PROJ_001",
        "incidents": [...],  // Optional; if missing, demo data generated
        "assessments": [...]  // Optional; if missing, standard checkpoints assessed
    }
    
    Response (200 OK):
    {
        "status": "success",
        "project_id": "PROJ_001",
        "compliance_safety": {...},
        "risk_score": {...}
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
    
    analyzer = ComplianceSafetyAnalyzer()
    
    # Get or generate incidents
    incidents_input = payload.get("incidents")
    if incidents_input:
        incidents = incidents_input
    else:
        incidents = analyzer.generate_demo_incidents(project_id, count=5, days_back=90)
    
    # Get or generate assessments
    assessments_input = payload.get("assessments")
    if assessments_input:
        assessments = assessments_input
    else:
        checkpoints = analyzer.standard_checkpoints()
        assessments = analyzer.assess_compliance(project_id, checkpoints)
    
    # Calculate safety risk
    safety_risk_score = analyzer.calculate_safety_risk(
        project_id=project_id,
        incidents=incidents,
        assessments=assessments,
        estimated_hours_worked=1000,
    )
    
    # Synthesize project intelligence
    compliance_safety = analyzer.project_compliance_safety(
        project_id=project_id,
        incidents=incidents,
        safety_risk_score=safety_risk_score,
        assessments=assessments,
    )
    
    response = {
        "status": "success",
        "project_id": project_id,
        "compliance_safety": compliance_to_dict(compliance_safety),
        "risk_score": compliance_to_dict(safety_risk_score),
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200


@compliance_bp.route("/project/<project_id>", methods=["GET", "OPTIONS"])
def get_project_compliance(project_id: str):
    """Get project-level compliance and safety intelligence (demo mode).
    
    Response (200 OK):
    {
        "status": "success",
        "compliance_safety": {...},
        "risk_score": {...}
    }
    """
    if request.method == "OPTIONS":
        resp = make_response(('', 204))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    analyzer = ComplianceSafetyAnalyzer()
    
    # Generate demo data
    incidents = analyzer.generate_demo_incidents(project_id, count=5)
    checkpoints = analyzer.standard_checkpoints()
    assessments = analyzer.assess_compliance(project_id, checkpoints)
    
    # Calculate safety risk
    safety_risk_score = analyzer.calculate_safety_risk(
        project_id=project_id,
        incidents=incidents,
        assessments=assessments,
    )
    
    # Synthesize intelligence
    compliance_safety = analyzer.project_compliance_safety(
        project_id=project_id,
        incidents=incidents,
        safety_risk_score=safety_risk_score,
        assessments=assessments,
    )
    
    response = {
        "status": "success",
        "compliance_safety": compliance_to_dict(compliance_safety),
        "risk_score": compliance_to_dict(safety_risk_score),
    }
    
    resp = jsonify(response)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200
