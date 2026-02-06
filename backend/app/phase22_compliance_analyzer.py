"""
Compliance & Safety Analyzer for Phase 22
Implements deterministic compliance risk scoring and violation analysis
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from phase22_compliance_types import (
    ComplianceHealthSummary,
    ComplianceRiskInsight,
    ComplianceIntelligence,
    ComplianceViolation,
    SafetyInspection,
    ViolationSeverity,
    InspectionStatus,
    ComplianceRiskLevel,
    ShutdownRiskLevel,
    AuditReport,
)


class ComplianceAnalyzer:
    """
    Analyzes compliance and safety data to produce risk scores and intelligence.
    Uses deterministic algorithms (no randomness) for reproducibility.
    """

    # Violation severity weights for risk calculation
    SEVERITY_WEIGHTS = {
        ViolationSeverity.MINOR.value: 0.1,
        ViolationSeverity.SERIOUS.value: 0.35,
        ViolationSeverity.WILLFUL.value: 0.60,
        ViolationSeverity.REPEAT.value: 0.75,
        ViolationSeverity.CRITICAL.value: 1.0,
    }

    # Time-based recency multiplier (violations more recent = higher weight)
    MAX_VIOLATION_AGE_DAYS = 365
    RECENCY_DECAY_FACTOR = 0.98  # Daily decay

    # Inspection threshold (days): if > this, site is "overdue" for inspection
    INSPECTION_OVERDUE_THRESHOLD_DAYS = 90

    def __init__(self):
        """Initialize the compliance analyzer"""
        pass

    def calculate_violation_risk_score(
        self,
        active_violations: List[ComplianceViolation],
        historical_violation_count: int = 0,
        days_since_last_violation: Optional[int] = None,
    ) -> float:
        """
        Calculate compliance risk score based on violations.
        Score is 0.0 (compliant) to 1.0 (severe violations).

        Args:
            active_violations: List of currently active violations
            historical_violation_count: Total violations in project history
            days_since_last_violation: Days since most recent violation

        Returns:
            Risk score 0.0-1.0
        """
        if not active_violations and historical_violation_count == 0:
            return 0.0

        # Base score from active violations
        active_score = 0.0
        if active_violations:
            weighted_severity = sum(
                self.SEVERITY_WEIGHTS.get(v.severity.value, 0.5)
                for v in active_violations
            )
            # Normalize by violation count
            active_score = min(weighted_severity / len(active_violations), 1.0)

        # Historical factor: repeat offenders score higher
        historical_factor = 0.0
        if historical_violation_count > 0:
            # Scale: 1-5 prior violations = 0.1-0.5, 6+ = 0.6-1.0
            historical_factor = min(historical_violation_count / 20.0, 1.0)

        # Recency factor: recent violations score higher
        recency_factor = 0.0
        if days_since_last_violation is not None:
            if days_since_last_violation <= 30:
                recency_factor = 0.9
            elif days_since_last_violation <= 90:
                recency_factor = 0.6
            elif days_since_last_violation <= 180:
                recency_factor = 0.3
            else:
                recency_factor = 0.0

        # Weighted combination
        score = (active_score * 0.6) + (historical_factor * 0.25) + (recency_factor * 0.15)
        return min(score, 1.0)

    def calculate_shutdown_risk_score(
        self,
        critical_violations: int,
        serious_violations: int,
        total_violations: int,
        days_since_last_inspection: int,
        has_failed_recent_inspection: bool,
        unresolved_citations: int,
    ) -> float:
        """
        Calculate probability/risk of project shutdown due to violations.
        Score is 0.0 (no shutdown risk) to 1.0 (imminent shutdown).

        Args:
            critical_violations: Count of critical-severity violations
            serious_violations: Count of serious-severity violations
            total_violations: Total active violations
            days_since_last_inspection: Days since last inspection
            has_failed_recent_inspection: Whether failed inspection in last 30 days
            unresolved_citations: Count of unresolved citations

        Returns:
            Shutdown risk score 0.0-1.0
        """
        # Check if there's any risk factor (violations, failed inspection, overdue inspection)
        is_overdue = days_since_last_inspection > self.INSPECTION_OVERDUE_THRESHOLD_DAYS
        
        if total_violations == 0 and not has_failed_recent_inspection and not is_overdue:
            return 0.0

        # Critical violations are shutdown triggers
        critical_component = min(critical_violations * 0.3, 1.0)

        # Multiple serious violations increase risk
        serious_component = min((serious_violations / max(total_violations, 1)) * 0.25, 0.25)

        # Failed recent inspection is strong signal
        inspection_component = 0.35 if has_failed_recent_inspection else 0.0

        # Overdue inspections increase uncertainty/risk
        inspection_overdue_component = 0.0
        if is_overdue:
            days_overdue = days_since_last_inspection - self.INSPECTION_OVERDUE_THRESHOLD_DAYS
            inspection_overdue_component = min(days_overdue / 180.0, 0.15)

        # Unresolved citations are direct indicators
        citation_component = min(unresolved_citations * 0.05, 0.25)

        score = (
            critical_component
            + serious_component
            + inspection_component
            + inspection_overdue_component
            + citation_component
        )
        return min(score, 1.0)

    def score_to_risk_level(self, score: float) -> ComplianceRiskLevel:
        """Convert numeric score to risk level category"""
        if score < 0.25:
            return ComplianceRiskLevel.LOW
        elif score < 0.50:
            return ComplianceRiskLevel.MEDIUM
        elif score < 0.75:
            return ComplianceRiskLevel.HIGH
        else:
            return ComplianceRiskLevel.CRITICAL

    def score_to_shutdown_level(self, score: float) -> ShutdownRiskLevel:
        """Convert numeric score to shutdown risk level"""
        if score < 0.10:
            return ShutdownRiskLevel.NONE
        elif score < 0.30:
            return ShutdownRiskLevel.LOW
        elif score < 0.65:
            return ShutdownRiskLevel.MODERATE
        else:
            return ShutdownRiskLevel.HIGH

    def generate_compliance_insights(
        self,
        project_id: str,
        active_violations: List[ComplianceViolation],
        days_since_last_inspection: int,
        compliance_score: float,
        shutdown_score: float,
    ) -> List[ComplianceRiskInsight]:
        """
        Generate actionable compliance and safety insights.

        Args:
            project_id: Project identifier
            active_violations: Current violations
            days_since_last_inspection: Days since last safety inspection
            compliance_score: Overall compliance risk score
            shutdown_score: Shutdown risk score

        Returns:
            List of insights with recommendations
        """
        insights = []

        # Insight 1: Critical violations
        critical_violations = [v for v in active_violations if v.severity == ViolationSeverity.CRITICAL]
        if critical_violations:
            insights.append(
                ComplianceRiskInsight(
                    project_id=project_id,
                    insight_type="violation_risk",
                    severity="critical",
                    description=f"{len(critical_violations)} critical violation(s) requiring immediate remediation",
                    affected_regulations=[v.regulation_name for v in critical_violations],
                    recommended_actions=[
                        "Immediately contact compliance officer",
                        "Develop emergency mitigation plan",
                        "Deploy corrective measures within 48 hours",
                        "Document all corrective actions for audit",
                    ],
                    estimated_cost_to_remediate=sum(v.fine_amount_usd for v in critical_violations) * 1.5,
                    estimated_timeline_days=2,
                    confidence_percentage=95.0,
                )
            )

        # Insight 2: Overdue inspection
        if days_since_last_inspection > self.INSPECTION_OVERDUE_THRESHOLD_DAYS:
            insights.append(
                ComplianceRiskInsight(
                    project_id=project_id,
                    insight_type="inspection_overdue",
                    severity="high",
                    description=f"Site inspection overdue by {days_since_last_inspection - self.INSPECTION_OVERDUE_THRESHOLD_DAYS} days",
                    recommended_actions=[
                        "Schedule safety inspection immediately",
                        "Prepare inspection checklist and documentation",
                        "Ensure all personnel complete required safety training",
                        "Walk-through site to identify potential issues before inspection",
                    ],
                    estimated_timeline_days=7,
                    confidence_percentage=100.0,
                )
            )

        # Insight 3: Shutdown risk
        if shutdown_score > 0.5:
            insights.append(
                ComplianceRiskInsight(
                    project_id=project_id,
                    insight_type="shutdown_risk",
                    severity="critical",
                    description=f"High probability of project shutdown due to compliance violations (risk: {shutdown_score:.1%})",
                    recommended_actions=[
                        "Escalate to project leadership",
                        "Engage compliance consultant",
                        "Prepare voluntary disclosure to regulatory agency",
                        "Implement comprehensive remediation plan within 30 days",
                        "Brief insurance carrier",
                    ],
                    estimated_cost_to_remediate=sum(v.fine_amount_usd for v in active_violations) * 2.0,
                    estimated_timeline_days=30,
                    confidence_percentage=90.0,
                )
            )

        # Insight 4: Citation risk from pattern
        repeat_violations = [v for v in active_violations if v.citation_issued]
        if len(active_violations) > 3 or len(repeat_violations) > 1:
            insights.append(
                ComplianceRiskInsight(
                    project_id=project_id,
                    insight_type="citation_likely",
                    severity="high",
                    description=f"Pattern of {'repeat ' if len(repeat_violations) > 1 else ''}violations suggests citations likely in next inspection",
                    recommended_actions=[
                        "Conduct comprehensive site audit",
                        "Develop preventive compliance program",
                        "Assign compliance manager to site",
                        "Implement weekly safety audits",
                    ],
                    estimated_timeline_days=14,
                    confidence_percentage=85.0,
                )
            )

        return insights

    def generate_health_summary(
        self,
        project_id: str,
        project_name: str,
        inspections: List[SafetyInspection],
        violations: List[ComplianceViolation],
    ) -> ComplianceHealthSummary:
        """
        Generate compliance health summary for a project.

        Args:
            project_id: Project identifier
            project_name: Project name
            inspections: List of historical inspections
            violations: List of all violations (active and resolved)

        Returns:
            ComplianceHealthSummary with scores and classification
        """
        today = datetime.now().date()

        # Inspection metrics
        total_inspections = len(inspections)
        passed_inspections = sum(1 for i in inspections if i.status == InspectionStatus.PASSED)
        failed_inspections = total_inspections - passed_inspections

        # Get last inspection date
        last_inspection_date = None
        days_since_inspection = 999
        if inspections:
            sorted_inspections = sorted(inspections, key=lambda i: i.inspection_date, reverse=True)
            if sorted_inspections:
                last_inspection_date = sorted_inspections[0].inspection_date
                try:
                    insp_date = datetime.fromisoformat(last_inspection_date).date()
                    days_since_inspection = (today - insp_date).days
                except:
                    pass

        # Violation metrics
        active_violations = [v for v in violations if not v.mitigation_completed]
        resolved_violations = [v for v in violations if v.mitigation_completed]
        active_count = len(active_violations)
        resolved_count = len(resolved_violations)
        total_violations = len(violations)

        # Get most recent violation date
        days_since_last_violation = None
        if violations:
            sorted_violations = sorted(violations, key=lambda v: v.violation_date, reverse=True)
            if sorted_violations:
                try:
                    viol_date = datetime.fromisoformat(sorted_violations[0].violation_date).date()
                    days_since_last_violation = (today - viol_date).days
                except:
                    pass

        # Calculate scores
        compliance_score = self.calculate_violation_risk_score(
            active_violations, total_violations - active_count, days_since_last_violation
        )

        critical_violations = sum(1 for v in active_violations if v.severity == ViolationSeverity.CRITICAL)
        serious_violations = sum(1 for v in active_violations if v.severity == ViolationSeverity.SERIOUS)
        unresolved_citations = sum(1 for v in active_violations if v.citation_issued)

        shutdown_score = self.calculate_shutdown_risk_score(
            critical_violations=critical_violations,
            serious_violations=serious_violations,
            total_violations=active_count,
            days_since_last_inspection=days_since_inspection,
            has_failed_recent_inspection=failed_inspections > 0 and days_since_inspection <= 30,
            unresolved_citations=unresolved_citations,
        )

        # Estimate fine exposure
        estimated_fines = sum(v.fine_amount_usd for v in active_violations)

        # Generate explanation
        explanation = self._generate_health_explanation(
            compliance_score, shutdown_score, active_count, critical_violations
        )

        return ComplianceHealthSummary(
            project_id=project_id,
            project_name=project_name,
            last_inspection_date=last_inspection_date,
            total_inspections=total_inspections,
            inspections_passed=passed_inspections,
            inspections_failed=failed_inspections,
            active_violations=active_count,
            resolved_violations=resolved_count,
            total_violations_ever=total_violations,
            compliance_risk_score=compliance_score,
            compliance_risk_level=self.score_to_risk_level(compliance_score),
            shutdown_risk_score=shutdown_score,
            shutdown_risk_level=self.score_to_shutdown_level(shutdown_score),
            estimated_fine_exposure_usd=estimated_fines,
            days_since_last_inspection=days_since_inspection,
            explanation=explanation,
            generated_at=datetime.now().isoformat(),
        )

    def _generate_health_explanation(
        self, compliance_score: float, shutdown_score: float, active_violations: int, critical_count: int
    ) -> str:
        """Generate human-readable explanation of compliance health"""
        parts = []

        if critical_count > 0:
            parts.append(f"⚠️ {critical_count} CRITICAL violation(s) demanding immediate action.")

        if active_violations == 0:
            parts.append("✅ Currently compliant with no active violations.")
        elif active_violations == 1:
            parts.append("⚠️ 1 active violation requiring remediation.")
        else:
            parts.append(f"⚠️ {active_violations} active violation(s) requiring remediation.")

        if compliance_score < 0.25:
            parts.append("Good: Compliance profile is solid.")
        elif compliance_score < 0.50:
            parts.append("Fair: Compliance improvements recommended.")
        elif compliance_score < 0.75:
            parts.append("Poor: Significant compliance concerns present.")
        else:
            parts.append("Critical: Serious compliance issues require urgent attention.")

        if shutdown_score > 0.50:
            parts.append(f"🚨 Shutdown risk is HIGH ({shutdown_score:.0%}).")

        return " ".join(parts)

    def generate_intelligence(
        self,
        project_id: str,
        project_name: str,
        inspections: List[SafetyInspection],
        violations: List[ComplianceViolation],
    ) -> ComplianceIntelligence:
        """
        Generate comprehensive compliance intelligence for a project.

        Args:
            project_id: Project identifier
            project_name: Project name
            inspections: List of safety inspections
            violations: List of violations

        Returns:
            ComplianceIntelligence with full analysis and recommendations
        """
        active_violations = [v for v in violations if not v.mitigation_completed]

        # Generate health summary
        health_summary = self.generate_health_summary(project_id, project_name, inspections, violations)

        # Generate insights
        insights = self.generate_compliance_insights(
            project_id,
            active_violations,
            health_summary.days_since_last_inspection,
            health_summary.compliance_risk_score,
            health_summary.shutdown_risk_score,
        )

        # Generate project summary
        project_summary = self._generate_project_summary(
            project_name,
            health_summary.compliance_risk_level,
            health_summary.shutdown_risk_level,
            len(active_violations),
        )

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(
            health_summary.compliance_risk_score,
            health_summary.shutdown_risk_score,
            len([v for v in active_violations if v.severity == ViolationSeverity.CRITICAL]),
            health_summary.days_since_last_inspection,
        )

        # Prepare monday.com updates
        monday_updates = {
            "Compliance Risk": health_summary.compliance_risk_level.value.upper(),
            "Shutdown Risk": health_summary.shutdown_risk_level.value.upper(),
            "Active Violations": str(len(active_violations)),
            "Last Inspection": health_summary.last_inspection_date or "Never",
            "Fine Exposure": f"${health_summary.estimated_fine_exposure_usd:,.2f}",
        }

        return ComplianceIntelligence(
            project_id=project_id,
            project_name=project_name,
            compliance_health_summary=health_summary,
            compliance_risk_insights=insights,
            active_violations=active_violations,
            pending_inspections=sum(1 for i in inspections if i.status == InspectionStatus.PENDING),
            compliance_risk_score=health_summary.compliance_risk_score,
            shutdown_risk_score=health_summary.shutdown_risk_score,
            project_summary=project_summary,
            critical_violation_count=sum(
                1 for v in active_violations if v.severity == ViolationSeverity.CRITICAL
            ),
            estimated_total_fine_exposure=health_summary.estimated_fine_exposure_usd,
            audit_ready_status=health_summary.compliance_risk_score < 0.50,
            recommended_immediate_actions=recommended_actions,
            integration_ready=True,
            generated_at=datetime.now().isoformat(),
            monday_updates=monday_updates,
        )

    def _generate_project_summary(
        self, project_name: str, risk_level: ComplianceRiskLevel, shutdown_level: ShutdownRiskLevel, violation_count: int
    ) -> str:
        """Generate human-readable project compliance summary"""
        return (
            f"{project_name}: Compliance Risk {risk_level.value.title()}, "
            f"Shutdown Risk {shutdown_level.value.title()}, "
            f"{violation_count} active violation{'s' if violation_count != 1 else ''}."
        )

    def _generate_recommended_actions(
        self, compliance_score: float, shutdown_score: float, critical_count: int, days_since_inspection: int
    ) -> List[str]:
        """Generate list of recommended immediate actions"""
        actions = []

        if critical_count > 0:
            actions.append("🔴 URGENT: Address all critical violations immediately")

        if shutdown_score > 0.65:
            actions.append("Escalate to executive leadership and legal counsel")

        if days_since_inspection > 90:
            actions.append("Schedule safety inspection within 7 days")

        if compliance_score > 0.50:
            actions.append("Engage external compliance consultant for audit")

        if not actions:
            actions.append("Continue routine compliance monitoring and inspections")

        return actions

    def generate_audit_report(
        self,
        project_id: str,
        project_name: str,
        period_start: str,
        period_end: str,
        inspections: List[SafetyInspection],
        violations: List[ComplianceViolation],
    ) -> AuditReport:
        """
        Generate audit-ready compliance report.

        Args:
            project_id: Project identifier
            project_name: Project name
            period_start: ISO date string
            period_end: ISO date string
            inspections: Inspections in period
            violations: Violations in period

        Returns:
            AuditReport for compliance/regulatory review
        """
        total_inspections = len(inspections)
        total_violations = len(violations)

        # Count by severity
        by_severity = {}
        for severity in ViolationSeverity:
            count = sum(1 for v in violations if v.severity == severity)
            by_severity[severity.value] = count

        # Critical findings
        critical_findings = [
            f"Critical Violation: {v.regulation_name} - {v.description[:100]}"
            for v in violations
            if v.severity == ViolationSeverity.CRITICAL
        ]

        # Corrective actions
        corrective_actions_required = sum(1 for v in violations if v.mitigation_required)
        corrective_actions_completed = sum(1 for v in violations if v.mitigation_completed)

        # Financial exposure
        estimated_exposure = sum(v.fine_amount_usd for v in violations)

        # Determine compliance status
        if total_violations == 0:
            compliance_status = "in_compliance"
        elif total_violations <= 2:
            compliance_status = "at_risk"
        else:
            compliance_status = "non_compliant"

        # Executive summary
        executive_summary = (
            f"During the period {period_start} to {period_end}, {total_inspections} inspection(s) "
            f"were conducted discovering {total_violations} violation(s). "
            f"Project is currently {compliance_status}. "
            f"Estimated financial exposure: ${estimated_exposure:,.2f}."
        )

        return AuditReport(
            report_id=f"audit_{project_id}_{datetime.now().isoformat()}",
            project_id=project_id,
            project_name=project_name,
            report_date=datetime.now().isoformat(),
            period_start_date=period_start,
            period_end_date=period_end,
            total_inspections=total_inspections,
            total_violations=total_violations,
            by_severity=by_severity,
            critical_findings=critical_findings,
            corrective_actions_required=corrective_actions_required,
            corrective_actions_completed=corrective_actions_completed,
            estimated_financial_exposure=estimated_exposure,
            compliance_status=compliance_status,
            executive_summary=executive_summary,
            recommendations=[
                "Implement comprehensive compliance monitoring program",
                "Provide ongoing safety training to all personnel",
                "Conduct monthly internal audits against applicable regulations",
                "Maintain detailed compliance documentation for regulatory review",
            ],
        )
