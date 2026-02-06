"""Phase 20 - Workforce Reliability Analyzer

Analyzes worker attendance patterns, computes reliability scores, and quantifies
schedule/cost impacts. Integrates with Phase 9 risk synthesis.

Demo mode: Uses synthetic attendance data.
Production mode: Integrates with HR/timesheet systems (future).
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from pathlib import Path

from phase20_workforce_types import (
    AttendanceRecord,
    WorkerReliabilityScore,
    WorkforceImpactFactors,
    ProjectWorkforceIntelligence,
)


class WorkforceReliabilityAnalyzer:
    """Analyzes workforce attendance and reliability patterns."""
    
    def __init__(self, lookback_days: int = 90):
        """Initialize analyzer.
        
        Args:
            lookback_days: Number of days to consider for historical patterns
        """
        self.lookback_days = lookback_days
    
    def calculate_worker_reliability(
        self,
        worker_id: str,
        worker_name: str,
        role: str,
        attendance_records: List[AttendanceRecord],
    ) -> WorkerReliabilityScore:
        """Calculate reliability score for a single worker.
        
        Args:
            worker_id: Unique worker identifier
            worker_name: Worker's name
            role: Job role/title
            attendance_records: List of attendance events (sorted by date, most recent last)
        
        Returns:
            WorkerReliabilityScore with metrics and explanations
        """
        if not attendance_records:
            # Default: unknown worker (neutral score)
            return WorkerReliabilityScore(
                worker_id=worker_id,
                worker_name=worker_name,
                role=role,
                total_days=0,
                present_days=0,
                absent_days=0,
                late_days=0,
                early_departure_days=0,
                inspection_miss_count=0,
                attendance_rate=0.5,
                punctuality_rate=0.5,
                reliability_score=0.5,
                repeat_no_show=False,
                chronic_lateness=False,
                inspection_risk=False,
                declining_trend=False,
                risk_level='medium',
                explanation="Insufficient attendance data.",
            )
        
        # Count events
        total_events = len(attendance_records)
        present_count = sum(1 for r in attendance_records if r.event_type == 'present')
        late_count = sum(1 for r in attendance_records if r.event_type == 'late')
        absent_count = sum(1 for r in attendance_records if r.event_type == 'absent')
        early_dep_count = sum(1 for r in attendance_records if r.event_type == 'early_departure')
        inspection_miss_count = sum(1 for r in attendance_records if r.event_type == 'inspection_miss')
        
        # Derived metrics
        attendance_rate = (present_count + late_count * 0.8) / max(1, total_events)
        punctuality_rate = present_count / max(1, total_events)
        
        # Composite reliability (0-1): weighted average
        # - Attendance (60%): were they there?
        # - Punctuality (30%): were they on time?
        # - Inspection compliance (10%): did they attend inspections?
        inspection_compliance = max(0, 1.0 - (inspection_miss_count / max(1, total_events) * 2))
        reliability_score = (
            attendance_rate * 0.60 +
            punctuality_rate * 0.30 +
            inspection_compliance * 0.10
        )
        
        # Pattern detection: last 30 days
        cutoff_date = attendance_records[-1].date if attendance_records[-1].date else datetime.now().isoformat()
        try:
            cutoff = datetime.fromisoformat(cutoff_date) - timedelta(days=30)
        except:
            cutoff = None
        
        recent = [
            r for r in attendance_records
            if cutoff is None or datetime.fromisoformat(r.date) >= cutoff
        ]
        
        recent_absent = sum(1 for r in recent if r.event_type == 'absent')
        recent_late = sum(1 for r in recent if r.event_type == 'late')
        
        repeat_no_show = recent_absent >= 3
        chronic_lateness = recent_late >= 5
        inspection_risk = inspection_miss_count > 0
        
        # Trend detection: compare first half vs second half of lookback period
        mid = len(attendance_records) // 2
        first_half = attendance_records[:mid]
        second_half = attendance_records[mid:]
        
        first_score = sum(1 for r in first_half if r.event_type == 'present') / max(1, len(first_half))
        second_score = sum(1 for r in second_half if r.event_type == 'present') / max(1, len(second_half))
        declining_trend = second_score < (first_score - 0.15)
        
        # Risk level
        if reliability_score >= 0.85 and not repeat_no_show and not chronic_lateness:
            risk_level = 'low'
        elif reliability_score < 0.60 or repeat_no_show or chronic_lateness:
            risk_level = 'high'
        else:
            risk_level = 'medium'
        
        # Explanation
        explanation_parts = []
        explanation_parts.append(f"{worker_name} ({role}): {present_count}/{total_events} present, {late_count} late, {absent_count} absent.")
        
        if repeat_no_show:
            explanation_parts.append("⚠️ Repeat no-show risk: 3+ absences in last 30 days.")
        if chronic_lateness:
            explanation_parts.append("⚠️ Chronic lateness: 5+ late arrivals in last 30 days.")
        if inspection_risk:
            explanation_parts.append("⚠️ Inspection compliance risk: missed inspection(s).")
        if declining_trend:
            explanation_parts.append("⚠️ Declining trend: attendance worsening over time.")
        
        if reliability_score >= 0.85:
            explanation_parts.append("✓ Highly reliable worker.")
        elif reliability_score >= 0.70:
            explanation_parts.append("• Moderately reliable; monitor for patterns.")
        else:
            explanation_parts.append("⚠️ Low reliability; recommend intervention.")
        
        explanation = " ".join(explanation_parts)
        
        return WorkerReliabilityScore(
            worker_id=worker_id,
            worker_name=worker_name,
            role=role,
            total_days=total_events,
            present_days=present_count,
            absent_days=absent_count,
            late_days=late_count,
            early_departure_days=early_dep_count,
            inspection_miss_count=inspection_miss_count,
            attendance_rate=attendance_rate,
            punctuality_rate=punctuality_rate,
            reliability_score=reliability_score,
            repeat_no_show=repeat_no_show,
            chronic_lateness=chronic_lateness,
            inspection_risk=inspection_risk,
            declining_trend=declining_trend,
            risk_level=risk_level,
            explanation=explanation,
        )
    
    def estimate_schedule_impact(
        self,
        worker_scores: List[WorkerReliabilityScore],
        project_workers_by_role: Dict[str, int],
    ) -> WorkforceImpactFactors:
        """Estimate schedule and cost impacts from workforce reliability.
        
        Args:
            worker_scores: List of reliability scores
            project_workers_by_role: Mapping of role -> count (project composition)
        
        Returns:
            WorkforceImpactFactors with quantified impacts
        """
        # Identify critical roles at risk
        critical_roles_at_risk = []
        high_risk_count = sum(1 for s in worker_scores if s.risk_level == 'high')
        
        role_risk_map = {}
        for score in worker_scores:
            if score.role not in role_risk_map:
                role_risk_map[score.role] = []
            role_risk_map[score.role].append(score.reliability_score)
        
        for role, scores in role_risk_map.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.70:
                critical_roles_at_risk.append(role)
        
        # Estimate schedule slippage (days)
        # Heuristic: 1 day slippage per high-risk worker (represents productivity loss, rework, etc.)
        estimated_slippage = high_risk_count * 1.5
        
        # Productivity loss factor (0-1 multiplier)
        # Average team reliability score → maps to productivity loss
        if worker_scores:
            avg_reliability = sum(s.reliability_score for s in worker_scores) / len(worker_scores)
        else:
            avg_reliability = 0.8
        
        productivity_loss_factor = max(0, 1.0 - avg_reliability)
        
        # Overtime acceleration (days needed to recover lost productivity)
        overtime_acceleration = estimated_slippage * 0.5
        
        # Rework risk multiplier (baseline 1.0)
        # Low reliability → more rework
        rework_risk_multiplier = 1.0 + (productivity_loss_factor * 0.3)
        
        # Inspection delays (if missing inspections)
        inspection_miss_count = sum(s.inspection_miss_count for s in worker_scores)
        inspection_delays = inspection_miss_count * 2  # 2 days per missed inspection
        
        # Regulatory risk (likelihood inspection will fail due to staffing absences)
        absent_count = sum(s.absent_days for s in worker_scores)
        total_days = sum(s.total_days for s in worker_scores) if worker_scores else 1
        absent_pct = absent_count / max(1, total_days)
        regulatory_no_show_risk_pct = min(100, absent_pct * 100)
        
        # Detailed risk narrative
        detailed_risks = []
        if high_risk_count > 0:
            detailed_risks.append(f"{high_risk_count} workers at high attendance risk.")
        if critical_roles_at_risk:
            detailed_risks.append(f"Critical roles at risk: {', '.join(critical_roles_at_risk)}.")
        if inspection_miss_count > 0:
            detailed_risks.append(f"Inspection compliance risk: {inspection_miss_count} missed inspection(s).")
        
        # Recommended actions
        recommended_actions = []
        if high_risk_count > 1:
            recommended_actions.append("Increase management oversight for high-risk workers.")
        if critical_roles_at_risk:
            recommended_actions.append(f"Cross-train backups for {', '.join(critical_roles_at_risk)}.")
        if inspection_miss_count > 0:
            recommended_actions.append("Mandatory inspection attendance going forward; link to performance reviews.")
        if absent_pct > 0.10:
            recommended_actions.append("Implement stricter absence tracking and escalation protocols.")
        
        return WorkforceImpactFactors(
            project_id="",  # Will be set by caller
            analysis_datetime=datetime.now().isoformat(),
            critical_roles_at_risk=critical_roles_at_risk,
            estimated_schedule_slippage_days=estimated_slippage,
            productivity_loss_factor=min(1.0, productivity_loss_factor),
            overtime_acceleration_estimate=overtime_acceleration,
            rework_risk_multiplier=rework_risk_multiplier,
            inspection_delays_days=inspection_delays,
            regulatory_no_show_risk_pct=regulatory_no_show_risk_pct,
            detailed_risks=detailed_risks if detailed_risks else ["No major workforce risks detected."],
            recommended_staffing_actions=recommended_actions if recommended_actions else ["Continue monitoring; no immediate action needed."],
        )
    
    def project_workforce_intelligence(
        self,
        project_id: str,
        worker_scores: List[WorkerReliabilityScore],
        impact_factors: WorkforceImpactFactors,
    ) -> ProjectWorkforceIntelligence:
        """Synthesize project-level workforce intelligence.
        
        Args:
            project_id: Project identifier
            worker_scores: List of worker reliability scores
            impact_factors: Schedule/cost impact estimates
        
        Returns:
            ProjectWorkforceIntelligence with synthesis and recommendations
        """
        # Count workers by risk level
        high_risk = sum(1 for s in worker_scores if s.risk_level == 'high')
        medium_risk = sum(1 for s in worker_scores if s.risk_level == 'medium')
        low_risk = sum(1 for s in worker_scores if s.risk_level == 'low')
        
        # Team reliability score (weighted average)
        if worker_scores:
            team_reliability = sum(s.reliability_score for s in worker_scores) / len(worker_scores)
        else:
            team_reliability = 0.7  # Unknown
        
        # Workforce risk contribution to overall project (estimate)
        # Heuristic: each point below 0.8 contributes ~5% to overall risk
        workforce_risk_contribution_pct = max(0, min(100, (1.0 - team_reliability) * 50))
        
        # Summary
        summary_parts = []
        if low_risk > 0:
            summary_parts.append(f"✓ {low_risk} highly reliable worker(s)")
        if medium_risk > 0:
            summary_parts.append(f"• {medium_risk} moderately reliable worker(s)")
        if high_risk > 0:
            summary_parts.append(f"⚠️ {high_risk} at-risk worker(s)")
        
        summary_parts.append(f"Team reliability: {team_reliability:.0%}")
        summary_parts.append(f"Est. schedule impact: +{impact_factors.estimated_schedule_slippage_days:.1f} days")
        
        summary = " | ".join(summary_parts)
        
        # Confidence level based on data volume
        if len(worker_scores) >= 5:
            confidence = 'high'
        elif len(worker_scores) >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return ProjectWorkforceIntelligence(
            project_id=project_id,
            analysis_datetime=datetime.now().isoformat(),
            total_workers=len(worker_scores),
            workers_by_role={},  # Caller can populate
            team_reliability_score=team_reliability,
            high_risk_worker_count=high_risk,
            medium_risk_worker_count=medium_risk,
            low_risk_worker_count=low_risk,
            workforce_risk_contribution_pct=workforce_risk_contribution_pct,
            impact_factors=impact_factors,
            summary=summary,
            confidence=confidence,
        )
