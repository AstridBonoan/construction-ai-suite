"""
Phase 19: Subcontractor Performance Analyzer

Provides scoring, pattern detection, and project-level aggregation for
subcontractor performance intelligence.
"""
import logging
from typing import Dict, List
from datetime import datetime
from phase19_subcontractor_types import (
    Subcontractor, SubcontractorPerformanceRecord, SubcontractorSummary,
    SubcontractorRiskInsight, SubcontractorProjectSummary, SubcontractorIntelligence
)

logger = logging.getLogger(__name__)


class SubcontractorPerformanceAnalyzer:
    def __init__(self):
        self.subcontractors: Dict[str, Subcontractor] = {}
        self.records: List[SubcontractorPerformanceRecord] = []

    def add_subcontractor(self, sub: Subcontractor) -> None:
        self.subcontractors[sub.subcontractor_id] = sub
        logger.info(f"Added subcontractor {sub.subcontractor_id}")

    def add_record(self, rec: SubcontractorPerformanceRecord) -> None:
        self.records.append(rec)

    def add_records(self, recs: List[SubcontractorPerformanceRecord]) -> None:
        self.records.extend(recs)

    def calculate_subcontractor_summary(self, subcontractor_id: str) -> SubcontractorSummary:
        sub = self.subcontractors.get(subcontractor_id)
        name = sub.name if sub else "Unknown"
        recs = [r for r in self.records if r.subcontractor_id == subcontractor_id]

        if not recs:
            return SubcontractorSummary(subcontractor_id=subcontractor_id, subcontractor_name=name,
                                        explanation="No performance records")

        total = len(recs)
        late = sum(1 for r in recs if r.days_delay > 0)
        on_time = sum(1 for r in recs if r.days_delay <= 0 and r.completed)
        avg_delay = sum(r.days_delay for r in recs) / total
        quality_issues = sum(r.quality_issues for r in recs)

        # Reliability score: penalize late deliveries and quality issues deterministically
        late_rate = late / total
        quality_penalty = min(1.0, quality_issues / max(1, total))
        reliability = max(0.0, 1.0 - (late_rate * 0.6) - (quality_penalty * 0.3) - (max(0, avg_delay) / 30 * 0.1))

        # Risk level heuristics
        if reliability < 0.4:
            risk = "high"
        elif reliability < 0.7:
            risk = "medium"
        else:
            risk = "low"

        explanation = (f"{name}: {on_time}/{total} on-time, {late} late, avg delay {avg_delay:.2f} days;"
                       f" quality issues {quality_issues}.")

        return SubcontractorSummary(
            subcontractor_id=subcontractor_id,
            subcontractor_name=name,
            total_tasks=total,
            on_time_count=on_time,
            late_count=late,
            avg_days_delay=avg_delay,
            quality_issues=quality_issues,
            reliability_score=reliability,
            risk_level=risk,
            explanation=explanation
        )

    def identify_risk_insights(self, project_id: str) -> List[SubcontractorRiskInsight]:
        insights: List[SubcontractorRiskInsight] = []
        project_recs = [r for r in self.records if r.project_id == project_id]
        subs = set(r.subcontractor_id for r in project_recs)

        for sid in subs:
            summary = self.calculate_subcontractor_summary(sid)
            if summary.reliability_score < 0.5:
                insights.append(SubcontractorRiskInsight(
                    subcontractor_id=sid,
                    project_id=project_id,
                    identified_issue="repeated_delays",
                    severity="high",
                    impact_on_schedule=f"Estimated { (1-summary.reliability_score)*10 :.1f } day(s) delay",
                    impact_on_cost=f"Estimated ${ (1-summary.reliability_score)*2000 :.0f }",
                    confidence=0.8,
                    recommendation="Consider backup vendors or add schedule buffer",
                    monday_column_suggestion="Subcontractor_Risk_Flag"
                ))

        return insights

    def create_project_intelligence(self, project_id: str, project_name: str, subcontractor_ids: List[str]) -> SubcontractorIntelligence:
        subs = {sid: self.calculate_subcontractor_summary(sid) for sid in subcontractor_ids}
        insights = self.identify_risk_insights(project_id)

        avg_reliability = (sum(s.reliability_score for s in subs.values()) / len(subs)) if subs else 1.0
        high_risk = [sid for sid, s in subs.items() if s.risk_level == "high"]

        total_schedule_impact = sum((1 - s.reliability_score) * 5 for s in subs.values())
        total_cost_impact = sum((1 - s.reliability_score) * 3000 for s in subs.values())

        key_insights = []
        if high_risk:
            key_insights.append(f"{len(high_risk)} high-risk subcontractor(s) detected")
        if total_schedule_impact > 0:
            key_insights.append(f"Estimated schedule impact: {total_schedule_impact:.1f} days")

        recommendations = []
        if high_risk:
            recommendations.append("Identify backups for high-risk subcontractors")
        if total_schedule_impact > 5:
            recommendations.append("Add schedule contingency")

        project_summary = SubcontractorProjectSummary(
            project_id=project_id,
            project_name=project_name,
            total_subcontractors=len(subs),
            avg_reliability_score=avg_reliability,
            high_risk_subcontractors=high_risk,
            estimated_schedule_impact_days=total_schedule_impact,
            estimated_cost_impact=total_cost_impact,
            key_insights=key_insights,
            recommendations=recommendations,
            explanation=(f"Project {project_name}: {len(subs)} subcontractors. Avg reliability {avg_reliability:.2f}.")
        )

        intelligence = SubcontractorIntelligence(
            project_id=project_id,
            project_name=project_name,
            generated_at=datetime.utcnow().isoformat() + 'Z',
            subcontractor_summaries=subs,
            risk_insights=insights,
            project_summary=project_summary,
            subcontractor_risk_score=1.0 - avg_reliability,
            integration_ready=True
        )

        logger.info(f"Created subcontractor intelligence for {project_name}")
        return intelligence
