"""
Phase 20: Predictive Equipment Maintenance Analyzer

Implements failure risk scoring, pattern detection, and maintenance-driven
schedule/cost impact prediction.
"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from phase20_equipment_types import (
    Equipment, MaintenanceRecord, FailureEvent, EquipmentStatus,
    EquipmentHealthSummary, EquipmentRiskInsight, EquipmentProjectSummary,
    EquipmentIntelligence
)

logger = logging.getLogger(__name__)


class EquipmentMaintenanceAnalyzer:
    def __init__(self):
        self.equipment: Dict[str, Equipment] = {}
        self.maintenance_records: List[MaintenanceRecord] = []
        self.failure_events: List[FailureEvent] = []

    def add_equipment(self, eq: Equipment) -> None:
        self.equipment[eq.equipment_id] = eq
        logger.info(f"Added equipment {eq.equipment_id}: {eq.name}")

    def add_maintenance_record(self, rec: MaintenanceRecord) -> None:
        self.maintenance_records.append(rec)

    def add_failure_event(self, evt: FailureEvent) -> None:
        self.failure_events.append(evt)

    def calculate_equipment_health(self, equipment_id: str) -> EquipmentHealthSummary:
        eq = self.equipment.get(equipment_id)
        name = eq.name if eq else "Unknown"
        
        # Get all records for this equipment
        maint_recs = [r for r in self.maintenance_records if r.equipment_id == equipment_id]
        failure_evts = [e for e in self.failure_events if e.equipment_id == equipment_id]
        
        # Calculate basic metrics
        total_maint = len(maint_recs)
        total_failures = len(failure_evts)
        maint_cost = sum(r.cost for r in maint_recs)
        failure_cost = sum(e.repair_cost for e in failure_evts)
        
        # Estimate equipment age in days (from first record or defaults to 365)
        if maint_recs or failure_evts:
            dates = [r.maintenance_date for r in maint_recs] + [e.failure_date for e in failure_evts]
            oldest_date = min(dates)
            try:
                oldest = datetime.fromisoformat(oldest_date)
                age_days = (datetime.utcnow() - oldest).days
            except:
                age_days = 365.0
        else:
            age_days = 365.0
        
        # Average maintenance interval
        avg_interval = age_days / max(1, total_maint)
        
        # Days since last maintenance
        if maint_recs:
            try:
                last_maint_date = datetime.fromisoformat(max(r.maintenance_date for r in maint_recs))
                days_since_maint = (datetime.utcnow() - last_maint_date).days
            except:
                days_since_maint = 0.0
        else:
            days_since_maint = age_days
        
        # Failure probability: based on failure history and maintenance patterns
        # Higher failures + longer intervals = higher risk
        failure_rate = total_failures / max(1.0, age_days / 365)  # Failures per year
        overdue_factor = days_since_maint / max(1.0, avg_interval)
        
        # Probability: penalize overdue maintenance and past failures
        base_probability = min(1.0, failure_rate * 0.2)  # Past failures suggest future risk
        overdue_probability = min(1.0, overdue_factor * 0.1)  # Overdue maintenance increases risk
        failure_prob = min(1.0, base_probability + overdue_probability)
        
        # Risk level heuristics
        if failure_prob > 0.6:
            risk_level = "high"
        elif failure_prob > 0.3:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        explanation = (f"{name}: {total_maint} maintenance events, {total_failures} failures. "
                      f"Age: {age_days:.0f} days. Days since maint: {days_since_maint:.0f}. "
                      f"Failure probability: {failure_prob:.2%}.")
        
        return EquipmentHealthSummary(
            equipment_id=equipment_id,
            equipment_name=name,
            total_operational_days=age_days,
            total_maintenance_events=total_maint,
            total_failure_events=total_failures,
            average_maintenance_interval_days=avg_interval,
            days_since_last_maintenance=days_since_maint,
            maintenance_cost_total=maint_cost,
            failure_cost_total=failure_cost,
            failure_probability=failure_prob,
            risk_level=risk_level,
            explanation=explanation
        )
    
    def identify_risk_insights(self, project_id: str) -> List[EquipmentRiskInsight]:
        insights: List[EquipmentRiskInsight] = []
        
        # Find all equipment used in this project
        project_maint = set(r.equipment_id for r in self.maintenance_records if r.project_id == project_id)
        project_failures = set(e.equipment_id for e in self.failure_events if e.project_id == project_id)
        project_equipment = project_maint | project_failures
        
        for eq_id in project_equipment:
            health = self.calculate_equipment_health(eq_id)
            
            if health.failure_probability > 0.5:
                insights.append(EquipmentRiskInsight(
                    equipment_id=eq_id,
                    project_id=project_id,
                    identified_issue="high_failure_risk",
                    severity="high",
                    impact_on_schedule=f"Equipment has {health.failure_probability:.0%} failure probability; {(health.failure_probability * 5):.1f} day(s) expected downtime",
                    impact_on_cost=f"Estimated repair cost: ${health.failure_cost_total + (health.failure_probability * 2000):.0f}",
                    confidence=0.75,
                    recommendation="Schedule preventive maintenance or allocate backup equipment",
                    monday_column_suggestion="Equipment_Maintenance_Flag"
                ))
            elif health.days_since_last_maintenance > health.average_maintenance_interval_days * 1.2:
                insights.append(EquipmentRiskInsight(
                    equipment_id=eq_id,
                    project_id=project_id,
                    identified_issue="maintenance_overdue",
                    severity="medium",
                    impact_on_schedule=f"Maintenance overdue by {health.days_since_last_maintenance - health.average_maintenance_interval_days:.0f} days; potential 2-3 day delay",
                    impact_on_cost=f"Estimated maintenance cost: ${max(500, health.maintenance_cost_total / max(1, health.total_maintenance_events)):.0f}",
                    confidence=0.8,
                    recommendation="Schedule maintenance immediately",
                    monday_column_suggestion="Equipment_Maintenance_Alert"
                ))
        
        return insights
    
    def create_project_intelligence(
        self,
        project_id: str,
        project_name: str,
        equipment_ids: List[str]
    ) -> EquipmentIntelligence:
        # Generate health summaries for all equipment
        summaries = {eq_id: self.calculate_equipment_health(eq_id) for eq_id in equipment_ids}
        
        # Gather risk insights
        insights = self.identify_risk_insights(project_id)
        
        # Calculate project-level aggregations
        avg_failure_prob = (sum(s.failure_probability for s in summaries.values()) / len(summaries)) if summaries else 0.0
        high_risk = [eq_id for eq_id, s in summaries.items() if s.risk_level == "high"]
        
        total_downtime = sum(s.failure_probability * 5 for s in summaries.values())
        total_cost_impact = sum(s.failure_cost_total + (s.failure_probability * 2000) for s in summaries.values())
        
        key_insights = []
        if high_risk:
            key_insights.append(f"{len(high_risk)} equipment item(s) at high failure risk")
        if total_downtime > 0:
            key_insights.append(f"Estimated maintenance-driven downtime: {total_downtime:.1f} days")
        if avg_failure_prob > 0.4:
            key_insights.append("Equipment fleet reliability below acceptable threshold")
        
        recommendations = []
        if high_risk:
            recommendations.append("Prioritize maintenance for high-risk equipment")
        if total_downtime > 3:
            recommendations.append("Allocate schedule buffer for equipment maintenance")
        if avg_failure_prob > 0.5:
            recommendations.append("Conduct full equipment audit and preventive maintenance review")
        
        project_summary = EquipmentProjectSummary(
            project_id=project_id,
            project_name=project_name,
            total_equipment=len(equipment_ids),
            avg_failure_probability=avg_failure_prob,
            high_risk_equipment=high_risk,
            estimated_maintenance_downtime_days=total_downtime,
            estimated_maintenance_cost=total_cost_impact,
            key_insights=key_insights,
            recommendations=recommendations,
            explanation=(f"Project {project_name}: {len(equipment_ids)} equipment items. "
                        f"Avg failure probability {avg_failure_prob:.2%}. "
                        f"Est. downtime {total_downtime:.1f} days, cost impact ${total_cost_impact:.0f}.")
        )
        
        intelligence = EquipmentIntelligence(
            project_id=project_id,
            project_name=project_name,
            generated_at=datetime.utcnow().isoformat() + 'Z',
            equipment_summaries=summaries,
            risk_insights=insights[:10],  # Top 10 insights
            project_summary=project_summary,
            equipment_risk_score=avg_failure_prob,
            integration_ready=True
        )
        
        logger.info(f"Created equipment intelligence for {project_name}: risk_score={avg_failure_prob:.2f}")
        return intelligence
