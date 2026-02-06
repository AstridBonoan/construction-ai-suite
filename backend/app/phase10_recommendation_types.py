"""
Feature 10: Automated AI Recommendations & What-If Scenarios
Data types and structures for recommendation and scenario analysis
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class RecommendationType(Enum):
    """Types of AI recommendations"""
    COST_REDUCTION = "cost_reduction"           # Reduce project costs
    SCHEDULE_ACCELERATION = "schedule_acceleration"  # Speed up timeline
    SCHEDULE_BUFFER = "schedule_buffer"        # Add schedule buffer
    RISK_MITIGATION = "risk_mitigation"        # Reduce overall risk
    QUALITY_IMPROVEMENT = "quality_improvement" # Improve quality
    WORKFORCE_OPTIMIZATION = "workforce_optimization"  # Better staffing
    EQUIPMENT_EFFICIENCY = "equipment_efficiency"  # Better equipment use
    MATERIAL_SUBSTITUTION = "material_substitution"  # Alternative materials
    COMPLIANCE_ENHANCEMENT = "compliance_enhancement"  # Compliance improvements
    ENVIRONMENTAL_PROTECTION = "environmental_protection"  # Environmental safeguards


class RecommendationSeverity(Enum):
    """Priority/impact level of recommendation"""
    LOW = "low"              # Nice-to-have
    MEDIUM = "medium"        # Should consider
    HIGH = "high"            # Strongly recommended
    CRITICAL = "critical"    # Must implement


class ScenarioType(Enum):
    """Types of what-if scenarios"""
    BASELINE = "baseline"              # Current plan
    OPTIMISTIC = "optimistic"          # Best case (aggressive timeline)
    CONSERVATIVE = "conservative"      # Worst case (buffer added)
    COST_OPTIMIZED = "cost_optimized"  # Minimize cost
    TIME_OPTIMIZED = "time_optimized"  # Minimize schedule
    RISK_OPTIMIZED = "risk_optimized"  # Minimize risk
    CUSTOM = "custom"                  # User-defined parameters


class ImpactMetric(Enum):
    """Metrics affected by recommendations/scenarios"""
    OVERALL_RISK = "overall_risk"
    COST = "cost"
    SCHEDULE = "schedule"
    QUALITY = "quality"
    SAFETY = "safety"
    COMPLIANCE = "compliance"
    WORKFORCE_MORALE = "workforce_morale"
    RESOURCE_UTILIZATION = "resource_utilization"


@dataclass
class RiskImpact:
    """Risk impact of a recommendation or scenario"""
    overall_risk_delta: float  # Change in overall risk (-1.0 to +1.0)
    cost_risk_delta: float     # Change in cost risk
    schedule_risk_delta: float # Change in schedule risk
    workforce_risk_delta: float # Change in workforce risk
    equipment_risk_delta: float # Change in equipment risk
    other_risk_deltas: Dict[str, float] = field(default_factory=dict)


@dataclass
class CostImpact:
    """Cost impact of a recommendation or scenario"""
    direct_cost_delta: float          # Direct cost change ($)
    indirect_cost_delta: float        # Indirect cost change ($)
    total_cost_delta: float           # Total cost change
    cost_as_percent_of_project: float # Cost change as % of total project
    payback_period_days: Optional[int] = None  # Days to recover cost (if applicable)


@dataclass
class ScheduleImpact:
    """Schedule impact of a recommendation or scenario"""
    duration_delta_days: int    # Change in project duration (days)
    critical_path_delta_days: int  # Change in critical path
    completion_date_delta_days: int  # Change in completion date
    schedule_confidence_change: float  # Change in schedule confidence (-1.0 to +1.0)


@dataclass
class RecommendationImpact:
    """Combined impact of a recommendation"""
    risk_impact: RiskImpact
    cost_impact: CostImpact
    schedule_impact: ScheduleImpact
    implementation_effort_hours: float  # Effort to implement (hours)
    implementation_difficulty: str  # easy|moderate|hard
    implementation_duration_days: int  # Days to implement
    risk_of_implementation: float  # Risk introduced by implementing (0.0-1.0)


@dataclass
class Recommendation:
    """Single AI recommendation"""
    recommendation_id: str
    project_id: str
    task_id: Optional[str]  # None for project-level recommendations
    
    recommendation_type: RecommendationType
    severity: RecommendationSeverity
    title: str  # Short title (e.g., "Hire 2 additional electricians")
    description: str  # Detailed description
    
    impact: RecommendationImpact
    
    # Reasoning
    reasoning: str  # Why this recommendation reduces risk/cost/schedule
    primary_benefits: List[str]  # Main benefits
    potential_drawbacks: List[str]  # Possible downsides
    
    # Preconditions
    prerequisites: List[str]  # What must be true to implement
    constraints: List[str]  # What limitations exist
    
    # Scenario context
    baseline_metric_values: Dict[str, float]  # Baseline values before recommendation
    projected_metric_values: Dict[str, float]  # Projected values after recommendation
    
    # Approval/status
    supported_by_data: bool  # Whether based on real project data
    confidence_level: float  # Confidence in this recommendation (0.0-1.0)
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    valid_until: Optional[str] = None  # Expiration date for recommendation
    monday_com_column_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScenarioAdjustment:
    """Adjustments to apply in a scenario"""
    task_id: Optional[str]  # None for project-level adjustment
    
    # Staffing adjustments
    workforce_count_delta: int = 0  # Add/remove workers
    workforce_skill_boost: float = 0.0  # Improve workforce efficiency (0-1.0)
    
    # Schedule adjustments
    duration_override_days: Optional[int] = None  # Override task duration
    parallel_dependencies: bool = False  # Allow parallel execution of dependent tasks
    
    # Cost adjustments
    cost_multiplier: float = 1.0  # Multiply baseline cost (e.g., 0.8 = -20%)
    overtime_percent: float = 0.0  # Add overtime budget
    
    # Equipment adjustments
    equipment_quality_level: Optional[str] = None  # premium|standard|basic
    equipment_count_delta: int = 0  # Add/remove equipment
    
    # Material adjustments
    material_quality_level: Optional[str] = None  # premium|standard|basic
    material_substitution: Optional[str] = None  # Alternative material specification
    
    # Scope adjustments
    requirements_reduction_percent: float = 0.0  # Reduce scope by %
    fast_track_percent: float = 0.0  # Fast-track by %
    
    # Risk adjustments
    risk_mitigation_measures: List[str] = field(default_factory=list)  # Applied mitigations


@dataclass
class Scenario:
    """What-if scenario for analysis"""
    scenario_id: str
    project_id: str
    
    scenario_type: ScenarioType
    name: str  # Descriptive name (e.g., "Hire 3 electricians early")
    description: str  # Detailed scenario description
    
    # Adjustments
    adjustments: List[ScenarioAdjustment] = field(default_factory=list)
    
    # Impacts
    estimated_risk_score: float  # Projected overall risk (0.0-1.0)
    estimated_total_cost: float  # Projected total cost
    estimated_completion_days: int  # Projected completion days from now
    
    risk_impact_breakdown: Dict[str, float] = field(default_factory=dict)  # Per-factor risk
    cost_breakdown: Dict[str, float] = field(default_factory=dict)  # By category
    schedule_breakdown: Dict[str, int] = field(default_factory=dict)  # By phase
    
    # Analysis
    viability_score: float  # How realistic/achievable (0.0-1.0)
    risk_of_scenario: float  # Risk introduced by scenario changes (0.0-1.0)
    confidence_level: float  # Confidence in projections (0.0-1.0)
    
    # Trade-offs
    cost_vs_time_tradeoff: float  # Correlation between cost reduction and time increase (-1 to +1)
    cost_vs_risk_tradeoff: float  # Correlation between cost reduction and risk (-1 to +1)
    time_vs_risk_tradeoff: float  # Correlation between schedule and risk (-1 to +1)
    
    # Decision support
    recommended: bool  # Is this scenario recommended?
    recommendation_reason: Optional[str] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    valid_until: Optional[str] = None
    
    monday_com_column_map: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScenarioComparison:
    """Comparison of multiple scenarios"""
    project_id: str
    scenarios: List[Scenario]
    
    # Metrics for comparison
    scenario_rankings: Dict[str, Tuple[int, float]]  # scenario_id -> (rank, score)
    
    # Risk analysis
    best_for_risk: str  # Scenario ID with lowest risk
    worst_for_risk: str  # Scenario ID with highest risk
    
    # Cost analysis
    best_for_cost: str  # Scenario ID with lowest cost
    worst_for_cost: str  # Scenario ID with highest cost
    
    # Schedule analysis
    best_for_schedule: str  # Scenario ID with shortest duration
    worst_for_schedule: str  # Scenario ID with longest duration
    
    # Balanced analysis
    best_overall: str  # Scenario ID with best balance
    
    # Trade-off summary
    trade_off_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)  # Scenario x Metric
    
    # Analysis metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_rationale: str = ""
    
    monday_com_comparison_map: Dict[str, Dict[str, str]] = field(default_factory=dict)


@dataclass
class RecommendationContext:
    """Context for generating recommendations"""
    project_id: str
    task_id: Optional[str]  # None for project-level analysis
    
    # Current state
    current_overall_risk: float
    current_total_cost: float
    current_duration_days: int
    
    # Risk breakdown
    cost_risk: float
    schedule_risk: float
    workforce_risk: float
    subcontractor_risk: float
    equipment_risk: float
    materials_risk: float
    compliance_risk: float
    environmental_risk: float
    
    # Project state
    project_phase: str  # planning|execution|closing
    days_into_project: int
    days_remaining: int
    percent_complete: float
    
    # Constraints
    budget_headroom_available: float  # Available budget ($)
    schedule_headroom_available_days: int  # Days available to add
    resource_availability: Dict[str, int]  # Available resources by type
    
    # Recent trends
    risk_trend: str  # increasing|stable|decreasing
    cost_variance: float  # Actual vs planned cost
    schedule_variance: float  # Actual vs planned schedule (days)
    
    # Historical data
    similar_projects_count: int  # Number of similar historical projects
    success_rate_percent: float  # Success rate of similar projects


@dataclass
class RecommendationRequest:
    """Request to generate recommendations"""
    project_id: str
    task_id: Optional[str] = None
    
    # Focus areas
    focus_on_risk: bool = True
    focus_on_cost: bool = True
    focus_on_schedule: bool = True
    
    # Constraints
    max_cost_increase: Optional[float] = None  # Max increase in project cost
    max_schedule_increase: Optional[int] = None  # Max days to add
    min_risk_reduction: float = 0.05  # Min 5% risk reduction to recommend
    
    # Options
    include_aggressive_recommendations: bool = True
    include_conservative_recommendations: bool = True
    max_recommendations_to_return: int = 10
    
    # Filters
    allowed_recommendation_types: List[RecommendationType] = field(default_factory=list)
    exclude_recommendation_types: List[RecommendationType] = field(default_factory=list)


@dataclass
class ScenarioRequest:
    """Request to simulate scenarios"""
    project_id: str
    task_id: Optional[str] = None
    
    # Scenarios to simulate
    scenario_types: List[ScenarioType] = field(default_factory=lambda: [
        ScenarioType.BASELINE,
        ScenarioType.OPTIMISTIC,
        ScenarioType.CONSERVATIVE,
        ScenarioType.RISK_OPTIMIZED
    ])
    
    # Custom scenarios
    custom_adjustments: List[ScenarioAdjustment] = field(default_factory=list)
    
    # Analysis options
    include_trade_off_analysis: bool = True
    include_sensitivity_analysis: bool = True
    max_scenarios: int = 10
    
    # Comparison options
    rank_by: str = "balanced"  # balanced|risk|cost|schedule


@dataclass
class MondayComMapping:
    """Mapping of Feature 10 output to monday.com columns"""
    recommendation_title: str
    recommendation_type: str
    impact_category: str  # Risk|Cost|Schedule|Quality
    estimated_impact: str  # "Risk -25%", "Cost -$50K", "Schedule +5 days"
    effort_to_implement: str  # "Easy (2 days)", "Moderate (1 week)", "Hard (2 weeks)"
    recommended_action: str  # The recommendation itself
    rationale: str  # Why this helps
    confidence: str  # "High (85%)", "Medium (60%)", "Low (40%)"
    next_steps: str  # What to do next


@dataclass
class RecommendationOutput:
    """Output containing recommendations and scenarios"""
    project_id: str
    task_id: Optional[str]
    
    # Recommendations
    recommendations: List[Recommendation] = field(default_factory=list)
    
    # Scenarios
    scenarios: List[Scenario] = field(default_factory=list)
    comparison: Optional[ScenarioComparison] = None
    
    # Summary
    total_cost_reduction_potential: float  # Max possible cost reduction
    total_risk_reduction_potential: float  # Max possible risk reduction (0.0-1.0)
    total_schedule_improvement: int  # Max schedule improvement (days)
    
    # Decision support
    top_recommendation: Optional[Recommendation] = None
    recommended_scenario: Optional[Scenario] = None
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_basis: str  # What data was used
    confidence_level: float  # Overall confidence (0.0-1.0)
    
    # Monday.com mappings
    monday_com_mappings: List[MondayComMapping] = field(default_factory=list)
