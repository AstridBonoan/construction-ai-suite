"""
Phase 22: Compliance & Safety API
REST endpoints for compliance analysis and intelligence
"""
from flask import Blueprint, request, jsonify
from typing import Dict, Any, List
from datetime import datetime
import logging

from phase22_compliance_types import (
    ComplianceViolation,
    SafetyInspection,
    ViolationSeverity,
    InspectionStatus,
)
from phase22_compliance_integration import analyze_compliance, ComplianceIntegration

logger = logging.getLogger(__name__)

# Create blueprint
compliance_bp = Blueprint("compliance", __name__, url_prefix="/api/phase22/compliance")

# Integration instance
compliance_integration = ComplianceIntegration()


@compliance_bp.route("/analyze", methods=["POST"])
def analyze_compliance_endpoint():
    """
    Analyze compliance and safety for a project.

    Request JSON:
    {
        "project_id": "proj_123",
        "project_name": "Downtown Tower",
        "inspections": [
            {
                "inspection_id": "insp_1",
                "project_id": "proj_123",
                "inspection_date": "2024-01-15",
                "status": "completed",
                "passed": true,
                "violations_found": 0
            }
        ],
        "violations": [
            {
                "violation_id": "viol_1",
                "project_id": "proj_123",
                "regulation_id": "osha_fall_protection",
                "regulation_name": "OSHA Fall Protection Standard",
                "violation_date": "2024-01-10",
                "severity": "serious",
                "description": "Inadequate fall protection beyond 10 feet",
                "citation_issued": false,
                "fine_amount_usd": 2500
            }
        ]
    }

    Returns:
    {
        "project_id": "proj_123",
        "project_name": "Downtown Tower",
        "compliance_risk_score": 0.35,
        "compliance_risk_level": "medium",
        "shutdown_risk_score": 0.15,
        "shutdown_risk_level": "low",
        "active_violations": 1,
        "insights": [...],
        "recommendations": [...],
        "status": "success"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400

        project_id = data.get("project_id")
        project_name = data.get("project_name", f"Project_{project_id}")

        if not project_id:
            return jsonify({"status": "error", "message": "project_id is required"}), 400

        # Parse inspections
        inspection_data = data.get("inspections", [])
        inspections = []
        for insp in inspection_data:
            try:
                inspections.append(
                    SafetyInspection(
                        inspection_id=insp.get("inspection_id", f"insp_{len(inspections)}"),
                        project_id=project_id,
                        task_id=insp.get("task_id"),
                        site_id=insp.get("site_id", ""),
                        inspection_date=insp.get("inspection_date", datetime.now().isoformat()),
                        inspection_type=insp.get("inspection_type", "routine"),
                        inspector_name=insp.get("inspector_name", ""),
                        status=InspectionStatus[insp.get("status", "completed").upper()]
                        if insp.get("status", "completed").upper() in InspectionStatus.__members__
                        else InspectionStatus.COMPLETED,
                        passed=insp.get("passed", False),
                        violations_found=insp.get("violations_found", 0),
                        notes=insp.get("notes", ""),
                        follow_up_required=insp.get("follow_up_required", False),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse inspection: {str(e)}")
                continue

        # Parse violations
        violation_data = data.get("violations", [])
        violations = []
        for viol in violation_data:
            try:
                severity_str = viol.get("severity", "serious").upper()
                severity = (
                    ViolationSeverity[severity_str]
                    if severity_str in ViolationSeverity.__members__
                    else ViolationSeverity.SERIOUS
                )

                violations.append(
                    ComplianceViolation(
                        violation_id=viol.get("violation_id", f"viol_{len(violations)}"),
                        project_id=project_id,
                        task_id=viol.get("task_id"),
                        regulation_id=viol.get("regulation_id", ""),
                        regulation_name=viol.get("regulation_name", ""),
                        violation_date=viol.get("violation_date", datetime.now().isoformat()),
                        severity=severity,
                        description=viol.get("description", ""),
                        citation_issued=viol.get("citation_issued", False),
                        fine_amount_usd=viol.get("fine_amount_usd", 0.0),
                        mitigation_required=viol.get("mitigation_required", True),
                        mitigation_deadline=viol.get("mitigation_deadline"),
                        mitigation_completed=viol.get("mitigation_completed", False),
                        mitigation_completion_date=viol.get("mitigation_completion_date"),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse violation: {str(e)}")
                continue

        # Perform analysis
        result = analyze_compliance(project_id, project_name, inspections, violations)
        result["status"] = "success"

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Compliance analysis error: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@compliance_bp.route("/intelligence/<project_id>", methods=["GET"])
def get_intelligence_endpoint(project_id: str):
    """
    Get stored compliance intelligence for a project.

    Returns compliance risk analysis, insights, and recommendations.
    """
    try:
        intelligence = compliance_integration.get_project_intelligence(project_id)

        if not intelligence:
            return jsonify({"status": "error", "message": f"No compliance data for project {project_id}"}), 404

        result = {
            "project_id": intelligence.project_id,
            "project_name": intelligence.project_name,
            "compliance_risk_score": intelligence.compliance_risk_score,
            "compliance_risk_level": intelligence.compliance_health_summary.compliance_risk_level.value
            if intelligence.compliance_health_summary
            else "unknown",
            "shutdown_risk_score": intelligence.shutdown_risk_score,
            "shutdown_risk_level": intelligence.compliance_health_summary.shutdown_risk_level.value
            if intelligence.compliance_health_summary
            else "unknown",
            "active_violations": len(intelligence.active_violations),
            "critical_violations": intelligence.critical_violation_count,
            "insights": [
                {
                    "type": insight.insight_type,
                    "severity": insight.severity,
                    "description": insight.description,
                    "recommendations": insight.recommended_actions,
                }
                for insight in intelligence.compliance_risk_insights
            ],
            "recommendations": intelligence.recommended_immediate_actions,
            "project_summary": intelligence.project_summary,
            "audit_ready": intelligence.audit_ready_status,
            "generated_at": intelligence.generated_at,
            "status": "success",
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Failed to get intelligence: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@compliance_bp.route("/score-detail/<project_id>", methods=["GET"])
def get_score_detail_endpoint(project_id: str):
    """
    Get detailed breakdown of compliance and shutdown risk scores.

    Returns:
    {
        "project_id": "proj_123",
        "compliance_score": 0.35,
        "compliance_level": "medium",
        "shutdown_score": 0.15,
        "shutdown_level": "low",
        "health_summary": {
            "total_inspections": 5,
            "inspections_passed": 4,
            "inspections_failed": 1,
            "active_violations": 2,
            "resolved_violations": 8,
            "total_violations_ever": 10,
            "estimated_fine_exposure": 5000.0,
            "days_since_last_inspection": 45,
            "explanation": "..."
        },
        "status": "success"
    }
    """
    try:
        intelligence = compliance_integration.get_project_intelligence(project_id)

        if not intelligence or not intelligence.compliance_health_summary:
            return jsonify({"status": "error", "message": f"No compliance data for project {project_id}"}), 404

        health = intelligence.compliance_health_summary

        result = {
            "project_id": project_id,
            "compliance_score": round(health.compliance_risk_score, 3),
            "compliance_level": health.compliance_risk_level.value,
            "shutdown_score": round(health.shutdown_risk_score, 3),
            "shutdown_level": health.shutdown_risk_level.value,
            "health_summary": {
                "total_inspections": health.total_inspections,
                "inspections_passed": health.inspections_passed,
                "inspections_failed": health.inspections_failed,
                "active_violations": health.active_violations,
                "resolved_violations": health.resolved_violations,
                "total_violations_ever": health.total_violations_ever,
                "estimated_fine_exposure": health.estimated_fine_exposure_usd,
                "days_since_last_inspection": health.days_since_last_inspection,
                "explanation": health.explanation,
            },
            "status": "success",
        }

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Failed to get score detail: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@compliance_bp.route("/audit-report/<project_id>", methods=["POST"])
def generate_audit_report_endpoint(project_id: str):
    """
    Generate audit-ready compliance report for a project.

    Request JSON:
    {
        "period_start": "2024-01-01",
        "period_end": "2024-12-31"
    }

    Returns audit report with findings, violations, and recommendations.
    """
    try:
        data = request.get_json() or {}
        period_start = data.get("period_start", "2024-01-01")
        period_end = data.get("period_end", "2024-12-31")

        report = compliance_integration.get_audit_report(project_id, period_start, period_end)

        if not report:
            return jsonify({"status": "error", "message": f"No compliance data for project {project_id}"}), 404

        report["status"] = "success"
        return jsonify(report), 200

    except Exception as e:
        logger.error(f"Failed to generate audit report: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@compliance_bp.route("/monday-mapping/<project_id>", methods=["GET"])
def get_monday_mapping_endpoint(project_id: str):
    """
    Get compliance intelligence formatted for monday.com integration.

    Returns data structure ready to update monday.com board columns.
    """
    try:
        intelligence = compliance_integration.get_project_intelligence(project_id)

        if not intelligence:
            return jsonify({"status": "error", "message": f"No compliance data for project {project_id}"}), 404

        mapping = compliance_integration.export_monday_mapping(intelligence)
        return jsonify(mapping), 200

    except Exception as e:
        logger.error(f"Failed to get monday mapping: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@compliance_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "compliance", "version": "1.0"}), 200
