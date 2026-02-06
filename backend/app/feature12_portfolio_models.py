"""
Feature 12: Portfolio Intelligence - Core Data Models
Executive-facing portfolio aggregation models for multi-project intelligence.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, date
from enum import Enum


class RiskLevel(Enum):
    """Portfolio risk severity levels"""
    CRITICAL = "critical"  # > 75% ROR
    HIGH = "high"  # 50-75% ROR
    MEDIUM = "medium"  # 25-50% ROR
    LOW = "low"  # < 25% ROR


class PortfolioViewType(Enum):
    """Portfolio grouping views"""
    CLIENT = "client"
    REGION = "region"
    PROGRAM = "program"
    DIVISION = "division"
    PORTFOLIO = "portfolio"  # All projects


@dataclass
class ProjectSnapshot:
    """Snapshot of single project data for portfolio aggregation"""
    
    project_id: str
    project_name: str
    client: str
    region: str
    program: Optional[str] = None
    division: Optional[str] = None
    
    # Timeline data
    start_date: date
    original_end_date: date
    current_end_date: date
    expected_actual_end_date: Optional[date] = None
    
    # Cost data
    original_budget: float
    current_budget: float
    original_cost: float
    current_cost: float
    forecasted_final_cost: float
    
    # Risk metrics (from Feature 9)
    overall_risk_score: float  # 0-1
    delay_risk_score: float  # 0-1
    cost_risk_score: float  # 0-1
    resource_risk_score: float  # 0-1
    safety_risk_score: float  # 0-1
    
    # Status tracking
    status: str  # "planning", "active", "at_risk", "delayed", "completed"
    progress_percentage: float  # 0-100
    
    # Workload and resource data
    total_tasks: int
    completed_tasks: int
    at_risk_tasks: int
    overdue_tasks: int
    unallocated_tasks: int
    total_workers: int
    average_worker_reliability: float
    
    # Feature integration IDs for traceability
    feature_9_risk_id: Optional[str] = None
    feature_10_recommendation_ids: List[str] = field(default_factory=list)
    feature_11_allocation_ids: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    data_confidence: float = field(default=0.8)  # 0-1 confidence in data quality


@dataclass
class PortfolioRiskExposure:
    """Portfolio-level risk exposure aggregation"""
    
    portfolio_id: str
    view_type: PortfolioViewType
    grouping_key: str  # e.g., client name, region code
    
    # Risk scoring
    portfolio_risk_score: float  # Weighted 0-1
    risk_level: RiskLevel
    
    # Component risks
    delay_risk_score: float
    cost_risk_score: float
    resource_risk_score: float
    safety_risk_score: float
    compliance_risk_score: float
    
    # High-risk projects
    critical_projects: List[str]  # Project IDs at critical risk
    at_risk_projects: List[str]  # Project IDs at elevated risk
    healthy_projects: List[str]  # Project IDs in good state
    
    # Aggregated metrics
    total_projects: int
    total_budget: float
    total_cost_to_date: float
    forecasted_total_cost: float
    total_schedule_variance_days: int
    total_cost_variance: float
    
    # Workforce metrics
    average_workforce_reliability: float
    total_resource_gaps: int
    critical_skill_gaps: List[str]
    
    # Trending
    risk_trend: str  # "improving", "stable", "degrading"
    risk_trend_magnitude: float  # Rate of change
    
    # Metadata
    aggregation_time: datetime = field(default_factory=datetime.now)
    project_count_in_calc: int = 0
    confidence_score: float = field(default=0.75)


@dataclass
class RiskDriver:
    """Identified systemic risk driver in portfolio"""
    
    driver_id: str
    driver_name: str
    description: str
    risk_category: str  # "delay", "cost", "resource", "safety", "compliance"
    
    # Impact across portfolio
    affected_project_count: int
    total_impact_weight: float  # 0-1
    percentage_of_portfolio_risk: float  # What % of portfolio risk is this driver?
    
    # Specific projects affected
    affected_projects: List[tuple] = field(default_factory=list)  # (project_id, impact_weight)
    
    # Context
    examples: List[str] = field(default_factory=list)  # Human-readable examples
    recommended_actions: List[str] = field(default_factory=list)
    
    # Trend
    trend: str  # "emerging", "persistent", "improving"
    first_identified: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutiveSummary:
    """Executive-friendly portfolio summary"""
    
    portfolio_id: str
    report_date: datetime
    report_period: str  # "weekly", "monthly", "quarterly"
    
    # Key statistics
    project_count: int
    portfolio_health_score: float  # 0-100
    overall_risk_level: RiskLevel
    
    # Top line findings (human-friendly)
    headline: str  # E.g., "12 of 45 projects at elevated risk, delay risk +3% WoW"
    key_findings: List[str]  # 3-5 bullet points
    top_risks: List[str]  # Top 3 risk drivers as plain English
    
    # Performance metrics
    on_time_projects: int
    delayed_projects: int
    over_budget_projects: int
    critical_risk_projects: int
    
    # Financial impact
    total_portfolio_value: float
    cumulative_at_risk_value: float
    potential_cost_overrun: float
    
    # Trends
    week_over_week_change: Optional[Dict[str, float]] = None  # {"risk": +0.05, "delay_days": +2}
    month_over_month_change: Optional[Dict[str, float]] = None
    
    # Recommendations
    top_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    # Format: [{"action": "Increase workforce on PRJ-001", "impact": "Reduce delay by 3 days", "priority": "high"}]
    
    # Metadata
    generated_by: str = "Feature 12 - Portfolio Intelligence"
    confidence_level: str = "high"  # "high", "medium", "low"


@dataclass
class PortfolioTrendData:
    """Time-series trend data for portfolio"""
    
    portfolio_id: str
    metric_name: str  # "risk_score", "delay_risk", "cost_variance", etc.
    
    # Time series data
    dates: List[date]
    values: List[float]
    
    # Statistics
    current_value: float
    previous_value: float
    change_amount: float
    change_percent: float
    trend_direction: str  # "up", "down", "stable"
    
    # Projections
    forecast_value: Optional[float] = None
    forecast_date: Optional[date] = None
    confidence_in_forecast: Optional[float] = None


@dataclass
class DashboardDataContract:
    """
    Data contract for monday.com dashboard integration.
    Defines structure and format for dashboard consumption.
    """
    
    # Portfolio level
    portfolio_risk_score: float
    portfolio_health_status: str  # "healthy", "caution", "critical"
    portfolio_name: str
    
    # Summary metrics
    total_projects: int
    projects_on_track: int
    projects_at_risk: int
    projects_critical: int
    
    # Financial
    total_budget: float
    total_spend: float
    projected_final_cost: float
    budget_variance: float
    
    # Schedule
    total_schedule_variance_days: int
    on_time_percentage: float
    delayed_project_count: int
    
    # Resource
    average_workforce_reliability: float
    resource_utilization_percentage: float
    critical_skill_gaps: List[str]
    
    # Risk breakdown
    risk_by_category: Dict[str, float]  # {"delay": 0.6, "cost": 0.4, "resource": 0.3}
    
    # Trend indicators
    risk_trend: str  # "improving", "stable", "degrading"
    risk_trend_value: float  # magnitude
    
    # Top risks
    top_3_risk_drivers: List[Dict[str, str]]
    # [{"name": "Labor shortage", "impact": "5 projects", "projects": "PRJ-001, PRJ-002, ..."}]
    
    # Recommendations
    top_3_recommendations: List[Dict[str, Any]]
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None
    
    def to_monday_com_format(self) -> Dict[str, Any]:
        """
        Convert to monday.com board format.
        Supports direct insertion into monday.com dashboards.
        """
        return {
            "portfolio": {
                "id": self.portfolio_name,
                "name": self.portfolio_name,
                "health": self.portfolio_health_status,
                "risk_score": self.portfolio_risk_score,
                "metrics": {
                    "projects": {
                        "total": self.total_projects,
                        "on_track": self.projects_on_track,
                        "at_risk": self.projects_at_risk,
                        "critical": self.projects_critical,
                    },
                    "financial": {
                        "budget": self.total_budget,
                        "spent": self.total_spend,
                        "projected": self.projected_final_cost,
                        "variance": self.budget_variance,
                    },
                    "schedule": {
                        "variance_days": self.total_schedule_variance_days,
                        "on_time_pct": self.on_time_percentage,
                        "delayed_count": self.delayed_project_count,
                    },
                    "resource": {
                        "avg_reliability": self.average_workforce_reliability,
                        "utilization_pct": self.resource_utilization_percentage,
                        "skill_gaps": self.critical_skill_gaps,
                    }
                },
                "risks": {
                    "by_category": self.risk_by_category,
                    "trend": self.risk_trend,
                    "trend_magnitude": self.risk_trend_value,
                    "top_drivers": self.top_3_risk_drivers,
                },
                "recommendations": self.top_3_recommendations,
            },
            "generated_at": self.generated_at.isoformat(),
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
        }


@dataclass
class PortfolioComparison:
    """
    Comparison between portfolio snapshots (e.g., week-over-week).
    Enables trend analysis and change detection.
    """
    
    comparison_id: str
    portfolio_id: str
    period_type: str  # "day", "week", "month", "quarter"
    
    # Snapshots being compared
    previous_snapshot_date: datetime
    current_snapshot_date: datetime
    
    # Changes
    risk_score_change: float
    delay_risk_change: float
    cost_risk_change: float
    resource_risk_change: float
    
    # Project changes
    new_critical_projects: List[str]
    resolved_critical_projects: List[str]
    degraded_projects: List[str]  # Was healthy, now at risk
    improved_projects: List[str]
    
    # Metric changes
    budget_variance_change: float
    schedule_variance_change: int  # Days
    workforce_reliability_change: float
    
    # Summary
    summary: str  # "2 projects escalated to critical, overall risk +5%"
    action_items: List[str]


# Data aggregation helpers
@dataclass
class AggregationConfig:
    """Configuration for portfolio aggregation"""
    
    # Weighting factors
    delay_risk_weight: float = 0.35
    cost_risk_weight: float = 0.30
    resource_risk_weight: float = 0.20
    safety_risk_weight: float = 0.10
    compliance_risk_weight: float = 0.05
    
    # Sensitivity
    risk_score_threshold_critical: float = 0.75
    risk_score_threshold_high: float = 0.50
    risk_score_threshold_medium: float = 0.25
    
    # Data staleness
    max_snapshot_age_days: int = 7
    warn_if_older_than_days: int = 3
    
    # Portfolio grouping
    default_view: PortfolioViewType = PortfolioViewType.CLIENT
    
    # Confidence thresholds
    min_data_confidence_to_report: float = 0.60
    warn_if_confidence_below: float = 0.75
