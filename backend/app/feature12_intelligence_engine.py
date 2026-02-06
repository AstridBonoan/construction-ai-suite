"""
Feature 12: Portfolio Intelligence - Executive Intelligence Engine
Generates insights, trends, and recommendations from aggregated portfolio data.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import json

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    RiskDriver,
    ExecutiveSummary,
    PortfolioTrendData,
    RiskLevel,
    PortfolioComparison,
)

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Direction of trend"""
    IMPROVING = "improving"
    STABLE = "stable"
    DEGRADING = "degrading"


class RecommendationPriority(Enum):
    """Recommendation priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutiveIntelligenceEngine:
    """
    Generates executive insights, trends, and recommendations from portfolio data.
    Synthesizes information from aggregation service and integration hooks (Features 9, 10, 11).
    """
    
    def __init__(self):
        """Initialize intelligence engine"""
        self.trend_history: Dict[str, List[PortfolioTrendData]] = {}
        self.recommendation_cache: Dict[str, List[Dict[str, Any]]] = {}
        
    def generate_trends(
        self,
        portfolio_id: str,
        current_exposure: PortfolioRiskExposure,
        time_period: str = "weekly",
        comparison_exposures: Optional[List[PortfolioRiskExposure]] = None,
    ) -> PortfolioTrendData:
        """
        Generate trend data for portfolio over time.
        
        Args:
            portfolio_id: Portfolio identifier
            current_exposure: Current risk exposure
            time_period: "weekly", "monthly", "quarterly"
            comparison_exposures: Historical exposures for trend calculation
        
        Returns:
            PortfolioTrendData with trend metrics
        """
        
        now = datetime.now()
        
        # Calculate trend direction and magnitude
        trend_direction, magnitude = self._calculate_trend_direction(
            portfolio_id,
            current_exposure,
            comparison_exposures,
        )
        
        # Calculate projection
        projection_date = now + self._get_period_delta(time_period)
        projected_score = self._project_risk_score(
            current_exposure.portfolio_risk_score,
            magnitude,
            time_period,
        )
        
        trend_data = PortfolioTrendData(
            portfolio_id=portfolio_id,
            timestamp=now,
            time_period=time_period,
            risk_score=current_exposure.portfolio_risk_score,
            risk_level=current_exposure.risk_level,
            trend_direction=trend_direction.value,
            trend_magnitude=magnitude,
            key_metrics={
                "delay_risk": current_exposure.delay_risk_score,
                "cost_risk": current_exposure.cost_risk_score,
                "resource_risk": current_exposure.resource_risk_score,
                "safety_risk": current_exposure.safety_risk_score,
                "workforce_reliability": current_exposure.average_workforce_reliability,
            },
            metrics_trend={
                "delay_trend": self._trend_component(comparison_exposures, "delay_risk_score"),
                "cost_trend": self._trend_component(comparison_exposures, "cost_risk_score"),
                "resource_trend": self._trend_component(comparison_exposures, "resource_risk_score"),
                "safety_trend": self._trend_component(comparison_exposures, "safety_risk_score"),
            },
            projected_score_date=projection_date,
            projected_score=projected_score,
            confidence_interval_lower=projected_score * 0.85,
            confidence_interval_upper=projected_score * 1.15,
            data_completeness=current_exposure.confidence_score,
        )
        
        # Store in history
        if portfolio_id not in self.trend_history:
            self.trend_history[portfolio_id] = []
        self.trend_history[portfolio_id].append(trend_data)
        
        logger.info(f"Generated trends for portfolio {portfolio_id}: direction={trend_direction.value}, magnitude={magnitude:.2f}")
        return trend_data
    
    def generate_period_comparison(
        self,
        portfolio_id: str,
        current_exposure: PortfolioRiskExposure,
        previous_exposure: Optional[PortfolioRiskExposure] = None,
    ) -> PortfolioComparison:
        """
        Generate week-over-week or month-over-month comparison.
        
        Args:
            portfolio_id: Portfolio identifier
            current_exposure: Current period exposure
            previous_exposure: Previous period exposure for comparison
        
        Returns:
            PortfolioComparison with changes and insights
        """
        
        if previous_exposure is None:
            # No comparison possible
            return PortfolioComparison(
                portfolio_id=portfolio_id,
                current_period_start=datetime.now() - timedelta(days=7),
                current_period_end=datetime.now(),
                previous_period_start=datetime.now() - timedelta(days=14),
                previous_period_end=datetime.now() - timedelta(days=7),
                current_risk_score=current_exposure.portfolio_risk_score,
                previous_risk_score=current_exposure.portfolio_risk_score,
                risk_score_change=0.0,
                risk_level_change="no_change",
                critical_projects_change=0,
                at_risk_projects_change=0,
                health_score_delta=0.0,
                key_changes=[],
                data_quality="baseline",
            )
        
        risk_change = current_exposure.portfolio_risk_score - previous_exposure.portfolio_risk_score
        risk_change_pct = (risk_change / previous_exposure.portfolio_risk_score * 100) if previous_exposure.portfolio_risk_score > 0 else 0
        
        # Determine level change
        if current_exposure.risk_level == previous_exposure.risk_level:
            level_change = "no_change"
        elif current_exposure.risk_level.value > previous_exposure.risk_level.value:
            level_change = "escalated"
        else:
            level_change = "improved"
        
        # Key changes
        key_changes = []
        
        critical_change = len(current_exposure.critical_projects) - len(previous_exposure.critical_projects)
        if critical_change > 0:
            key_changes.append(f"+{critical_change} project(s) now critical")
        elif critical_change < 0:
            key_changes.append(f"{critical_change} project(s) recovered from critical")
        
        at_risk_change = len(current_exposure.at_risk_projects) - len(previous_exposure.at_risk_projects)
        if at_risk_change > 0:
            key_changes.append(f"+{at_risk_change} project(s) at risk")
        elif at_risk_change < 0:
            key_changes.append(f"{abs(at_risk_change)} project(s) improved")
        
        cost_var_change = current_exposure.total_cost_variance - previous_exposure.total_cost_variance
        if cost_var_change > 0.03:
            key_changes.append(f"Cost variance deteriorated {cost_var_change:.1%}")
        elif cost_var_change < -0.03:
            key_changes.append(f"Cost variance improved {abs(cost_var_change):.1%}")
        
        schedule_var_change = current_exposure.total_schedule_variance_days - previous_exposure.total_schedule_variance_days
        if abs(schedule_var_change) > 5:
            key_changes.append(f"Schedule variance {'worsened' if schedule_var_change > 0 else 'improved'} by {abs(schedule_var_change)} days")
        
        # Health score calculation
        current_health = 100 - (current_exposure.portfolio_risk_score * 70)
        previous_health = 100 - (previous_exposure.portfolio_risk_score * 70)
        health_delta = current_health - previous_health
        
        comparison = PortfolioComparison(
            portfolio_id=portfolio_id,
            current_period_start=datetime.now() - timedelta(days=7),
            current_period_end=datetime.now(),
            previous_period_start=datetime.now() - timedelta(days=14),
            previous_period_end=datetime.now() - timedelta(days=7),
            current_risk_score=current_exposure.portfolio_risk_score,
            previous_risk_score=previous_exposure.portfolio_risk_score,
            risk_score_change=risk_change,
            risk_score_change_pct=risk_change_pct,
            risk_level_change=level_change,
            critical_projects_change=critical_change,
            at_risk_projects_change=at_risk_change,
            total_projects_change=current_exposure.total_projects - previous_exposure.total_projects,
            budget_change=current_exposure.total_budget - previous_exposure.total_budget,
            cost_variance_change=cost_var_change,
            schedule_variance_change_days=schedule_var_change,
            health_score_delta=health_delta,
            key_changes=key_changes[:5],
            data_quality="high" if current_exposure.confidence_score > 0.8 else "medium",
        )
        
        return comparison
    
    def generate_recommendations(
        self,
        portfolio_id: str,
        exposure: PortfolioRiskExposure,
        drivers: List[RiskDriver],
        projects: List[ProjectSnapshot],
        feature11_allocations: Optional[List[Dict[str, Any]]] = None,
        feature10_recommendations: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations synthesizing drives and features.
        
        Args:
            portfolio_id: Portfolio identifier
            exposure: Risk exposure
            drivers: Risk drivers
            projects: Project snapshots
            feature11_allocations: Feature 11 Resource Allocation data
            feature10_recommendations: Feature 10 Deterministic Risk data
        
        Returns:
            List of recommendations with priority and actions
        """
        
        recommendations = []
        
        # Recommendation 1: Address critical projects
        if exposure.critical_projects:
            rec = {
                "id": f"REC-CRITICAL-{portfolio_id}",
                "title": "Immediate intervention required for critical projects",
                "priority": RecommendationPriority.CRITICAL.value,
                "affected_projects": exposure.critical_projects[:5],
                "affected_project_count": len(exposure.critical_projects),
                "impact": f"${sum(p.current_budget for p in projects if p.project_id in exposure.critical_projects):,.0f} at immediate risk",
                "recommended_actions": [
                    "Schedule immediate project reviews with stakeholders",
                    "Activate escalation procedures per project protocols",
                    "Allocate additional resources to resolve blockers",
                    f"Expected impact: Reduce critical project count by {len(exposure.critical_projects) // 2 + 1} within 2 weeks",
                ],
                "success_metrics": [
                    "1+ critical projects move to at-risk within 1 week",
                    "Schedule variance reduced by 20%",
                    "Resource allocation improved to 90%+ for blocked tasks",
                ],
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        
        # Recommendation 2: Resource optimization from Feature 11
        if exposure.resource_risk_score > 0.5 and feature11_allocations:
            total_unallocated = sum(p.unallocated_tasks for p in projects)
            rec = {
                "id": f"REC-RESOURCE-{portfolio_id}",
                "title": "Optimize resource allocation to eliminate task gaps",
                "priority": RecommendationPriority.HIGH.value,
                "resource_gap": total_unallocated,
                "impact": f"{total_unallocated} unallocated tasks affecting schedule",
                "recommended_actions": [
                    "Review Feature 11 resource reallocation recommendations",
                    "Execute cross-project resource sharing where feasible",
                    "Engage subcontractor partners for temporary coverage",
                    "Implement parallel task execution where dependencies allow",
                ],
                "success_metrics": [
                    f"Reduce unallocated tasks to <{total_unallocated * 0.5:.0f} within 3 days",
                    "Resource utilization increase to >85%",
                    "Task completion rate improvement to baseline +10%",
                ],
                "feature11_integration": "See Feature 11 allocations endpoint for detailed reallocation options",
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        
        # Recommendation 3: Cost management
        if exposure.cost_risk_score > 0.5:
            overrun_projects = [p for p in projects if p.forecasted_final_cost > p.original_budget * 1.1]
            total_overrun = sum(p.forecasted_final_cost - p.original_budget for p in overrun_projects)
            
            rec = {
                "id": f"REC-COST-{portfolio_id}",
                "title": "Implement cost controls to prevent further overruns",
                "priority": RecommendationPriority.HIGH.value,
                "at_risk_projects": len(overrun_projects),
                "estimated_overrun": total_overrun,
                "overrun_percentage": (exposure.total_cost_variance * 100) if exposure.total_cost_variance > 0 else 0,
                "recommended_actions": [
                    "Conduct value engineering review on over-budget projects",
                    "Renegotiate supplier contracts where margin allows",
                    "Implement project budget controls with weekly reviews",
                    "Identify cost reduction levers through waste elimination",
                ],
                "success_metrics": [
                    f"Reduce cost variance to <5% within 2 weeks",
                    f"Recover ${total_overrun * 0.3:,.0f} through process improvements",
                    "Establish weekly cost tracking to prevent new overruns",
                ],
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        
        # Recommendation 4: Schedule recovery
        if exposure.total_schedule_variance_days > 14:
            delayed_projects = [p for p in projects if (p.current_end_date - p.original_end_date).days > 0]
            
            rec = {
                "id": f"REC-SCHEDULE-{portfolio_id}",
                "title": "Execute schedule recovery plan",
                "priority": RecommendationPriority.HIGH.value,
                "delayed_projects": len(delayed_projects),
                "total_variance_days": exposure.total_schedule_variance_days,
                "max_variance_days": max((p.current_end_date - p.original_end_date).days for p in delayed_projects) if delayed_projects else 0,
                "recommended_actions": [
                    "Identify and resolve schedule constraints (critical path analysis)",
                    "Increase crew sizes for longest-pole activities",
                    "Execute weekend/overtime work with ROI approval",
                    "Implement daily stand-ups for schedule-critical projects",
                    "Compress non-critical path activities where feasible",
                ],
                "success_metrics": [
                    f"Recover {exposure.total_schedule_variance_days // 3} days within 2 weeks",
                    "Get 50% of delayed projects back to schedule",
                    "Prevent further delays for remaining projects",
                ],
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        
        # Recommendation 5: Workforce reliability
        if exposure.average_workforce_reliability < 0.75:
            unreliable_projects = [p for p in projects if p.average_worker_reliability < 0.70]
            
            rec = {
                "id": f"REC-WORKFORCE-{portfolio_id}",
                "title": "Address workforce reliability issues",
                "priority": RecommendationPriority.MEDIUM.value,
                "affected_projects": len(unreliable_projects),
                "avg_reliability_gap": (0.75 - exposure.average_workforce_reliability) * 100,
                "recommended_actions": [
                    f"Conduct worker engagement survey on {len(unreliable_projects)} projects",
                    "Review incentive structures and bonus programs",
                    "Increase on-site supervision for lowest-reliability crews",
                    "Implement attendance tracking and accountability measures",
                ],
                "success_metrics": [
                    "Improve average reliability to >80% within 4 weeks",
                    "Reduce absence rate by 30%",
                    "Identify and address root causes of unreliability",
                ],
                "generated_at": datetime.now().isoformat(),
            }
            recommendations.append(rec)
        
        # Recommendation 6: Risk drivers
        if drivers:
            for driver in drivers[:2]:  # Top 2 drivers
                rec = {
                    "id": f"REC-DRIVER-{driver.driver_id}",
                    "title": f"Address systemic risk: {driver.driver_name}",
                    "priority": RecommendationPriority.HIGH.value if driver.total_impact_weight > 0.4 else RecommendationPriority.MEDIUM.value,
                    "risk_driver": driver.driver_name,
                    "affected_projects": len(driver.affected_projects),
                    "impact_weight": driver.total_impact_weight,
                    "percentage_of_portfolio": f"{driver.percentage_of_portfolio_risk:.1%}",
                    "recommended_actions": driver.recommended_actions or ["Review driver analysis", "Develop mitigation strategy"],
                    "examples": driver.examples[:2],
                    "generated_at": datetime.now().isoformat(),
                }
                recommendations.append(rec)
        
        # Cache recommendations
        self.recommendation_cache[portfolio_id] = recommendations
        
        logger.info(f"Generated {len(recommendations)} recommendations for portfolio {portfolio_id}")
        return recommendations
    
    def get_portfolio_insights(
        self,
        portfolio_id: str,
        exposure: PortfolioRiskExposure,
        summary: ExecutiveSummary,
        drivers: List[RiskDriver],
    ) -> Dict[str, Any]:
        """
        Get comprehensive portfolio insights summary.
        
        Returns:
            Dictionary of key insights for executive consumption
        """
        
        insights = {
            "portfolio_id": portfolio_id,
            "report_time": datetime.now().isoformat(),
            "executive_summary": {
                "health_score": summary.portfolio_health_score,
                "risk_level": exposure.risk_level.value,
                "headline": summary.headline,
                "key_findings": summary.key_findings,
            },
            "portfolio_metrics": {
                "total_projects": exposure.total_projects,
                "project_health": {
                    "healthy": len(exposure.healthy_projects),
                    "at_risk": len(exposure.at_risk_projects),
                    "critical": len(exposure.critical_projects),
                },
                "total_budget": exposure.total_budget,
                "total_cost": exposure.total_cost_to_date,
                "forecast": exposure.forecasted_total_cost,
            },
            "risk_breakdown": {
                "delay_risk": exposure.delay_risk_score,
                "cost_risk": exposure.cost_risk_score,
                "resource_risk": exposure.resource_risk_score,
                "safety_risk": exposure.safety_risk_score,
                "compliance_risk": exposure.compliance_risk_score,
            },
            "top_risks": [
                {
                    "driver": d.driver_name,
                    "category": d.risk_category,
                    "impact": f"{d.percentage_of_portfolio_risk:.1%}",
                    "affected_projects": d.affected_project_count,
                    "trend": d.trend,
                }
                for d in drivers[:5]
            ],
            "performance_indicators": {
                "on_schedule": summary.on_time_projects,
                "delayed": summary.delayed_projects,
                "cost_overrun_projects": summary.over_budget_projects,
                "schedule_variance_days": exposure.total_schedule_variance_days,
                "cost_variance_pct": exposure.total_cost_variance,
                "workforce_reliability": exposure.average_workforce_reliability,
                "resource_gaps": exposure.total_resource_gaps,
            },
            "confidence": {
                "data_quality": exposure.confidence_score,
                "recommendation_confidence": "high" if exposure.confidence_score > 0.8 else "medium",
            },
        }
        
        return insights
    
    def _calculate_trend_direction(
        self,
        portfolio_id: str,
        current: PortfolioRiskExposure,
        comparison_list: Optional[List[PortfolioRiskExposure]],
    ) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and magnitude"""
        
        if not comparison_list or len(comparison_list) < 2:
            return TrendDirection.STABLE, 0.0
        
        prev = comparison_list[-2] if len(comparison_list) >= 2 else comparison_list[0]
        
        change = current.portfolio_risk_score - prev.portfolio_risk_score
        
        if change > 0.05:
            direction = TrendDirection.DEGRADING
        elif change < -0.05:
            direction = TrendDirection.IMPROVING
        else:
            direction = TrendDirection.STABLE
        
        return direction, change
    
    def _trend_component(
        self,
        comparison_list: Optional[List[PortfolioRiskExposure]],
        component: str,
    ) -> str:
        """Get trend direction for specific risk component"""
        
        if not comparison_list or len(comparison_list) < 2:
            return "stable"
        
        current_val = getattr(comparison_list[-1], component, 0)
        prev_val = getattr(comparison_list[-2], component, 0) if len(comparison_list) >= 2 else current_val
        
        change = current_val - prev_val
        
        if change > 0.03:
            return "degrading"
        elif change < -0.03:
            return "improving"
        else:
            return "stable"
    
    def _get_period_delta(self, time_period: str) -> timedelta:
        """Get timedelta for period"""
        
        if time_period == "weekly":
            return timedelta(days=7)
        elif time_period == "monthly":
            return timedelta(days=30)
        elif time_period == "quarterly":
            return timedelta(days=90)
        else:
            return timedelta(days=7)
    
    def _project_risk_score(
        self,
        current_score: float,
        trend_magnitude: float,
        time_period: str,
    ) -> float:
        """Project future risk score"""
        
        # Simple linear projection
        periods = {"weekly": 4, "monthly": 3, "quarterly": 1}
        future_score = current_score + (trend_magnitude * periods.get(time_period, 4))
        
        # Bound to [0, 1]
        return max(0.0, min(1.0, future_score))
