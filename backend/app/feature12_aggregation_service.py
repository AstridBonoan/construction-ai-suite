"""
Feature 12: Portfolio Intelligence - Aggregation Service
Aggregates project-level data into portfolio-level intelligence.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date, timedelta
import logging
from collections import defaultdict

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    RiskDriver,
    ExecutiveSummary,
    PortfolioTrendData,
    RiskLevel,
    PortfolioViewType,
    AggregationConfig,
    PortfolioComparison,
)

logger = logging.getLogger(__name__)


class PortfolioAggregationService:
    """
    Service for aggregating project-level data into portfolio intelligence.
    Implements deterministic aggregation with full traceability.
    """
    
    def __init__(self, config: Optional[AggregationConfig] = None):
        """Initialize with optional configuration"""
        self.config = config or AggregationConfig()
        self.aggregation_history: Dict[str, List[PortfolioRiskExposure]] = defaultdict(list)
        
    def aggregate_portfolio(
        self,
        portfolio_id: str,
        projects: List[ProjectSnapshot],
        view_type: PortfolioViewType = PortfolioViewType.CLIENT,
    ) -> PortfolioRiskExposure:
        """
        Aggregate projects into portfolio-level risk exposure.
        
        Args:
            portfolio_id: Unique portfolio identifier
            projects: List of project snapshots to aggregate
            view_type: How to group projects (by client, region, etc.)
        
        Returns:
            PortfolioRiskExposure with aggregated metrics
        """
        
        if not projects:
            logger.warning(f"Empty project list for portfolio {portfolio_id}")
            return self._create_empty_portfolio_exposure(portfolio_id, view_type)
        
        # Group projects by view
        grouped = self._group_projects(projects, view_type)
        
        # Aggregate each group
        exposures = []
        for grouping_key, group_projects in grouped.items():
            exposure = self._aggregate_group(portfolio_id, grouping_key, group_projects, view_type)
            exposures.append(exposure)
        
        # Combine all groups into portfolio
        portfolio_exposure = self._combine_exposures(portfolio_id, view_type, exposures)
        
        # Store in history for trending
        self.aggregation_history[portfolio_id].append(portfolio_exposure)
        
        logger.info(f"Aggregated portfolio {portfolio_id}: risk_score={portfolio_exposure.portfolio_risk_score:.2f}")
        return portfolio_exposure
    
    def _group_projects(
        self,
        projects: List[ProjectSnapshot],
        view_type: PortfolioViewType,
    ) -> Dict[str, List[ProjectSnapshot]]:
        """Group projects by specified view"""
        grouped = defaultdict(list)
        
        for project in projects:
            if view_type == PortfolioViewType.CLIENT:
                key = project.client
            elif view_type == PortfolioViewType.REGION:
                key = project.region
            elif view_type == PortfolioViewType.PROGRAM:
                key = project.program or "Unassigned"
            elif view_type == PortfolioViewType.DIVISION:
                key = project.division or "Unassigned"
            else:  # PORTFOLIO
                key = "All"
            
            grouped[key].append(project)
        
        return grouped
    
    def _aggregate_group(
        self,
        portfolio_id: str,
        grouping_key: str,
        projects: List[ProjectSnapshot],
        view_type: PortfolioViewType,
    ) -> PortfolioRiskExposure:
        """Aggregate a group of projects"""
        
        # Calculate weighted risk scores
        delay_risk = sum(p.delay_risk_score * p.current_budget for p in projects) / sum(p.current_budget for p in projects)
        cost_risk = sum(p.cost_risk_score * p.current_budget for p in projects) / sum(p.current_budget for p in projects)
        resource_risk = sum(p.resource_risk_score * p.current_budget for p in projects) / sum(p.current_budget for p in projects)
        safety_risk = sum(p.safety_risk_score * p.current_budget for p in projects) / sum(p.current_budget for p in projects)
        compliance_risk = sum(p.overall_risk_score * p.current_budget for p in projects) / sum(p.current_budget for p in projects) * 0.05
        
        # Combine using configured weights
        portfolio_risk_score = (
            delay_risk * self.config.delay_risk_weight +
            cost_risk * self.config.cost_risk_weight +
            resource_risk * self.config.resource_risk_weight +
            safety_risk * self.config.safety_risk_weight +
            compliance_risk * self.config.compliance_risk_weight
        )
        
        # Determine risk level
        if portfolio_risk_score >= self.config.risk_score_threshold_critical:
            risk_level = RiskLevel.CRITICAL
        elif portfolio_risk_score >= self.config.risk_score_threshold_high:
            risk_level = RiskLevel.HIGH
        elif portfolio_risk_score >= self.config.risk_score_threshold_medium:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Classify projects by risk
        critical_projects = [p.project_id for p in projects if p.overall_risk_score >= 0.75]
        at_risk_projects = [p.project_id for p in projects if 0.5 <= p.overall_risk_score < 0.75]
        healthy_projects = [p.project_id for p in projects if p.overall_risk_score < 0.5]
        
        # Calculate aggregated metrics
        total_budget = sum(p.current_budget for p in projects)
        total_cost = sum(p.current_cost for p in projects)
        forecasted_total = sum(p.forecasted_final_cost for p in projects)
        
        # Schedule variance (in days)
        schedule_variance = sum(
            (p.current_end_date - p.original_end_date).days 
            for p in projects
        )
        
        # Cost variance
        cost_variance = (forecasted_total - total_budget) / total_budget if total_budget > 0 else 0
        
        # Workforce metrics
        avg_workforce_reliability = (
            sum(p.average_worker_reliability * p.total_workers for p in projects) / 
            sum(p.total_workers for p in projects)
            if sum(p.total_workers for p in projects) > 0 else 0.75
        )
        
        # Risk trending
        risk_trend = self._calculate_risk_trend(portfolio_id, grouping_key, portfolio_risk_score)
        
        exposure = PortfolioRiskExposure(
            portfolio_id=portfolio_id,
            view_type=view_type,
            grouping_key=grouping_key,
            portfolio_risk_score=portfolio_risk_score,
            risk_level=risk_level,
            delay_risk_score=delay_risk,
            cost_risk_score=cost_risk,
            resource_risk_score=resource_risk,
            safety_risk_score=safety_risk,
            compliance_risk_score=compliance_risk,
            critical_projects=critical_projects,
            at_risk_projects=at_risk_projects,
            healthy_projects=healthy_projects,
            total_projects=len(projects),
            total_budget=total_budget,
            total_cost_to_date=total_cost,
            forecasted_total_cost=forecasted_total,
            total_schedule_variance_days=schedule_variance,
            total_cost_variance=cost_variance,
            average_workforce_reliability=avg_workforce_reliability,
            total_resource_gaps=sum(p.unallocated_tasks for p in projects),
            risk_trend=risk_trend[0],
            risk_trend_magnitude=risk_trend[1],
            project_count_in_calc=len(projects),
            confidence_score=self._calculate_confidence(projects),
        )
        
        return exposure
    
    def _combine_exposures(
        self,
        portfolio_id: str,
        view_type: PortfolioViewType,
        exposures: List[PortfolioRiskExposure],
    ) -> PortfolioRiskExposure:
        """Combine all group exposures into portfolio-level exposure"""
        
        if not exposures:
            return self._create_empty_portfolio_exposure(portfolio_id, view_type)
        
        # Aggregate across all groups
        total_projects = sum(e.total_projects for e in exposures)
        total_budget = sum(e.total_budget for e in exposures)
        
        # Weighted average of risk scores
        portfolio_risk = sum(e.portfolio_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0
        delay_risk = sum(e.delay_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0
        cost_risk = sum(e.cost_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0
        resource_risk = sum(e.resource_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0
        safety_risk = sum(e.safety_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0
        
        # Determine overall risk level
        if portfolio_risk >= self.config.risk_score_threshold_critical:
            risk_level = RiskLevel.CRITICAL
        elif portfolio_risk >= self.config.risk_score_threshold_high:
            risk_level = RiskLevel.HIGH
        elif portfolio_risk >= self.config.risk_score_threshold_medium:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        combined = PortfolioRiskExposure(
            portfolio_id=portfolio_id,
            view_type=view_type,
            grouping_key="Portfolio",
            portfolio_risk_score=portfolio_risk,
            risk_level=risk_level,
            delay_risk_score=delay_risk,
            cost_risk_score=cost_risk,
            resource_risk_score=resource_risk,
            safety_risk_score=safety_risk,
            compliance_risk_score=sum(e.compliance_risk_score * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0,
            critical_projects=[p for e in exposures for p in e.critical_projects],
            at_risk_projects=[p for e in exposures for p in e.at_risk_projects],
            healthy_projects=[p for e in exposures for p in e.healthy_projects],
            total_projects=total_projects,
            total_budget=total_budget,
            total_cost_to_date=sum(e.total_cost_to_date for e in exposures),
            forecasted_total_cost=sum(e.forecasted_total_cost for e in exposures),
            total_schedule_variance_days=sum(e.total_schedule_variance_days for e in exposures),
            total_cost_variance=sum(e.total_cost_variance * e.total_budget for e in exposures) / total_budget if total_budget > 0 else 0,
            average_workforce_reliability=sum(e.average_workforce_reliability * e.total_projects for e in exposures) / total_projects if total_projects > 0 else 0.75,
            total_resource_gaps=sum(e.total_resource_gaps for e in exposures),
            risk_trend=self._calculate_portfolio_trend(exposures)[0],
            risk_trend_magnitude=self._calculate_portfolio_trend(exposures)[1],
            project_count_in_calc=total_projects,
            confidence_score=min(e.confidence_score for e in exposures) if exposures else 0.75,
        )
        
        return combined
    
    def identify_risk_drivers(
        self,
        portfolio_id: str,
        exposure: PortfolioRiskExposure,
        projects: List[ProjectSnapshot],
    ) -> List[RiskDriver]:
        """
        Identify systemic risk drivers affecting portfolio.
        Analyzes patterns across projects.
        """
        
        drivers = []
        
        # Driver 1: Delay risk
        if exposure.delay_risk_score > 0.5:
            delayed_projects = [p for p in projects if p.delay_risk_score > 0.5]
            if delayed_projects:
                driver = RiskDriver(
                    driver_id=f"DRV-DELAY-{portfolio_id}",
                    driver_name="Schedule Delay Risk",
                    description="Multiple projects facing schedule delay",
                    risk_category="delay",
                    affected_project_count=len(delayed_projects),
                    total_impact_weight=exposure.delay_risk_score,
                    percentage_of_portfolio_risk=exposure.delay_risk_score / exposure.portfolio_risk_score if exposure.portfolio_risk_score > 0 else 0,
                    affected_projects=[(p.project_id, p.delay_risk_score) for p in delayed_projects],
                    examples=[f"{p.project_id}: {(p.current_end_date - p.original_end_date).days} days behind" for p in delayed_projects[:3]],
                    trend="persistent" if len(delayed_projects) > 2 else "emerging",
                )
                drivers.append(driver)
        
        # Driver 2: Cost overrun
        if exposure.cost_risk_score > 0.5:
            over_budget_projects = [p for p in projects if p.forecasted_final_cost > p.original_budget * 1.1]
            if over_budget_projects:
                total_overrun = sum(p.forecasted_final_cost - p.original_budget for p in over_budget_projects)
                driver = RiskDriver(
                    driver_id=f"DRV-COST-{portfolio_id}",
                    driver_name="Cost Overrun Risk",
                    description="Projects exceeding budgets",
                    risk_category="cost",
                    affected_project_count=len(over_budget_projects),
                    total_impact_weight=exposure.cost_risk_score,
                    percentage_of_portfolio_risk=exposure.cost_risk_score / exposure.portfolio_risk_score if exposure.portfolio_risk_score > 0 else 0,
                    affected_projects=[(p.project_id, p.cost_risk_score) for p in over_budget_projects],
                    examples=[f"{p.project_id}: ${(p.forecasted_final_cost - p.original_budget):,.0f} over budget" for p in over_budget_projects[:3]],
                    trend="degrading" if total_overrun > sum(p.original_budget * 0.15 for p in over_budget_projects) else "stable",
                )
                drivers.append(driver)
        
        # Driver 3: Resource constraints
        if exposure.resource_risk_score > 0.5:
            resource_constrained = [p for p in projects if p.unallocated_tasks > p.total_tasks * 0.2]
            if resource_constrained:
                driver = RiskDriver(
                    driver_id=f"DRV-RESOURCE-{portfolio_id}",
                    driver_name="Resource Availability",
                    description="Insufficient resources causing task delays",
                    risk_category="resource",
                    affected_project_count=len(resource_constrained),
                    total_impact_weight=exposure.resource_risk_score,
                    percentage_of_portfolio_risk=exposure.resource_risk_score / exposure.portfolio_risk_score if exposure.portfolio_risk_score > 0 else 0,
                    affected_projects=[(p.project_id, p.resource_risk_score) for p in resource_constrained],
                    examples=[f"{p.project_id}: {p.unallocated_tasks} tasks unallocated" for p in resource_constrained[:3]],
                    recommended_actions=["Review resource allocation", "Bring in subcontractors", "Parallel task execution"],
                    trend="emerging" if len(resource_constrained) > 3 else "stable",
                )
                drivers.append(driver)
        
        # Driver 4: Low workforce reliability
        if exposure.average_workforce_reliability < 0.75:
            unreliable_projects = [p for p in projects if p.average_worker_reliability < 0.70]
            if unreliable_projects:
                driver = RiskDriver(
                    driver_id=f"DRV-RELIABILITY-{portfolio_id}",
                    driver_name="Workforce Reliability",
                    description="Worker absences and unreliability causing delays",
                    risk_category="resource",
                    affected_project_count=len(unreliable_projects),
                    total_impact_weight=1 - exposure.average_workforce_reliability,
                    percentage_of_portfolio_risk=(1 - exposure.average_workforce_reliability) / exposure.portfolio_risk_score if exposure.portfolio_risk_score > 0 else 0,
                    affected_projects=[(p.project_id, 1 - p.average_worker_reliability) for p in unreliable_projects],
                    examples=[f"{p.project_id}: {1 - p.average_worker_reliability:.0%} unreliability rate" for p in unreliable_projects[:3]],
                    recommended_actions=["Increase supervision", "Conduct team check-ins", "Review incentive structures"],
                    trend="persistent" if len(unreliable_projects) > 2 else "emerging",
                )
                drivers.append(driver)
        
        return sorted(drivers, key=lambda d: d.total_impact_weight, reverse=True)
    
    def generate_executive_summary(
        self,
        portfolio_id: str,
        exposure: PortfolioRiskExposure,
        drivers: List[RiskDriver],
        projects: List[ProjectSnapshot],
    ) -> ExecutiveSummary:
        """Generate executive-friendly summary"""
        
        # Health score (0-100)
        health_score = 100 - (exposure.portfolio_risk_score * 70)  # Risk weighted to health
        
        # Key findings
        key_findings = []
        
        if exposure.critical_projects:
            key_findings.append(
                f"{len(exposure.critical_projects)} project(s) at critical risk, "
                f"representing ${sum(p.current_budget for p in projects if p.project_id in exposure.critical_projects):,.0f}"
            )
        
        if exposure.total_schedule_variance_days > 30:
            key_findings.append(
                f"Portfolio behind schedule by {exposure.total_schedule_variance_days} days, "
                f"driven by {len([p for p in projects if (p.current_end_date - p.original_end_date).days > 0])} delayed projects"
            )
        
        if exposure.total_cost_variance > 0.1:
            key_findings.append(
                f"Cost exposure: estimated overrun of ${exposure.forecasted_total_cost - exposure.total_budget:,.0f} "
                f"({exposure.total_cost_variance:.1%})"
            )
        
        # Top risks as plain text
        top_risks = [
            d.description for d in drivers[:3]
        ]
        
        # Project health
        on_time = len([p for p in projects if (p.current_end_date - p.original_end_date).days <= 0])
        delayed = len([p for p in projects if (p.current_end_date - p.original_end_date).days > 0])
        over_budget = len([p for p in projects if p.forecasted_final_cost > p.original_budget * 1.05])
        
        # Headline
        headline = (
            f"{exposure.total_projects} projects in {exposure.grouping_key}: "
            f"{len(exposure.healthy_projects)} healthy, "
            f"{len(exposure.at_risk_projects)} at risk, "
            f"{len(exposure.critical_projects)} critical"
        )
        
        summary = ExecutiveSummary(
            portfolio_id=portfolio_id,
            report_date=datetime.now(),
            report_period="weekly",
            project_count=exposure.total_projects,
            portfolio_health_score=health_score,
            overall_risk_level=exposure.risk_level,
            headline=headline,
            key_findings=key_findings[:5],
            top_risks=top_risks,
            on_time_projects=on_time,
            delayed_projects=delayed,
            over_budget_projects=over_budget,
            critical_risk_projects=len(exposure.critical_projects),
            total_portfolio_value=exposure.total_budget,
            cumulative_at_risk_value=sum(
                p.current_budget for p in projects 
                if p.project_id in (exposure.critical_projects + exposure.at_risk_projects)
            ),
            potential_cost_overrun=max(0, exposure.forecasted_total_cost - exposure.total_budget),
        )
        
        return summary
    
    def _calculate_risk_trend(
        self,
        portfolio_id: str,
        grouping_key: str,
        current_score: float,
    ) -> Tuple[str, float]:
        """Calculate risk trend direction and magnitude"""
        
        history_key = f"{portfolio_id}_{grouping_key}"
        if history_key not in self.aggregation_history or len(self.aggregation_history[history_key]) < 2:
            return "stable", 0.0
        
        recent = self.aggregation_history[history_key][-1].portfolio_risk_score
        previous = self.aggregation_history[history_key][-2].portfolio_risk_score
        
        change = current_score - previous
        
        if change > 0.05:
            trend = "degrading"
        elif change < -0.05:
            trend = "improving"
        else:
            trend = "stable"
        
        return trend, change
    
    def _calculate_portfolio_trend(self, exposures: List[PortfolioRiskExposure]) -> Tuple[str, float]:
        """Calculate overall portfolio trend"""
        if len(exposures) < 1:
            return "stable", 0.0
        
        avg_risk = sum(e.portfolio_risk_score for e in exposures) / len(exposures)
        
        if avg_risk > 0.60:
            return "degrading", avg_risk
        elif avg_risk < 0.35:
            return "improving", avg_risk
        else:
            return "stable", avg_risk
    
    def _calculate_confidence(self, projects: List[ProjectSnapshot]) -> float:
        """Calculate overall confidence in aggregation"""
        
        if not projects:
            return 0.5
        
        avg_confidence = sum(p.data_confidence for p in projects) / len(projects)
        
        # Reduce confidence if data is stale
        stale_count = sum(
            1 for p in projects 
            if (datetime.now() - p.last_updated).days > self.config.max_snapshot_age_days
        )
        
        staleness_penalty = (stale_count / len(projects)) * 0.2 if stale_count > 0 else 0
        
        return max(0.5, min(1.0, avg_confidence - staleness_penalty))
    
    def _create_empty_portfolio_exposure(
        self,
        portfolio_id: str,
        view_type: PortfolioViewType,
    ) -> PortfolioRiskExposure:
        """Create empty/zero exposure when no projects"""
        
        return PortfolioRiskExposure(
            portfolio_id=portfolio_id,
            view_type=view_type,
            grouping_key="Empty",
            portfolio_risk_score=0.0,
            risk_level=RiskLevel.LOW,
            delay_risk_score=0.0,
            cost_risk_score=0.0,
            resource_risk_score=0.0,
            safety_risk_score=0.0,
            compliance_risk_score=0.0,
            critical_projects=[],
            at_risk_projects=[],
            healthy_projects=[],
            total_projects=0,
            total_budget=0.0,
            total_cost_to_date=0.0,
            forecasted_total_cost=0.0,
            total_schedule_variance_days=0,
            total_cost_variance=0.0,
            average_workforce_reliability=0.75,
            total_resource_gaps=0,
            risk_trend="stable",
            risk_trend_magnitude=0.0,
            project_count_in_calc=0,
            confidence_score=0.0,
        )
