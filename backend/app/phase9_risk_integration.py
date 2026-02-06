"""
Feature 9: Integration with Core Risk Engine (Feature 1)
Bridges synthesized multi-factor risks back into project-level risk management
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import logging

from phase9_risk_types import (
    MultiFactorRiskInput,
    SynthesizedRiskOutput,
    RiskFactorInput,
    RiskCategory,
    RiskAlert,
    RiskSeverity,
)
from phase9_risk_aggregator import MultiFactorRiskAggregator

logger = logging.getLogger(__name__)


class Feature9Integration:
    """
    Manages Feature 9 synthesis within the broader Feature 1 architecture.
    
    Responsibilities:
    - Accept risk inputs from Features 1-8
    - Coordinate multi-factor synthesis
    - Feed results back to Feature 1 for holistic project risk
    - Manage risk propagation through task dependencies
    - Generate alerts when risks exceed thresholds
    """

    def __init__(self, project_id: str):
        """Initialize integration for a project"""
        self.project_id = project_id
        self.aggregator = MultiFactorRiskAggregator()
        self.synthesis_cache: Dict[str, SynthesizedRiskOutput] = {}
        self.alert_history: List[RiskAlert] = []
        self.propagation_paths: Dict[str, List] = {}
        self.threshold_config = {
            "overall_risk_critical": 0.75,
            "overall_risk_high": 0.50,
            "interaction_threshold": 0.60,  # When to alert on interactions
        }

    def register_feature_risks(
        self,
        cost_risk: Optional[RiskFactorInput] = None,
        schedule_risk: Optional[RiskFactorInput] = None,
        workforce_risk: Optional[RiskFactorInput] = None,
        subcontractor_risk: Optional[RiskFactorInput] = None,
        equipment_risk: Optional[RiskFactorInput] = None,
        materials_risk: Optional[RiskFactorInput] = None,
        compliance_risk: Optional[RiskFactorInput] = None,
        environmental_risk: Optional[RiskFactorInput] = None,
        task_id: Optional[str] = None,
        project_phase: str = "execution",
        criticality: str = "medium",
        dependencies_count: int = 0,
    ) -> SynthesizedRiskOutput:
        """
        Register risk inputs from Features 1-8 and synthesize.
        
        Args:
            cost_risk: From Feature 1
            schedule_risk: From Feature 2
            workforce_risk: From Feature 3
            subcontractor_risk: From Feature 4
            equipment_risk: From Feature 5
            materials_risk: From Feature 6
            compliance_risk: From Feature 7
            environmental_risk: From Feature 8
            task_id: Optional task-level synthesis
            project_phase: planning, execution, or closing
            criticality: low, medium, high, or critical
            dependencies_count: Number of task dependencies
            
        Returns:
            SynthesizedRiskOutput with complete synthesis
        """
        # Build multi-factor input
        multi_factor_input = MultiFactorRiskInput(
            project_id=self.project_id,
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            cost_risk=cost_risk,
            schedule_risk=schedule_risk,
            workforce_risk=workforce_risk,
            subcontractor_risk=subcontractor_risk,
            equipment_risk=equipment_risk,
            materials_risk=materials_risk,
            compliance_risk=compliance_risk,
            environmental_risk=environmental_risk,
            project_phase=project_phase,
            criticality=criticality,
            dependencies_count=dependencies_count,
        )

        # Synthesize
        synthesis = self.aggregator.synthesize(multi_factor_input)

        # Cache
        cache_key = task_id or self.project_id
        self.synthesis_cache[cache_key] = synthesis

        # Check for alerts
        self._check_alert_conditions(synthesis)

        # Model propagation
        if task_id:
            self._model_risk_propagation(synthesis)

        return synthesis

    def get_core_engine_input(self, task_id: Optional[str] = None) -> Dict[str, any]:
        """
        Prepare Feature 9 output for Feature 1 (Core Risk Engine).
        
        This is the primary integration point. The core engine will use this
        data along with its own calculations to determine final project risk.
        
        Args:
            task_id: Get synthesis for specific task (or project-level if None)
            
        Returns:
            Dictionary formatted for core engine consumption
        """
        cache_key = task_id or self.project_id
        synthesis = self.synthesis_cache.get(cache_key)

        if not synthesis:
            return self._get_default_output()

        return {
            # Primary synthesized metric
            "feature9_overall_risk": synthesis.overall_risk_score,
            "feature9_risk_severity": synthesis.overall_severity.value,
            "feature9_confidence": synthesis.overall_confidence,
            
            # Component metrics
            "feature9_cost_risk": synthesis.cost_risk_metric.score if synthesis.cost_risk_metric else None,
            "feature9_schedule_risk": synthesis.schedule_risk_metric.score if synthesis.schedule_risk_metric else None,
            "feature9_workforce_risk": synthesis.workforce_risk_metric.score if synthesis.workforce_risk_metric else None,
            "feature9_subcontractor_risk": synthesis.subcontractor_risk_metric.score if synthesis.subcontractor_risk_metric else None,
            "feature9_equipment_risk": synthesis.equipment_risk_metric.score if synthesis.equipment_risk_metric else None,
            "feature9_materials_risk": synthesis.materials_risk_metric.score if synthesis.materials_risk_metric else None,
            "feature9_compliance_risk": synthesis.compliance_risk_metric.score if synthesis.compliance_risk_metric else None,
            "feature9_environmental_risk": synthesis.environmental_risk_metric.score if synthesis.environmental_risk_metric else None,
            
            # Driver information
            "feature9_primary_drivers": synthesis.primary_risk_drivers,
            "feature9_secondary_drivers": synthesis.secondary_risk_drivers,
            "feature9_key_interdependencies": synthesis.key_interdependencies,
            
            # Actionable intelligence
            "feature9_executive_summary": synthesis.executive_summary,
            "feature9_mitigation_plan": synthesis.risk_mitigation_plan,
            "feature9_short_term_outlook": synthesis.short_term_outlook,
            "feature9_medium_term_outlook": synthesis.medium_term_outlook,
            
            # Metadata
            "feature9_input_count": synthesis.input_count,
            "feature9_missing_factors": synthesis.missing_factors,
            "feature9_aggregation_method": synthesis.aggregation_method.value,
            "feature9_synthesis_timestamp": synthesis.timestamp,
        }

    def _get_default_output(self) -> Dict[str, any]:
        """Get default output when no synthesis available"""
        return {
            "feature9_overall_risk": 0.0,
            "feature9_risk_severity": "low",
            "feature9_confidence": 0.0,
            "feature9_cost_risk": None,
            "feature9_schedule_risk": None,
            "feature9_workforce_risk": None,
            "feature9_subcontractor_risk": None,
            "feature9_equipment_risk": None,
            "feature9_materials_risk": None,
            "feature9_compliance_risk": None,
            "feature9_environmental_risk": None,
            "feature9_primary_drivers": [],
            "feature9_secondary_drivers": [],
            "feature9_key_interdependencies": [],
            "feature9_executive_summary": "No synthesis data available",
            "feature9_mitigation_plan": [],
            "feature9_short_term_outlook": "Unknown",
            "feature9_medium_term_outlook": "Unknown",
            "feature9_input_count": 0,
            "feature9_missing_factors": [],
            "feature9_aggregation_method": "weighted_average",
            "feature9_synthesis_timestamp": datetime.now().isoformat(),
        }

    def _check_alert_conditions(self, synthesis: SynthesizedRiskOutput):
        """Check if synthesis triggers any alerts"""
        alerts = []

        # Overall risk critical
        if synthesis.overall_risk_score > self.threshold_config["overall_risk_critical"]:
            alert = RiskAlert(
                alert_id=f"alert_critical_{self.project_id}_{datetime.now().isoformat()}",
                project_id=self.project_id,
                task_id=synthesis.task_id,
                risk_category=RiskCategory.COST,  # Placeholder
                alert_type="threshold_exceeded",
                severity=RiskSeverity.CRITICAL,
                triggered_at=datetime.now().isoformat(),
                threshold_value=self.threshold_config["overall_risk_critical"],
                current_value=synthesis.overall_risk_score,
                message=f"Overall project risk CRITICAL at {synthesis.overall_risk_score:.0%}",
                recommended_action=synthesis.risk_mitigation_plan[0] if synthesis.risk_mitigation_plan else "Review risk factors",
                escalation_level=3,
            )
            alerts.append(alert)

        # Overall risk high
        elif synthesis.overall_risk_score > self.threshold_config["overall_risk_high"]:
            alert = RiskAlert(
                alert_id=f"alert_high_{self.project_id}_{datetime.now().isoformat()}",
                project_id=self.project_id,
                task_id=synthesis.task_id,
                risk_category=RiskCategory.SCHEDULE,  # Placeholder
                alert_type="threshold_exceeded",
                severity=RiskSeverity.HIGH,
                triggered_at=datetime.now().isoformat(),
                threshold_value=self.threshold_config["overall_risk_high"],
                current_value=synthesis.overall_risk_score,
                message=f"Overall project risk HIGH at {synthesis.overall_risk_score:.0%}",
                recommended_action=synthesis.risk_mitigation_plan[0] if synthesis.risk_mitigation_plan else "Monitor risk progression",
                escalation_level=2,
            )
            alerts.append(alert)

        # Check for high-impact interactions
        if len(synthesis.key_interdependencies) > 0:
            combined_interaction_risk = sum(
                c.contribution_to_total for c in synthesis.factor_contributions[:2]
            )
            if combined_interaction_risk > self.threshold_config["interaction_threshold"]:
                alert = RiskAlert(
                    alert_id=f"alert_interaction_{self.project_id}_{datetime.now().isoformat()}",
                    project_id=self.project_id,
                    task_id=synthesis.task_id,
                    risk_category=RiskCategory.COST,  # Could be multiple
                    alert_type="interaction_detected",
                    severity=RiskSeverity.HIGH,
                    triggered_at=datetime.now().isoformat(),
                    threshold_value=self.threshold_config["interaction_threshold"],
                    current_value=combined_interaction_risk,
                    message=f"High-risk factor interaction detected: {synthesis.key_interdependencies[0]}",
                    recommended_action="Address root cause shared by multiple risk factors",
                    escalation_level=2,
                )
                alerts.append(alert)

        # Store alerts
        self.alert_history.extend(alerts)

        # Log alerts
        for alert in alerts:
            logger.warning(f"Risk Alert: {alert.message}")

    def _model_risk_propagation(self, synthesis: SynthesizedRiskOutput):
        """Model how task risk propagates to dependent tasks"""
        if not synthesis.task_id:
            return

        # This would connect to Feature 2 (Schedule) to understand dependencies
        # For now, store propagation information for future use
        propagation_info = {
            "source_task": synthesis.task_id,
            "overall_risk": synthesis.overall_risk_score,
            "primary_drivers": synthesis.primary_risk_drivers,
            "estimated_propagation_strength": min(synthesis.overall_risk_score * 0.6, 1.0),
            "timestamp": datetime.now().isoformat(),
        }

        if synthesis.task_id not in self.propagation_paths:
            self.propagation_paths[synthesis.task_id] = []

        self.propagation_paths[synthesis.task_id].append(propagation_info)

    def get_synthesis_history(self, task_id: Optional[str] = None, limit: int = 10) -> List[SynthesizedRiskOutput]:
        """Retrieve historical synthesis records"""
        history = self.aggregator.synthesis_history.get(self.project_id, [])

        # Filter by task if specified
        if task_id:
            history = [s for s in history if s.task_id == task_id]

        # Return most recent N records
        return sorted(history[-limit:], key=lambda x: x.timestamp, reverse=True)

    def get_risk_trend(self, task_id: Optional[str] = None) -> Dict[str, any]:
        """Analyze risk trend over time"""
        history = self.get_synthesis_history(task_id, limit=20)

        if not history:
            return {
                "trend": "insufficient_data",
                "direction": None,
                "velocity": 0.0,
            }

        scores = [s.overall_risk_score for s in history]

        # Calculate trend
        if len(scores) >= 3:
            recent = scores[-3:]  # Last 3 observations
            older = scores[-6:-3] if len(scores) >= 6 else scores[0]

            if isinstance(older, list):
                older_avg = sum(older) / len(older)
            else:
                older_avg = older

            recent_avg = sum(recent) / len(recent)
            velocity = recent_avg - older_avg
            direction = "increasing" if velocity > 0.05 else ("decreasing" if velocity < -0.05 else "stable")
        else:
            direction = "insufficient_data"
            velocity = 0.0

        return {
            "trend": direction,
            "direction": velocity,
            "velocity": abs(velocity),
            "current_score": scores[-1] if scores else 0.0,
            "historical_high": max(scores) if scores else 0.0,
            "historical_low": min(scores) if scores else 0.0,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
        }

    def get_monday_com_data(self, task_id: Optional[str] = None) -> Dict[str, str]:
        """Format synthesis data for monday.com integration"""
        cache_key = task_id or self.project_id
        synthesis = self.synthesis_cache.get(cache_key)

        if not synthesis:
            return self._get_default_monday_data()

        return {
            "Holistic Risk": synthesis.monday_risk_status,
            "Primary Concern": synthesis.monday_primary_concern,
            "Risk Score": f"{synthesis.overall_risk_score:.0%}",
            "Confidence": f"{synthesis.overall_confidence:.0%}",
            "Executive Summary": synthesis.executive_summary[:100],
            "Action Items": "; ".join(synthesis.monday_action_items),
            "Outlook (Next 2 Weeks)": synthesis.short_term_outlook[:50],
            "Mitigation Plan": synthesis.risk_mitigation_plan[0] if synthesis.risk_mitigation_plan else "Monitor",
        }

    def _get_default_monday_data(self) -> Dict[str, str]:
        """Default monday.com data when no synthesis"""
        return {
            "Holistic Risk": "🟢 Low",
            "Primary Concern": "No data",
            "Risk Score": "0%",
            "Confidence": "0%",
            "Executive Summary": "Awaiting data",
            "Action Items": "None",
            "Outlook (Next 2 Weeks)": "Unknown",
            "Mitigation Plan": "TBD",
        }

    def set_threshold(self, category: str, value: float):
        """Configure alert thresholds"""
        if category in self.threshold_config:
            self.threshold_config[category] = value
            logger.info(f"Updated {category} threshold to {value}")

    def reset_project(self):
        """Reset synthesis for project"""
        self.synthesis_cache.clear()
        self.alert_history.clear()
        self.propagation_paths.clear()
        logger.info(f"Reset Feature 9 synthesis for project {self.project_id}")


def create_feature9_integration(project_id: str) -> Feature9Integration:
    """Factory function to create Feature 9 integration"""
    return Feature9Integration(project_id)
