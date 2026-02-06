"""
Integration tests for Phase 22: Compliance & Safety Intelligence
Validates monday.com mapping and core engine integration
"""
import pytest
from datetime import datetime

from phase22_compliance_types import (
    ComplianceViolation,
    SafetyInspection,
    ViolationSeverity,
    InspectionStatus,
)
from phase22_compliance_integration import (
    ComplianceIntegration,
    analyze_compliance,
)


class TestComplianceIntegration:
    """Test compliance integration with core systems"""

    def setup_method(self):
        """Setup before each test"""
        # Use the module-level singleton instance
        import phase22_compliance_integration
        self.integration = phase22_compliance_integration._integration_instance

    def test_analyze_compliance_basic(self):
        """Test basic compliance analysis"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p_basic",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = []

        result = analyze_compliance("p_basic", "Project 1", inspections, violations)

        assert result["project_id"] == "p_basic"
        assert result["project_name"] == "Project 1"
        assert "compliance_risk_score" in result
        assert "shutdown_risk_score" in result
        assert "compliance_risk_level" in result
        assert "shutdown_risk_level" in result
        # Check for integration status instead of service status
        assert "integration_status" in result

    def test_analyze_compliance_with_violations(self):
        """Test compliance analysis with violations"""
        inspections = []
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_viol",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
                fine_amount_usd=2500.0,
                citation_issued=True,
                mitigation_completed=False,
            ),
            ComplianceViolation(
                violation_id="v2",
                project_id="p_viol",
                regulation_id="env_1",
                regulation_name="Environmental Impact",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.MINOR,
                fine_amount_usd=500.0,
                citation_issued=False,
                mitigation_completed=False,
            ),
        ]

        result = analyze_compliance("p_viol", "Project 1", inspections, violations)

        assert result["active_violations"] == 2
        assert result["compliance_risk_score"] > 0.0
        assert len(result["insights"]) > 0
        assert "integration_status" in result

    def test_analyze_compliance_critical_violation(self):
        """Test that critical violations are properly flagged"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_critical",
                regulation_id="osha_crit",
                regulation_name="OSHA Critical Safety",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
                fine_amount_usd=10000.0,
                citation_issued=True,
            )
        ]

        result = analyze_compliance("p_critical", "Project 1", [], violations)

        assert result["critical_violations"] == 1
        assert result["compliance_risk_score"] > 0.70  # Critical violations produce high score
        assert result["compliance_risk_level"] in ["high", "critical"]  # May be high or critical depending on calculation
        critical_insight = [i for i in result["insights"] if i["severity"] == "critical"]
        assert len(critical_insight) > 0

    def test_monday_mapping_structure(self):
        """Test that monday.com mapping has required structure"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p_monday",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_monday",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
            )
        ]

        # Analyze to populate data
        analyze_compliance("p_monday", "Project 1", inspections, violations)

        # Get monday mapping
        intelligence = self.integration.get_project_intelligence("p_monday")
        mapping = self.integration.export_monday_mapping(intelligence)

        # Verify required columns for monday
        required_columns = [
            "project_id",
            "project_name",
            "compliance_risk_score",
            "compliance_risk_level",
            "shutdown_risk_score",
            "shutdown_risk_level",
            "active_violations",
            "critical_violation_count",
            "estimated_fine_exposure",
            "last_inspection_date",
            "audit_ready",
            "status",
        ]

        for column in required_columns:
            assert column in mapping, f"Missing required column: {column}"

    def test_monday_mapping_values_are_serializable(self):
        """Test that monday mapping values are JSON-serializable"""
        import json

        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p1",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = []

        analyze_compliance("p1", "Project 1", inspections, violations)

        intelligence = self.integration.get_project_intelligence("p1")
        mapping = self.integration.export_monday_mapping(intelligence)

        # Should not raise
        json_str = json.dumps(mapping)
        assert len(json_str) > 0

    def test_compliance_scoring_consistency(self):
        """Test that scoring is consistent across calls"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p_consist",
                inspection_date="2024-01-15",
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_consist",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date="2024-01-10",
                severity=ViolationSeverity.SERIOUS,
                fine_amount_usd=2500.0,
            )
        ]

        # Run analysis twice
        result1 = analyze_compliance("p_consist", "Project 1", inspections, violations)
        result2 = analyze_compliance("p_consist", "Project 1", inspections, violations)

        # Scores should be identical
        assert result1["compliance_risk_score"] == result2["compliance_risk_score"]
        assert result1["shutdown_risk_score"] == result2["shutdown_risk_score"]
        assert result1["compliance_risk_level"] == result2["compliance_risk_level"]

    def test_multiple_projects_isolation(self):
        """Test that multiple projects don't interfere"""
        inspections1 = []
        violations1 = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_iso1",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
            )
        ]

        inspections2 = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p_iso2",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations2 = []

        # Analyze both projects
        result1 = analyze_compliance("p_iso1", "Project 1", inspections1, violations1)
        result2 = analyze_compliance("p_iso2", "Project 2", inspections2, violations2)

        # Project 1 should have high risk
        assert result1["compliance_risk_score"] > 0.70

        # Project 2 should have low risk
        assert result2["compliance_risk_score"] < 0.25

        # Verify stored data is separate
        intel1 = self.integration.get_project_intelligence("p_iso1")
        intel2 = self.integration.get_project_intelligence("p_iso2")

        assert intel1.project_id == "p_iso1"
        assert intel2.project_id == "p_iso2"
        assert intel1.compliance_risk_score > intel2.compliance_risk_score

    def test_audit_report_generation(self):
        """Test audit report generation for compliance review"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p_audit",
                inspection_date="2024-06-15",
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_audit",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date="2024-06-10",
                severity=ViolationSeverity.SERIOUS,
                fine_amount_usd=2500.0,
                mitigation_required=True,
                mitigation_completed=False,
            )
        ]

        analyze_compliance("p_audit", "Project 1", inspections, violations)

        report = self.integration.get_audit_report("p_audit", "2024-01-01", "2024-12-31")

        assert report is not None
        assert "report_id" in report
        assert "project_id" in report
        assert report["total_violations"] == 1
        assert report["estimated_financial_exposure"] == 2500.0
        assert report["compliance_status"] == "at_risk"
        assert len(report["recommendations"]) > 0

    def test_compliance_recommendations_present(self):
        """Test that compliance analysis includes recommendations"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p_rec",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
            )
        ]

        result = analyze_compliance("p_rec", "Project 1", [], violations)

        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert all(isinstance(r, str) for r in result["recommendations"])

    def test_compliance_score_boundaries(self):
        """Test that compliance scores stay within 0-1 bounds"""
        # Create extreme scenario
        violations = [
            ComplianceViolation(
                violation_id=f"v{i}",
                project_id="p_bound",
                regulation_id=f"osha_{i}",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
            )
            for i in range(100)
        ]
        inspections = [
            SafetyInspection(
                inspection_id=f"i{i}",
                project_id="p_bound",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.FAILED,
                passed=False,
            )
            for i in range(10)
        ]

        result = analyze_compliance("p_bound", "Project 1", inspections, violations)

        assert 0.0 <= result["compliance_risk_score"] <= 1.0
        assert 0.0 <= result["shutdown_risk_score"] <= 1.0

    def test_compliance_integration_ready_flag(self):
        """Test that integration_ready flag is set correctly"""
        inspections = []
        violations = []

        result = analyze_compliance("p_ready", "Project 1", inspections, violations)

        assert "integration_status" in result
        assert result["integration_status"] in ["registered", "pending", "error"]
