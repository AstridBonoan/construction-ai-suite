"""
Phase 22: Compliance Integration
Integrates compliance and safety analysis into core risk engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from phase22_compliance_types import (
    ComplianceViolation,
    SafetyInspection,
    ComplianceIntelligence,
)
from phase22_compliance_analyzer import ComplianceAnalyzer

logger = logging.getLogger(__name__)


class ComplianceIntegration:
    """Integrates compliance analysis with core risk engine"""

    def __init__(self):
        """Initialize compliance integration"""
        self.analyzer = ComplianceAnalyzer()
        self.project_data: Dict[str, Dict[str, Any]] = {}

    def store_project_compliance_data(
        self,
        project_id: str,
        project_name: str,
        inspections: List[SafetyInspection],
        violations: List[ComplianceViolation],
    ) -> None:
        """
        Store compliance data for a project.

        Args:
            project_id: Project identifier
            project_name: Project name
            inspections: List of safety inspections
            violations: List of compliance violations
        """
        self.project_data[project_id] = {
            "project_name": project_name,
            "inspections": inspections,
            "violations": violations,
            "stored_at": datetime.now().isoformat(),
        }
        logger.debug(f"Stored compliance data for project {project_id}")

    def analyze_project_compliance(
        self, project_id: str, project_name: str, inspections: List[SafetyInspection], violations: List[ComplianceViolation]
    ) -> ComplianceIntelligence:
        """
        Analyze project compliance and safety.

        Args:
            project_id: Project identifier
            project_name: Project name
            inspections: List of safety inspections
            violations: List of violations

        Returns:
            ComplianceIntelligence with full analysis
        """
        # Store data for later reference
        self.store_project_compliance_data(project_id, project_name, inspections, violations)

        # Generate intelligence
        intelligence = self.analyzer.generate_intelligence(project_id, project_name, inspections, violations)

        return intelligence

    def register_compliance_risk(
        self, project_id: str, compliance_score: float, shutdown_score: float, explanation: str = ""
    ) -> Dict[str, Any]:
        """
        Register compliance risk with core risk engine.
        This is called from analyze_project_compliance and should propagate to the core engine.

        Args:
            project_id: Project identifier
            compliance_score: Compliance risk score 0.0-1.0
            shutdown_score: Shutdown risk score 0.0-1.0
            explanation: Risk explanation

        Returns:
            Registration confirmation
        """
        # Try to register with core engine if available
        try:
            from ml.core_risk_engine import register_compliance_risk as core_register

            core_register(project_id, compliance_score, shutdown_score, explanation)
            logger.info(
                f"Registered compliance risk for project {project_id}: "
                f"compliance={compliance_score:.2f}, shutdown={shutdown_score:.2f}"
            )
            return {"status": "registered", "project_id": project_id, "compliance_score": compliance_score}
        except ImportError:
            logger.warning("Core risk engine not available; compliance risk not registered")
            return {"status": "pending", "project_id": project_id, "reason": "core_engine_unavailable"}
        except Exception as e:
            logger.error(f"Failed to register compliance risk: {str(e)}")
            return {"status": "error", "project_id": project_id, "error": str(e)}

    def get_project_intelligence(self, project_id: str) -> Optional[ComplianceIntelligence]:
        """
        Get stored compliance intelligence for a project.

        Args:
            project_id: Project identifier

        Returns:
            ComplianceIntelligence or None if not available
        """
        if project_id not in self.project_data:
            logger.warning(f"No compliance data found for project {project_id}")
            return None

        data = self.project_data[project_id]
        return self.analyzer.generate_intelligence(
            project_id, data["project_name"], data["inspections"], data["violations"]
        )

    def get_audit_report(
        self, project_id: str, period_start: str, period_end: str
    ) -> Optional[Dict[str, Any]]:
        """
        Generate audit report for compliance review.

        Args:
            project_id: Project identifier
            period_start: ISO date string
            period_end: ISO date string

        Returns:
            Audit report as dict or None
        """
        if project_id not in self.project_data:
            logger.warning(f"No compliance data found for project {project_id}")
            return None

        data = self.project_data[project_id]
        report = self.analyzer.generate_audit_report(
            project_id, data["project_name"], period_start, period_end, data["inspections"], data["violations"]
        )

        return {
            "report_id": report.report_id,
            "project_id": report.project_id,
            "project_name": report.project_name,
            "report_date": report.report_date,
            "period_start_date": report.period_start_date,
            "period_end_date": report.period_end_date,
            "total_inspections": report.total_inspections,
            "total_violations": report.total_violations,
            "by_severity": report.by_severity,
            "critical_findings": report.critical_findings,
            "corrective_actions_required": report.corrective_actions_required,
            "corrective_actions_completed": report.corrective_actions_completed,
            "estimated_financial_exposure": report.estimated_financial_exposure,
            "compliance_status": report.compliance_status,
            "executive_summary": report.executive_summary,
            "recommendations": report.recommendations,
        }

    def export_monday_mapping(self, compliance_intelligence: ComplianceIntelligence) -> Dict[str, Any]:
        """
        Export compliance intelligence for monday.com integration.

        Args:
            compliance_intelligence: ComplianceIntelligence object

        Returns:
            Dict ready for monday.com board update
        """
        if not compliance_intelligence:
            return {"status": "error", "reason": "No compliance intelligence provided"}

        return {
            "project_id": compliance_intelligence.project_id,
            "project_name": compliance_intelligence.project_name,
            "compliance_risk_score": round(compliance_intelligence.compliance_risk_score, 2),
            "shutdown_risk_score": round(compliance_intelligence.shutdown_risk_score, 2),
            "compliance_risk_level": compliance_intelligence.compliance_health_summary.compliance_risk_level.value
            if compliance_intelligence.compliance_health_summary
            else "unknown",
            "shutdown_risk_level": compliance_intelligence.compliance_health_summary.shutdown_risk_level.value
            if compliance_intelligence.compliance_health_summary
            else "unknown",
            "active_violations": compliance_intelligence.compliance_health_summary.active_violations
            if compliance_intelligence.compliance_health_summary
            else 0,
            "critical_violation_count": compliance_intelligence.critical_violation_count,
            "estimated_fine_exposure": f"${compliance_intelligence.estimated_total_fine_exposure:,.2f}",
            "last_inspection_date": compliance_intelligence.compliance_health_summary.last_inspection_date
            if compliance_intelligence.compliance_health_summary
            else "Never",
            "days_since_inspection": compliance_intelligence.compliance_health_summary.days_since_last_inspection
            if compliance_intelligence.compliance_health_summary
            else 999,
            "audit_ready": compliance_intelligence.audit_ready_status,
            "project_summary": compliance_intelligence.project_summary,
            "insights_count": len(compliance_intelligence.compliance_risk_insights),
            "recommendations": compliance_intelligence.recommended_immediate_actions,
            "status": "ready",
            "monday_updates": compliance_intelligence.monday_updates,
        }


# Singleton instance for module-level access
_integration_instance = ComplianceIntegration()


def analyze_compliance(
    project_id: str, project_name: str, inspections: List[SafetyInspection], violations: List[ComplianceViolation]
) -> Dict[str, Any]:
    """
    Module-level function to analyze compliance.

    Args:
        project_id: Project identifier
        project_name: Project name
        inspections: List of safety inspections
        violations: List of violations

    Returns:
        ComplianceIntelligence as dict
    """
    intelligence = _integration_instance.analyze_project_compliance(project_id, project_name, inspections, violations)

    # Register with core engine
    registration_result = _integration_instance.register_compliance_risk(
        project_id,
        intelligence.compliance_risk_score,
        intelligence.shutdown_risk_score,
        intelligence.project_summary,
    )

    return {
        "project_id": project_id,
        "project_name": project_name,
        "compliance_risk_score": intelligence.compliance_risk_score,
        "shutdown_risk_score": intelligence.shutdown_risk_score,
        "compliance_risk_level": intelligence.compliance_health_summary.compliance_risk_level.value
        if intelligence.compliance_health_summary
        else "unknown",
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
        "integration_status": registration_result.get("status", "unknown"),
        "generated_at": intelligence.generated_at,
    }
