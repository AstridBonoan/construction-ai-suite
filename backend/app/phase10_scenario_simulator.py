"""
Feature 10: Scenario Simulator
What-if analysis engine for comparing alternative scenarios
"""
from typing import List, Dict, Optional
import logging
import math

from phase10_recommendation_types import (
    Scenario,
    ScenarioType,
    ScenarioAdjustment,
    ScenarioRequest,
    ScenarioComparison,
    RecommendationContext,
)

logger = logging.getLogger(__name__)


class ScenarioSimulator:
    """What-if scenario simulation engine"""
    
    def __init__(self):
        """Initialize scenario simulator"""
        self.scenarios_history: Dict[str, List[Scenario]] = {}
    
    def simulate_scenarios(
        self,
        context: RecommendationContext,
        request: ScenarioRequest
    ) -> ScenarioComparison:
        """
        Simulate multiple what-if scenarios and compare
        
        Args:
            context: Current project state
            request: Scenario simulation request
            
        Returns:
            Comparison of all scenarios
        """
        scenarios = []
        
        # Generate baseline first
        baseline = self._simulate_baseline(context)
        scenarios.append(baseline)
        
        # Generate standard scenarios
        for scenario_type in request.scenario_types:
            if scenario_type == ScenarioType.BASELINE:
                continue  # Already added
            
            scenario = self._simulate_scenario_type(context, scenario_type)
            scenarios.append(scenario)
        
        # Add custom scenarios
        for adjustments in request.custom_adjustments:
            scenario = self._simulate_custom(context, adjustments)
            scenarios.append(scenario)
        
        # Limit scenarios
        scenarios = scenarios[:request.max_scenarios]
        
        # Run comparison
        comparison = self._compare_scenarios(scenarios, request)
        
        # Store history
        project_id = context.project_id
        if project_id not in self.scenarios_history:
            self.scenarios_history[project_id] = []
        self.scenarios_history[project_id].extend(scenarios)
        
        return comparison
    
    def _simulate_baseline(self, context: RecommendationContext) -> Scenario:
        """Simulate baseline (no changes) scenario"""
        
        return Scenario(
            scenario_id="baseline",
            project_id=context.project_id,
            scenario_type=ScenarioType.BASELINE,
            name="Current Plan (Baseline)",
            description="No changes from current plan and baseline schedule",
            adjustments=[],
            estimated_risk_score=context.current_overall_risk,
            estimated_total_cost=context.current_total_cost,
            estimated_completion_days=context.days_remaining,
            risk_impact_breakdown={
                "cost_risk": context.cost_risk,
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
                "equipment_risk": context.equipment_risk,
                "materials_risk": context.materials_risk,
                "compliance_risk": context.compliance_risk,
            },
            cost_breakdown={
                "labor": context.current_total_cost * 0.40,
                "materials": context.current_total_cost * 0.35,
                "equipment": context.current_total_cost * 0.15,
                "overhead": context.current_total_cost * 0.10,
            },
            schedule_breakdown={
                "planning": 5,
                "execution": context.days_remaining - 10,
                "closing": 5,
            },
            viability_score=1.0,
            risk_of_scenario=0.0,
            confidence_level=1.0,
            cost_vs_time_tradeoff=0.0,
            cost_vs_risk_tradeoff=0.0,
            time_vs_risk_tradeoff=0.0,
            recommended=False,
            recommendation_reason=None,
        )
    
    def _simulate_scenario_type(
        self,
        context: RecommendationContext,
        scenario_type: ScenarioType
    ) -> Scenario:
        """Simulate a predefined scenario type"""
        
        if scenario_type == ScenarioType.OPTIMISTIC:
            return self._simulate_optimistic(context)
        elif scenario_type == ScenarioType.CONSERVATIVE:
            return self._simulate_conservative(context)
        elif scenario_type == ScenarioType.COST_OPTIMIZED:
            return self._simulate_cost_optimized(context)
        elif scenario_type == ScenarioType.TIME_OPTIMIZED:
            return self._simulate_time_optimized(context)
        elif scenario_type == ScenarioType.RISK_OPTIMIZED:
            return self._simulate_risk_optimized(context)
        else:
            return self._simulate_baseline(context)
    
    def _simulate_optimistic(self, context: RecommendationContext) -> Scenario:
        """Everything goes well scenario"""
        
        # Optimistic: better efficiency, fewer issues
        risk_reduction = 0.25  # 25% risk reduction
        cost_reduction = 0.08  # 8% cost reduction
        schedule_reduction = 0.15 * context.days_remaining  # 15% schedule reduction
        
        scenario = Scenario(
            scenario_id="optimistic",
            project_id=context.project_id,
            scenario_type=ScenarioType.OPTIMISTIC,
            name="Optimistic Case",
            description="Efficient execution, minimal issues, good weather, no delays",
            adjustments=[
                ScenarioAdjustment(
                    workforce_skill_boost=0.15,
                    cost_multiplier=1 - cost_reduction,
                    duration_override_days=int(context.days_remaining * (1 - schedule_reduction / context.days_remaining)),
                )
            ],
            estimated_risk_score=max(0, context.current_overall_risk * (1 - risk_reduction)),
            estimated_total_cost=context.current_total_cost * (1 - cost_reduction),
            estimated_completion_days=int(context.days_remaining * (1 - schedule_reduction / context.days_remaining)),
            risk_impact_breakdown={k: v * (1 - risk_reduction) for k, v in {
                "cost_risk": context.cost_risk,
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
                "equipment_risk": context.equipment_risk,
                "materials_risk": context.materials_risk,
                "compliance_risk": context.compliance_risk,
            }.items()},
            cost_breakdown={
                "labor": context.current_total_cost * 0.40 * (1 - cost_reduction),
                "materials": context.current_total_cost * 0.35 * (1 - cost_reduction),
                "equipment": context.current_total_cost * 0.15 * (1 - cost_reduction),
                "overhead": context.current_total_cost * 0.10 * (1 - cost_reduction),
            },
            schedule_breakdown={
                "planning": 5,
                "execution": int((context.days_remaining - 10) * (1 - schedule_reduction / context.days_remaining)),
                "closing": 4,
            },
            viability_score=0.6,
            risk_of_scenario=0.1,
            confidence_level=0.5,
            cost_vs_time_tradeoff=0.8,  # Good correlation
            cost_vs_risk_tradeoff=0.85,
            time_vs_risk_tradeoff=0.9,
            recommended=False,
        )
        
        return scenario
    
    def _simulate_conservative(self, context: RecommendationContext) -> Scenario:
        """Add buffers and contingency scenario"""
        
        # Conservative: buffers, slower execution
        risk_reduction = 0.15  # Risk reduced by buffers
        cost_increase = 0.12  # 12% cost for buffers
        schedule_increase = 0.20 * context.days_remaining  # 20% schedule buffer
        
        scenario = Scenario(
            scenario_id="conservative",
            project_id=context.project_id,
            scenario_type=ScenarioType.CONSERVATIVE,
            name="Conservative Case",
            description="Include schedule buffers, contingency funds, risk mitigation measures",
            adjustments=[
                ScenarioAdjustment(
                    parallel_dependencies=False,
                    cost_multiplier=1 + cost_increase,
                    duration_override_days=int(context.days_remaining * (1 + schedule_increase / context.days_remaining)),
                    risk_mitigation_measures=[
                        "Weekly risk reviews",
                        "Contingency budget allocated",
                        "Backup suppliers identified",
                    ]
                )
            ],
            estimated_risk_score=max(0, context.current_overall_risk * (1 - risk_reduction)),
            estimated_total_cost=context.current_total_cost * (1 + cost_increase),
            estimated_completion_days=int(context.days_remaining * (1 + schedule_increase / context.days_remaining)),
            risk_impact_breakdown={k: v * (1 - risk_reduction) for k, v in {
                "cost_risk": context.cost_risk,
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
                "equipment_risk": context.equipment_risk,
                "materials_risk": context.materials_risk,
                "compliance_risk": context.compliance_risk,
            }.items()},
            cost_breakdown={
                "labor": context.current_total_cost * 0.40 * (1 + cost_increase),
                "materials": context.current_total_cost * 0.35 * (1 + cost_increase),
                "equipment": context.current_total_cost * 0.15 * (1 + cost_increase),
                "overhead": context.current_total_cost * 0.10 * (1 + cost_increase),
            },
            schedule_breakdown={
                "planning": 5,
                "execution": int((context.days_remaining - 10) * (1 + schedule_increase / context.days_remaining)),
                "closing": 5,
            },
            viability_score=0.95,
            risk_of_scenario=0.05,
            confidence_level=0.9,
            cost_vs_time_tradeoff=-0.6,  # Negative - more time, more cost
            cost_vs_risk_tradeoff=-0.8,  # More cost helps risk
            time_vs_risk_tradeoff=-0.85,  # More time helps risk
            recommended=True,
            recommendation_reason="Provides risk mitigation while adding modest time and cost",
        )
        
        return scenario
    
    def _simulate_cost_optimized(self, context: RecommendationContext) -> Scenario:
        """Minimize total project cost scenario"""
        
        # Cost optimized: material substitution, efficient staffing
        cost_reduction = 0.15  # 15% cost reduction
        risk_increase = 0.12  # Risk increases
        schedule_impact = 0.05 * context.days_remaining  # Slight schedule increase
        
        scenario = Scenario(
            scenario_id="cost_optimized",
            project_id=context.project_id,
            scenario_type=ScenarioType.COST_OPTIMIZED,
            name="Cost-Optimized Scenario",
            description="Material substitutions, lean staffing, efficient logistics",
            adjustments=[
                ScenarioAdjustment(
                    material_quality_level="standard",
                    material_substitution="Cost-effective alternatives",
                    cost_multiplier=1 - cost_reduction,
                    workforce_skill_boost=-0.1,
                    duration_override_days=int(context.days_remaining * (1 + schedule_impact / context.days_remaining)),
                )
            ],
            estimated_risk_score=min(1.0, context.current_overall_risk * (1 + risk_increase)),
            estimated_total_cost=context.current_total_cost * (1 - cost_reduction),
            estimated_completion_days=int(context.days_remaining * (1 + schedule_impact / context.days_remaining)),
            risk_impact_breakdown={k: v * (1 + risk_increase) for k, v in {
                "cost_risk": context.cost_risk,
                "materials_risk": context.materials_risk,
            }.items()} | {k: v for k, v in {
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
                "equipment_risk": context.equipment_risk,
                "compliance_risk": context.compliance_risk,
            }.items()},
            cost_breakdown={
                "labor": context.current_total_cost * 0.40 * (1 - cost_reduction),
                "materials": context.current_total_cost * 0.35 * (1 - cost_reduction * 2),  # Materials hit harder
                "equipment": context.current_total_cost * 0.15 * (1 - cost_reduction),
                "overhead": context.current_total_cost * 0.10 * (1 - cost_reduction),
            },
            schedule_breakdown={
                "planning": 5,
                "execution": int((context.days_remaining - 10) * (1 + schedule_impact / context.days_remaining)),
                "closing": 5,
            },
            viability_score=0.7,
            risk_of_scenario=0.2,
            confidence_level=0.7,
            cost_vs_time_tradeoff=-0.7,
            cost_vs_risk_tradeoff=-0.8,  # Cost reduction increases risk
            time_vs_risk_tradeoff=-0.5,
            recommended=False,
            recommendation_reason="Lowest cost but increases material and schedule risk",
        )
        
        return scenario
    
    def _simulate_time_optimized(self, context: RecommendationContext) -> Scenario:
        """Minimize schedule scenario"""
        
        # Time optimized: parallel execution, additional resources
        schedule_reduction = 0.25 * context.days_remaining  # 25% schedule reduction
        cost_increase = 0.35  # 35% cost increase
        risk_increase = 0.18  # Risk increases from compression
        
        scenario = Scenario(
            scenario_id="time_optimized",
            project_id=context.project_id,
            scenario_type=ScenarioType.TIME_OPTIMIZED,
            name="Time-Optimized Scenario",
            description="Parallel execution, additional crews, fast-track approach",
            adjustments=[
                ScenarioAdjustment(
                    parallel_dependencies=True,
                    cost_multiplier=1 + cost_increase,
                    workout_count_delta=5,  # Additional workers
                    duration_override_days=int(context.days_remaining * (1 - schedule_reduction / context.days_remaining)),
                )
            ],
            estimated_risk_score=min(1.0, context.current_overall_risk * (1 + risk_increase)),
            estimated_total_cost=context.current_total_cost * (1 + cost_increase),
            estimated_completion_days=int(context.days_remaining * (1 - schedule_reduction / context.days_remaining)),
            risk_impact_breakdown={k: v * (1 + risk_increase) for k, v in {
                "cost_risk": context.cost_risk,
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
            }.items()} | {k: v for k, v in {
                "equipment_risk": context.equipment_risk,
                "materials_risk": context.materials_risk,
                "compliance_risk": context.compliance_risk,
            }.items()},
            cost_breakdown={
                "labor": context.current_total_cost * 0.40 * (1 + cost_increase * 1.5),  # Labor hit hardest
                "materials": context.current_total_cost * 0.35 * (1 + cost_increase),
                "equipment": context.current_total_cost * 0.15 * (1 + cost_increase),
                "overhead": context.current_total_cost * 0.10 * (1 + cost_increase),
            },
            schedule_breakdown={
                "planning": 5,
                "execution": int((context.days_remaining - 10) * (1 - schedule_reduction / context.days_remaining)),
                "closing": 3,
            },
            viability_score=0.65,
            risk_of_scenario=0.25,
            confidence_level=0.6,
            cost_vs_time_tradeoff=-0.85,  # Strong negative - cost increases, time decreases
            cost_vs_risk_tradeoff=-0.6,
            time_vs_risk_tradeoff=-0.75,  # Time reduction increases risk
            recommended=False,
            recommendation_reason="Fastest completion but significantly higher cost and risk",
        )
        
        return scenario
    
    def _simulate_risk_optimized(self, context: RecommendationContext) -> Scenario:
        """Minimize overall risk scenario"""
        
        # Risk optimized: mitigation, conservative approach, high oversight
        risk_reduction = 0.30  # 30% risk reduction
        cost_increase = 0.18  # Extra oversight and mitigation
        schedule_increase = 0.10 * context.days_remaining  # 10% schedule buffer
        
        scenario = Scenario(
            scenario_id="risk_optimized",
            project_id=context.project_id,
            scenario_type=ScenarioType.RISK_OPTIMIZED,
            name="Risk-Optimized Scenario",
            description="Risk mitigation focus: increased oversight, quality emphasis, contingencies",
            adjustments=[
                ScenarioAdjustment(
                    cost_multiplier=1 + cost_increase,
                    duration_override_days=int(context.days_remaining * (1 + schedule_increase / context.days_remaining)),
                    risk_mitigation_measures=[
                        "Daily safety audits",
                        "Quality control checkpoints",
                        "Weekly risk reviews",
                        "Supply chain redundancy",
                        "Weather monitoring",
                    ]
                )
            ],
            estimated_risk_score=max(0, context.current_overall_risk * (1 - risk_reduction)),
            estimated_total_cost=context.current_total_cost * (1 + cost_increase),
            estimated_completion_days=int(context.days_remaining * (1 + schedule_increase / context.days_remaining)),
            risk_impact_breakdown={k: v * (1 - risk_reduction) for k, v in {
                "cost_risk": context.cost_risk,
                "schedule_risk": context.schedule_risk,
                "workforce_risk": context.workforce_risk,
                "equipment_risk": context.equipment_risk,
                "materials_risk": context.materials_risk,
                "compliance_risk": context.compliance_risk,
            }.items()},
            cost_breakdown={
                "labor": context.current_total_cost * 0.40 * (1 + cost_increase),
                "materials": context.current_total_cost * 0.35 * (1 + cost_increase),
                "equipment": context.current_total_cost * 0.15 * (1 + cost_increase),
                "overhead": context.current_total_cost * 0.10 * (1 + cost_increase * 3),  # Oversight costs
            },
            schedule_breakdown={
                "planning": 6,  # More planning
                "execution": int((context.days_remaining - 11) * (1 + schedule_increase / context.days_remaining)),
                "closing": 5,
            },
            viability_score=0.85,
            risk_of_scenario=0.08,
            confidence_level=0.85,
            cost_vs_time_tradeoff=-0.5,
            cost_vs_risk_tradeoff=-0.85,  # Cost increase helps risk
            time_vs_risk_tradeoff=-0.8,  # Time increase helps risk
            recommended=True,
            recommendation_reason="Best overall risk profile with balanced cost and schedule impact",
        )
        
        return scenario
    
    def _simulate_custom(
        self,
        context: RecommendationContext,
        adjustments: ScenarioAdjustment
    ) -> Scenario:
        """Simulate custom adjustments scenario"""
        
        # Calculate impacts from adjustments
        risk_delta = self._calculate_risk_from_adjustments(adjustments, context)
        cost_delta = self._calculate_cost_from_adjustments(adjustments, context)
        schedule_delta = self._calculate_schedule_from_adjustments(adjustments, context)
        
        scenario = Scenario(
            scenario_id=f"custom_{int(__import__('time').time())}",
            project_id=context.project_id,
            scenario_type=ScenarioType.CUSTOM,
            name="Custom Scenario",
            description="User-defined adjustments",
            adjustments=[adjustments],
            estimated_risk_score=min(1.0, max(0, context.current_overall_risk + risk_delta)),
            estimated_total_cost=context.current_total_cost + cost_delta,
            estimated_completion_days=max(1, context.days_remaining + schedule_delta),
            viability_score=0.7,
            risk_of_scenario=abs(risk_delta),
            confidence_level=0.6,
            recommended=False,
        )
        
        return scenario
    
    def _calculate_risk_from_adjustments(
        self,
        adjustment: ScenarioAdjustment,
        context: RecommendationContext
    ) -> float:
        """Calculate risk delta from adjustments"""
        delta = 0.0
        
        # Workforce adjustments
        if adjustment.workforce_count_delta > 0:
            delta -= 0.05 * (adjustment.workforce_count_delta / 10)  # Small reduction per 10 workers
        elif adjustment.workforce_count_delta < 0:
            delta += 0.10 * abs(adjustment.workforce_count_delta / 10)
        
        # Skill boost
        delta -= adjustment.workforce_skill_boost * 0.15
        
        # Fast-track
        delta += adjustment.fast_track_percent * 0.002  # 0.2% per 1% fast-track
        
        # Risk mitigation measures
        delta -= len(adjustment.risk_mitigation_measures) * 0.03
        
        return delta
    
    def _calculate_cost_from_adjustments(
        self,
        adjustment: ScenarioAdjustment,
        context: RecommendationContext
    ) -> float:
        """Calculate cost delta from adjustments"""
        delta = 0.0
        
        # Direct cost multiplier
        delta = context.current_total_cost * (adjustment.cost_multiplier - 1.0)
        
        # Workforce additions (rough estimate)
        delta += adjustment.workforce_count_delta * 150000  # Per worker
        
        # Overtime
        delta += context.current_total_cost * (adjustment.overtime_percent / 100) * 0.5
        
        return delta
    
    def _calculate_schedule_from_adjustments(
        self,
        adjustment: ScenarioAdjustment,
        context: RecommendationContext
    ) -> int:
        """Calculate schedule delta from adjustments"""
        delta = 0
        
        # Duration override
        if adjustment.duration_override_days:
            delta = adjustment.duration_override_days - context.days_remaining
        
        # Fast-track
        if adjustment.fast_track_percent > 0:
            delta -= int(context.days_remaining * adjustment.fast_track_percent / 100)
        
        return delta
    
    def _compare_scenarios(
        self,
        scenarios: List[Scenario],
        request: ScenarioRequest
    ) -> ScenarioComparison:
        """Compare multiple scenarios"""
        
        # Find best scenarios for different criteria
        best_risk = min(scenarios, key=lambda s: s.estimated_risk_score)
        best_cost = min(scenarios, key=lambda s: s.estimated_total_cost)
        best_schedule = min(scenarios, key=lambda s: s.estimated_completion_days)
        
        # Calculate overall score (balance of all factors, weighted)
        def overall_score(scenario: Scenario) -> float:
            risk_norm = scenario.estimated_risk_score / max(s.estimated_risk_score for s in scenarios)
            cost_norm = scenario.estimated_total_cost / max(s.estimated_total_cost for s in scenarios)
            schedule_norm = scenario.estimated_completion_days / max(s.estimated_completion_days for s in scenarios)
            return (risk_norm * 0.4 + cost_norm * 0.35 + schedule_norm * 0.25)
        
        ranked = sorted(scenarios, key=overall_score)
        best_overall = ranked[0]
        
        # Build comparison
        comparison = ScenarioComparison(
            project_id=scenarios[0].project_id if scenarios else "",
            scenarios=scenarios,
            scenario_rankings={
                s.scenario_id: (i + 1, overall_score(s))
                for i, s in enumerate(ranked)
            },
            best_for_risk=best_risk.scenario_id,
            worst_for_risk=max(scenarios, key=lambda s: s.estimated_risk_score).scenario_id,
            best_for_cost=best_cost.scenario_id,
            worst_for_cost=max(scenarios, key=lambda s: s.estimated_total_cost).scenario_id,
            best_for_schedule=best_schedule.scenario_id,
            worst_for_schedule=max(scenarios, key=lambda s: s.estimated_completion_days).scenario_id,
            best_overall=best_overall.scenario_id,
            analysis_rationale="Scenarios ranked by balanced optimization of risk, cost, and schedule",
        )
        
        return comparison
