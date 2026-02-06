"""
Feature 10: AI Recommendation Engine
Generates actionable recommendations based on project risk and metrics
"""
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

from phase10_recommendation_types import (
    Recommendation,
    RecommendationContext,
    RecommendationRequest,
    RecommendationType,
    RecommendationSeverity,
    RecommendationImpact,
    RiskImpact,
    CostImpact,
    ScheduleImpact,
    MondayComMapping,
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Core AI recommendation engine"""
    
    def __init__(self):
        """Initialize recommendation engine"""
        self.generated_recommendations: List[Recommendation] = []
        self.recommendation_history: Dict[str, List[Recommendation]] = {}
    
    def generate_recommendations(
        self,
        context: RecommendationContext,
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """
        Generate AI recommendations based on project context
        
        Args:
            context: Current project state
            request: Recommendation request with constraints
            
        Returns:
            List of recommendations sorted by impact/severity
        """
        recommendations = []
        
        # Risk-focused recommendations
        if request.focus_on_risk:
            recommendations.extend(self._generate_risk_recommendations(context, request))
        
        # Cost-focused recommendations
        if request.focus_on_cost:
            recommendations.extend(self._generate_cost_recommendations(context, request))
        
        # Schedule-focused recommendations
        if request.focus_on_schedule:
            recommendations.extend(self._generate_schedule_recommendations(context, request))
        
        # Filter by request constraints
        recommendations = self._apply_filters(recommendations, request)
        
        # Sort by severity and impact
        recommendations = sorted(
            recommendations,
            key=lambda r: (
                -self._severity_score(r.severity),
                -abs(r.impact.risk_impact.overall_risk_delta),
                -r.impact.cost_impact.total_cost_delta,
            )
        )
        
        # Limit to max requested
        recommendations = recommendations[:request.max_recommendations_to_return]
        
        # Store in history
        project_id = context.project_id
        if project_id not in self.recommendation_history:
            self.recommendation_history[project_id] = []
        self.recommendation_history[project_id].extend(recommendations)
        
        return recommendations
    
    def _generate_risk_recommendations(
        self,
        context: RecommendationContext,
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        # High cost risk → recommend cost controls
        if context.cost_risk > 0.6:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.COST_REDUCTION,
                title="Implement strict cost controls",
                description="Cost risk is elevated. Implement weekly cost reviews and budget tracking.",
                risk_delta=-0.15,
                cost_increase=5000,
                schedule_delta=2,
                reasoning="Early cost control prevents cost overruns that cascade into schedule risk.",
                difficulty="moderate",
                severity=RecommendationSeverity.HIGH,
            )
            recommendations.append(rec)
        
        # High schedule risk → recommend schedule buffer
        if context.schedule_risk > 0.6:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.SCHEDULE_BUFFER,
                title="Add schedule contingency buffer",
                description=f"Add buffer to critical path. Current slack: {context.schedule_headroom_available_days} days.",
                risk_delta=-0.12,
                cost_increase=0,
                schedule_delta=context.schedule_headroom_available_days // 4,  # Use 1/4 of available
                reasoning="Schedule buffer reduces execution pressure and cascading delays.",
                difficulty="easy",
                severity=RecommendationSeverity.HIGH,
            )
            recommendations.append(rec)
        
        # High workforce risk → recommend staffing
        if context.workforce_risk > 0.55:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.WORKFORCE_OPTIMIZATION,
                title="Augment workforce with specialized trades",
                description="Add skilled workers to reduce execution timeline and improve quality.",
                risk_delta=-0.18,
                cost_increase=150000,
                schedule_delta=-5,
                reasoning="Early workforce augmentation prevents bottlenecks and quality issues.",
                difficulty="moderate",
                severity=RecommendationSeverity.HIGH,
            )
            recommendations.append(rec)
        
        # High equipment risk → recommend preventive maintenance
        if context.equipment_risk > 0.5:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.EQUIPMENT_EFFICIENCY,
                title="Implement predictive equipment maintenance",
                description="Schedule maintenance ahead of failure probability windows.",
                risk_delta=-0.10,
                cost_increase=25000,
                schedule_delta=0,
                reasoning="Preventive maintenance avoids equipment failures that cascade into schedule delays.",
                difficulty="moderate",
                severity=RecommendationSeverity.MEDIUM,
            )
            recommendations.append(rec)
        
        # High compliance risk → recommend enhancement
        if context.compliance_risk > 0.55:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.COMPLIANCE_ENHANCEMENT,
                title="Increase compliance monitoring frequency",
                description="Weekly compliance audits vs current monthly schedule.",
                risk_delta=-0.12,
                cost_increase=8000,
                schedule_delta=0,
                reasoning="Increased compliance monitoring catches issues early, avoiding shutdowns.",
                difficulty="easy",
                severity=RecommendationSeverity.HIGH,
            )
            recommendations.append(rec)
        
        # Environmental risk
        if context.environmental_risk > 0.5:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.ENVIRONMENTAL_PROTECTION,
                title="Enhanced environmental safeguards",
                description="Add dust control, stormwater management, and air quality monitoring.",
                risk_delta=-0.08,
                cost_increase=12000,
                schedule_delta=1,
                reasoning="Proactive environmental measures prevent shutdowns and fines.",
                difficulty="moderate",
                severity=RecommendationSeverity.MEDIUM,
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_cost_recommendations(
        self,
        context: RecommendationContext,
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """Generate cost reduction recommendations"""
        recommendations = []
        
        # Cost variance positive → spending over budget
        if context.cost_variance > 0.1:  # 10% over
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.COST_REDUCTION,
                title="Material substitution for cost optimization",
                description="Consider equivalent materials at lower cost without quality impact.",
                risk_delta=0.02,  # Slight risk increase from substitution
                cost_increase=-50000,  # Cost reduction
                schedule_delta=0,
                reasoning="Strategic material substitution reduces cost variance without schedule impact.",
                difficulty="moderate",
                severity=RecommendationSeverity.MEDIUM,
            )
            recommendations.append(rec)
        
        # Project in execution phase → recommend efficiency gains
        if context.project_phase == "execution":
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.COST_REDUCTION,
                title="Optimize crew productivity",
                description="Implement lean site planning and prefabrication where possible.",
                risk_delta=-0.05,
                cost_increase=-75000,
                schedule_delta=-3,
                reasoning="Productivity improvements reduce cost and schedule while improving quality.",
                difficulty="hard",
                severity=RecommendationSeverity.MEDIUM,
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_schedule_recommendations(
        self,
        context: RecommendationContext,
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """Generate schedule acceleration recommendations"""
        recommendations = []
        
        # High schedule risk → recommend acceleration
        if context.schedule_risk > 0.65 and context.days_remaining > 14:
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.SCHEDULE_ACCELERATION,
                title="Fast-track critical path",
                description="Run some dependent activities in parallel on critical path.",
                risk_delta=0.15,  # Risk increases with fast-tracking
                cost_increase=200000,  # Additional cost
                schedule_delta=-10,
                reasoning="Controlled fast-tracking reduces schedule risk if cost is available.",
                difficulty="hard",
                severity=RecommendationSeverity.MEDIUM,
            )
            recommendations.append(rec)
        
        # Behind schedule → recommend recovery
        if context.schedule_variance < -7:  # More than 1 week behind
            rec = self._create_recommendation(
                context=context,
                recommendation_type=RecommendationType.SCHEDULE_ACCELERATION,
                title="Implement schedule recovery plan",
                description="Deploy additional resources to critical path to recover schedule.",
                risk_delta=0.10,
                cost_increase=300000,
                schedule_delta=-context.schedule_variance,  # Recover the variance
                reasoning="Timely schedule recovery prevents cascading delays.",
                difficulty="hard",
                severity=RecommendationSeverity.HIGH,
            )
            recommendations.append(rec)
        
        return recommendations
    
    def _create_recommendation(
        self,
        context: RecommendationContext,
        recommendation_type: RecommendationType,
        title: str,
        description: str,
        risk_delta: float,
        cost_increase: float,
        schedule_delta: int,
        reasoning: str,
        difficulty: str,
        severity: RecommendationSeverity,
    ) -> Recommendation:
        """Create a recommendation object"""
        
        # Calculate implementation effort
        effort_hours = self._calculate_effort(difficulty)
        duration_days = self._calculate_duration(difficulty)
        implementation_risk = self._calculate_implementation_risk(difficulty)
        
        # Build impacts
        risk_impact = RiskImpact(
            overall_risk_delta=risk_delta,
            cost_risk_delta=risk_delta * 0.8,
            schedule_risk_delta=risk_delta * 0.7,
            workforce_risk_delta=risk_delta if "workforce" in title.lower() else 0,
            equipment_risk_delta=risk_delta if "equipment" in title.lower() else 0,
        )
        
        cost_impact = CostImpact(
            direct_cost_delta=cost_increase,
            indirect_cost_delta=cost_increase * 0.1,
            total_cost_delta=cost_increase * 1.1,
            cost_as_percent_of_project=cost_increase / max(context.current_total_cost, 1),
            payback_period_days=None if cost_increase <= 0 else None,
        )
        
        schedule_impact = ScheduleImpact(
            duration_delta_days=schedule_delta,
            critical_path_delta_days=schedule_delta if schedule_delta < 0 else 0,
            completion_date_delta_days=schedule_delta,
            schedule_confidence_change=0.05 if risk_delta < 0 else -0.05,
        )
        
        impact = RecommendationImpact(
            risk_impact=risk_impact,
            cost_impact=cost_impact,
            schedule_impact=schedule_impact,
            implementation_effort_hours=effort_hours,
            implementation_difficulty=difficulty,
            implementation_duration_days=duration_days,
            risk_of_implementation=implementation_risk,
        )
        
        # Build recommendation
        rec = Recommendation(
            recommendation_id=f"rec_{datetime.now().timestamp()}",
            project_id=context.project_id,
            task_id=context.task_id,
            recommendation_type=recommendation_type,
            severity=severity,
            title=title,
            description=description,
            impact=impact,
            reasoning=reasoning,
            primary_benefits=[
                f"Risk reduction: {abs(risk_delta)*100:.0f}%",
                f"Cost change: ${cost_increase:,.0f}",
                f"Schedule delta: {schedule_delta} days",
            ],
            potential_drawbacks=[
                f"Implementation effort: {effort_hours} hours",
                f"Implementation risk: {implementation_risk*100:.0f}%",
            ],
            prerequisites=[
                "Budget approval",
                f"Implementation timeline: {duration_days} days",
            ],
            constraints=[
                "Available budget headroom",
                "Team capacity",
                "Vendor availability",
            ],
            baseline_metric_values={
                "overall_risk": context.current_overall_risk,
                "total_cost": context.current_total_cost,
                "duration_days": context.current_duration_days,
            },
            projected_metric_values={
                "overall_risk": context.current_overall_risk + risk_delta,
                "total_cost": context.current_total_cost + cost_increase,
                "duration_days": context.current_duration_days + schedule_delta,
            },
            supported_by_data=True,
            confidence_level=0.75 + (abs(risk_delta) * 0.2),  # Higher impact = higher confidence
            monday_com_column_map=self._build_monday_mapping(
                title, recommendation_type, risk_delta, cost_increase, schedule_delta, difficulty
            ),
        )
        
        return rec
    
    def _apply_filters(
        self,
        recommendations: List[Recommendation],
        request: RecommendationRequest
    ) -> List[Recommendation]:
        """Apply filters to recommendations"""
        filtered = []
        
        for rec in recommendations:
            # Filter by type
            if request.allowed_recommendation_types:
                if rec.recommendation_type not in request.allowed_recommendation_types:
                    continue
            
            if rec.recommendation_type in request.exclude_recommendation_types:
                continue
            
            # Filter by cost impact
            if request.max_cost_increase is not None:
                if rec.impact.cost_impact.total_cost_delta > request.max_cost_increase:
                    continue
            
            # Filter by schedule impact
            if request.max_schedule_increase is not None:
                if rec.impact.schedule_impact.duration_delta_days > request.max_schedule_increase:
                    continue
            
            # Filter by minimum risk reduction
            if rec.impact.risk_impact.overall_risk_delta > -request.min_risk_reduction:
                if rec.recommendation_type not in [
                    RecommendationType.COST_REDUCTION,
                    RecommendationType.SCHEDULE_ACCELERATION,
                ]:
                    continue
            
            filtered.append(rec)
        
        return filtered
    
    def _severity_score(self, severity: RecommendationSeverity) -> int:
        """Convert severity to numeric score"""
        scores = {
            RecommendationSeverity.LOW: 1,
            RecommendationSeverity.MEDIUM: 2,
            RecommendationSeverity.HIGH: 3,
            RecommendationSeverity.CRITICAL: 4,
        }
        return scores.get(severity, 0)
    
    def _calculate_effort(self, difficulty: str) -> float:
        """Calculate implementation effort in hours"""
        efforts = {
            "easy": 8,
            "moderate": 40,
            "hard": 160,
        }
        return efforts.get(difficulty, 40)
    
    def _calculate_duration(self, difficulty: str) -> int:
        """Calculate implementation duration in days"""
        durations = {
            "easy": 1,
            "moderate": 7,
            "hard": 14,
        }
        return durations.get(difficulty, 7)
    
    def _calculate_implementation_risk(self, difficulty: str) -> float:
        """Calculate risk of implementation"""
        risks = {
            "easy": 0.05,
            "moderate": 0.15,
            "hard": 0.30,
        }
        return risks.get(difficulty, 0.1)
    
    def _build_monday_mapping(
        self,
        title: str,
        rec_type: RecommendationType,
        risk_delta: float,
        cost_delta: float,
        schedule_delta: int,
        difficulty: str,
    ) -> Dict[str, str]:
        """Build monday.com column mappings"""
        
        # Determine impact category
        if abs(risk_delta) > abs(cost_delta / 1000000):
            impact_category = "Risk"
            impact_value = f"Risk {risk_delta*100:+.0f}%"
        elif cost_delta != 0:
            impact_category = "Cost"
            impact_value = f"Cost ${cost_delta:+,.0f}"
        else:
            impact_category = "Schedule"
            impact_value = f"Schedule {schedule_delta:+.0f} days"
        
        return {
            "Recommended Action": title,
            "Recommendation Type": rec_type.value,
            "Impact Category": impact_category,
            "Estimated Impact": impact_value,
            "Effort to Implement": f"{difficulty.title()} ({self._calculate_duration(difficulty)} days)",
            "Confidence Level": "High" if abs(risk_delta) > 0.1 else "Medium",
        }
    
    def get_recommendation_history(self, project_id: str) -> List[Recommendation]:
        """Get recommendation history for project"""
        return self.recommendation_history.get(project_id, [])
    
    def get_top_recommendations(
        self,
        project_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """Get top recommendations by impact"""
        history = self.get_recommendation_history(project_id)
        sorted_recs = sorted(
            history,
            key=lambda r: (
                -self._severity_score(r.severity),
                -abs(r.impact.risk_impact.overall_risk_delta),
            )
        )
        return sorted_recs[:limit]
