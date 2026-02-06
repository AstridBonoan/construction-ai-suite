"""
Unit tests for Phase 22: Compliance & Safety Intelligence
Tests deterministic compliance risk scoring and violation analysis
"""
import pytest
from datetime import datetime, timedelta

from phase22_compliance_types import (
    ComplianceViolation,
    SafetyInspection,
    ViolationSeverity,
    InspectionStatus,
    ComplianceRiskLevel,
    ShutdownRiskLevel,
)
from phase22_compliance_analyzer import ComplianceAnalyzer


class TestComplianceAnalyzer:
    """Test suite for ComplianceAnalyzer"""

    def setup_method(self):
        """Setup before each test"""
        self.analyzer = ComplianceAnalyzer()

    def test_violation_risk_score_no_violations(self):
        """Test that no violations returns low risk"""
        score = self.analyzer.calculate_violation_risk_score([], 0, None)
        assert score == 0.0

    def test_violation_risk_score_single_serious(self):
        """Test serious violation produces medium risk"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
                description="Inadequate fall protection",
            )
        ]
        score = self.analyzer.calculate_violation_risk_score(violations, 0, 0)
        assert 0.25 < score < 0.50  # Serious should be medium range

    def test_violation_risk_score_critical(self):
        """Test critical violation produces high risk"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA Critical",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
                description="Critical safety hazard",
            )
        ]
        score = self.analyzer.calculate_violation_risk_score(violations, 0, 0)
        assert score > 0.70  # Critical should be high

    def test_violation_risk_score_with_history(self):
        """Test historical violations increase risk"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
            )
        ]
        # Score with no history
        score1 = self.analyzer.calculate_violation_risk_score(violations, 0, None)
        # Score with history
        score2 = self.analyzer.calculate_violation_risk_score(violations, 5, None)
        assert score2 > score1  # History should increase score

    def test_score_to_risk_level_low(self):
        """Test score-to-level conversion for low risk"""
        level = self.analyzer.score_to_risk_level(0.10)
        assert level == ComplianceRiskLevel.LOW

    def test_score_to_risk_level_medium(self):
        """Test score-to-level conversion for medium risk"""
        level = self.analyzer.score_to_risk_level(0.40)
        assert level == ComplianceRiskLevel.MEDIUM

    def test_score_to_risk_level_high(self):
        """Test score-to-level conversion for high risk"""
        level = self.analyzer.score_to_risk_level(0.65)
        assert level == ComplianceRiskLevel.HIGH

    def test_score_to_risk_level_critical(self):
        """Test score-to-level conversion for critical risk"""
        level = self.analyzer.score_to_risk_level(0.85)
        assert level == ComplianceRiskLevel.CRITICAL

    def test_shutdown_risk_score_no_violations(self):
        """Test no violations = no shutdown risk"""
        score = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=0,
            serious_violations=0,
            total_violations=0,
            days_since_last_inspection=30,
            has_failed_recent_inspection=False,
            unresolved_citations=0,
        )
        assert score == 0.0

    def test_shutdown_risk_score_critical_violations(self):
        """Test critical violations trigger high shutdown risk"""
        score = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=2,
            serious_violations=0,
            total_violations=2,
            days_since_last_inspection=30,
            has_failed_recent_inspection=False,
            unresolved_citations=0,
        )
        assert score > 0.5  # Should be moderate to high

    def test_shutdown_risk_score_failed_inspection(self):
        """Test failed recent inspection increases shutdown risk"""
        score = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=0,
            serious_violations=0,
            total_violations=0,
            days_since_last_inspection=10,
            has_failed_recent_inspection=True,
            unresolved_citations=0,
        )
        assert score > 0.30  # Should be at least low-moderate

    def test_shutdown_risk_score_overdue_inspection(self):
        """Test overdue inspection increases shutdown risk"""
        score_current = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=0,
            serious_violations=0,
            total_violations=0,
            days_since_last_inspection=30,
            has_failed_recent_inspection=False,
            unresolved_citations=0,
        )
        score_overdue = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=0,
            serious_violations=0,
            total_violations=0,
            days_since_last_inspection=150,
            has_failed_recent_inspection=False,
            unresolved_citations=0,
        )
        # Overdue inspection should increase risk even with no violations
        assert score_overdue >= 0.10  # Should be at least inspection_overdue_component

    def test_shutdown_risk_level_none(self):
        """Test shutdown risk level conversion for None"""
        level = self.analyzer.score_to_shutdown_level(0.05)
        assert level == ShutdownRiskLevel.NONE

    def test_shutdown_risk_level_high(self):
        """Test shutdown risk level conversion for High"""
        level = self.analyzer.score_to_shutdown_level(0.80)
        assert level == ShutdownRiskLevel.HIGH

    def test_generate_insights_critical_violations(self):
        """Test that critical violations generate insight"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA Critical",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
            )
        ]
        insights = self.analyzer.generate_compliance_insights(
            project_id="p1",
            active_violations=violations,
            days_since_last_inspection=30,
            compliance_score=0.8,
            shutdown_score=0.7,
        )
        assert len(insights) > 0
        assert any(i.insight_type == "violation_risk" for i in insights)
        assert insights[0].severity == "critical"

    def test_generate_insights_overdue_inspection(self):
        """Test that overdue inspection generates insight"""
        insights = self.analyzer.generate_compliance_insights(
            project_id="p1",
            active_violations=[],
            days_since_last_inspection=150,  # Overdue
            compliance_score=0.3,
            shutdown_score=0.1,
        )
        assert any(i.insight_type == "inspection_overdue" for i in insights)

    def test_generate_insights_shutdown_risk(self):
        """Test that high shutdown risk generates insight"""
        insights = self.analyzer.generate_compliance_insights(
            project_id="p1",
            active_violations=[],
            days_since_last_inspection=30,
            compliance_score=0.3,
            shutdown_score=0.7,  # High shutdown risk
        )
        assert any(i.insight_type == "shutdown_risk" for i in insights)

    def test_generate_health_summary_compliant(self):
        """Test health summary for compliant project"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p1",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            ),
            SafetyInspection(
                inspection_id="i2",
                project_id="p1",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            ),
        ]
        violations = []

        summary = self.analyzer.generate_health_summary("p1", "Project 1", inspections, violations)

        assert summary.compliance_risk_score < 0.25
        assert summary.compliance_risk_level == ComplianceRiskLevel.LOW
        assert summary.active_violations == 0
        assert summary.total_inspections == 2
        assert summary.inspections_passed == 2

    def test_generate_health_summary_with_violations(self):
        """Test health summary with active violations"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p1",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.FAILED,
                passed=False,
                violations_found=2,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
                mitigation_completed=False,
            ),
            ComplianceViolation(
                violation_id="v2",
                project_id="p1",
                regulation_id="osha_2",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
                mitigation_completed=True,
            ),
        ]

        summary = self.analyzer.generate_health_summary("p1", "Project 1", inspections, violations)

        assert summary.active_violations == 1
        assert summary.resolved_violations == 1
        assert summary.total_violations_ever == 2
        assert summary.inspections_failed == 1

    def test_generate_intelligence_complete(self):
        """Test complete intelligence generation"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p1",
                inspection_date=datetime.now().isoformat(),
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.SERIOUS,
            )
        ]

        intelligence = self.analyzer.generate_intelligence("p1", "Project 1", inspections, violations)

        assert intelligence.project_id == "p1"
        assert intelligence.project_name == "Project 1"
        assert intelligence.compliance_health_summary is not None
        assert intelligence.compliance_risk_score >= 0.0
        assert intelligence.compliance_risk_score <= 1.0
        assert intelligence.shutdown_risk_score >= 0.0
        assert intelligence.shutdown_risk_score <= 1.0
        assert intelligence.integration_ready is True

    def test_generate_audit_report(self):
        """Test audit report generation"""
        inspections = [
            SafetyInspection(
                inspection_id="i1",
                project_id="p1",
                inspection_date="2024-06-15",
                status=InspectionStatus.PASSED,
                passed=True,
            )
        ]
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA Fall Protection",
                violation_date="2024-06-10",
                severity=ViolationSeverity.SERIOUS,
                fine_amount_usd=2500.0,
                mitigation_required=True,
                mitigation_completed=False,
            )
        ]

        report = self.analyzer.generate_audit_report(
            "p1", "Project 1", "2024-01-01", "2024-12-31", inspections, violations
        )

        assert report.project_id == "p1"
        assert report.project_name == "Project 1"
        assert report.total_inspections == 1
        assert report.total_violations == 1
        assert report.estimated_financial_exposure == 2500.0
        assert "serious" in report.by_severity
        assert report.corrective_actions_required == 1

    def test_deterministic_scoring(self):
        """Test that scoring is deterministic (same inputs = same outputs)"""
        violations = [
            ComplianceViolation(
                violation_id="v1",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date="2024-01-01",
                severity=ViolationSeverity.SERIOUS,
            )
        ]

        # Score twice with identical inputs
        score1 = self.analyzer.calculate_violation_risk_score(violations, 2, 30)
        score2 = self.analyzer.calculate_violation_risk_score(violations, 2, 30)

        assert score1 == score2  # Must be exactly equal

    def test_score_bounds(self):
        """Test that all scores are bounded 0.0-1.0"""
        # Very high severity
        violations = [
            ComplianceViolation(
                violation_id=f"v{i}",
                project_id="p1",
                regulation_id="osha_1",
                regulation_name="OSHA",
                violation_date=datetime.now().isoformat(),
                severity=ViolationSeverity.CRITICAL,
            )
            for i in range(100)
        ]
        score = self.analyzer.calculate_violation_risk_score(violations, 1000, 1)

        assert 0.0 <= score <= 1.0

        # Very high shutdown risk
        shutdown_score = self.analyzer.calculate_shutdown_risk_score(
            critical_violations=100,
            serious_violations=200,
            total_violations=300,
            days_since_last_inspection=1000,
            has_failed_recent_inspection=True,
            unresolved_citations=50,
        )

        assert 0.0 <= shutdown_score <= 1.0
