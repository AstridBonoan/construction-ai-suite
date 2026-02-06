"""
Feature 11: Predictive Resource & Subcontractor Allocation
Data types and models for resource optimization
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date


class SkillLevel(Enum):
    """Skill proficiency levels"""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    MASTER = "master"


class ResourceType(Enum):
    """Types of resources"""
    LABOR = "labor"
    CREW = "crew"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"


class AllocationStatus(Enum):
    """Status of resource allocation"""
    UNALLOCATED = "unallocated"
    ALLOCATED = "allocated"
    OVER_ALLOCATED = "over_allocated"
    UNDER_ALLOCATED = "under_allocated"
    IDLE = "idle"


class ReallocationReason(Enum):
    """Reasons for reallocation"""
    REDUCE_DELAY_RISK = "reduce_delay_risk"
    REDUCE_COST_OVERRUN = "reduce_cost_overrun"
    REDUCE_CRITICAL_PATH = "reduce_critical_path"
    IMPROVE_CREW_UTILIZATION = "improve_crew_utilization"
    LEVERAGE_SKILLS = "leverage_skills"
    BALANCE_WORKLOAD = "balance_workload"
    MITIGATE_DEPENDENCY_RISK = "mitigate_dependency_risk"
    HANDLE_ABSENCE = "handle_absence"


@dataclass
class Skill:
    """Individual skill with proficiency level"""
    skill_name: str
    proficiency_level: SkillLevel
    years_experience: int
    certification_required: bool
    certification_expired: bool = False


@dataclass
class ResourceAvailability:
    """Availability window for a resource"""
    available_from: date
    available_to: date
    hours_per_week: int  # max hours available per week
    max_concurrent_tasks: int  # max tasks simultaneously
    on_site_requirement: bool  # must be on-site
    travel_time_hours: int  # time to reach site


@dataclass
class Worker:
    """Individual worker representation"""
    worker_id: str
    name: str
    crew_id: Optional[str]  # crew they belong to
    skills: List[Skill]  # list of skills
    availability: ResourceAvailability
    hourly_rate: float
    base_reliability_score: float  # 0-1, from Feature 3
    absence_history: List[Tuple[date, date]]  # historical absences
    monday_user_id: Optional[str]  # monday.com user ID
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Crew:
    """Group of workers working together"""
    crew_id: str
    name: str
    lead_worker_id: str  # crew leader
    member_worker_ids: List[str]  # worker IDs in crew
    team_role: str  # e.g., "concrete", "framing", "electrical"
    combined_reliability_score: float  # 0-1
    monday_team_id: Optional[str]  # monday.com team ID
    historical_productivity: Dict[str, float] = field(default_factory=dict)


@dataclass
class Subcontractor:
    """External subcontractor representation"""
    subcontractor_id: str
    company_name: str
    primary_contact: str
    contact_phone: str
    services: List[str]  # types of work
    availability: ResourceAvailability
    hourly_rate: float
    contract_cost_range: Tuple[float, float]  # min-max
    performance_score: float  # 0-1, from Feature 4
    reliability_score: float  # 0-1
    past_delay_frequency: float  # delays / total projects
    past_cost_overrun_percent: float  # typical overruns
    monday_vendor_id: Optional[str]  # monday.com vendor ID
    historical_projects: List[str] = field(default_factory=list)


@dataclass
class TaskResourceRequirement:
    """Resource requirement for a specific task"""
    task_id: str
    required_role: str  # e.g., "carpenter", "electrician"
    required_skills: List[Skill]
    min_skill_level: SkillLevel
    workers_needed: int
    crew_size_optimal: Optional[int]  # preferred crew size
    can_use_subcontractor: bool
    duration_days: int
    start_date: date
    end_date: date
    critical_path: bool
    estimated_hours: int  # total hours needed


@dataclass
class CurrentTaskAllocation:
    """Current allocation of resources to a task"""
    task_id: str
    project_id: str
    allocated_workers: Dict[str, int]  # worker_id -> hours allocated
    allocated_crew_ids: List[str]  # crews assigned
    allocated_subcontractor_ids: List[str]  # subcontractors
    allocation_start: date
    allocation_end: date
    estimated_completion_hours: int
    actual_completed_hours: int
    completion_percent: float  # 0-1
    delay_risk_from_allocation: float  # 0-1
    cost_from_allocation: float


@dataclass
class AllocationScore:
    """Scoring for resource allocation"""
    allocation_id: str
    skill_match_score: float  # 0-1 (higher = better match)
    availability_match_score: float  # 0-1 (higher = better fit)
    cost_efficiency_score: float  # 0-1 (higher = more efficient)
    reliability_score: float  # 0-1 (from Features 3/4)
    utilization_score: float  # 0-1 (how utilized resource is)
    dependency_impact_score: float  # 0-1 (positive if helps dependencies)
    overall_allocation_score: float  # weighted average
    explanation: str


@dataclass
class ReallocationRecommendation:
    """Recommendation to move resources"""
    recommendation_id: str
    from_task_id: str
    to_task_id: str
    project_id: str
    resource_type: ResourceType  # LABOR, CREW, SUBCONTRACTOR
    resource_id: str  # worker_id, crew_id, or subcontractor_id
    resource_name: str
    reason: ReallocationReason
    hours_to_reallocate: int
    current_allocation_score: float
    projected_allocation_score: float
    delay_risk_reduction: float  # absolute, e.g., 0.12 = 12% reduction
    cost_impact: float  # negative = cost savings
    confidence_level: float  # 0-1
    implementation_difficulty: str  # easy, moderate, hard
    downstream_effects: List['DownstreamEffect'] = field(default_factory=list)
    explanation: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    monday_notif_ready: bool = False


@dataclass
class DownstreamEffect:
    """Effect of a reallocation on another task/project"""
    affected_task_id: str
    affected_project_id: str
    effect_type: str  # "delay_reduction", "cost_increase", "risk_change"
    magnitude: float  # e.g., 0.08 for 8% improvement
    confidence: float  # 0-1


@dataclass
class AllocationComparison:
    """Comparison of current vs. optimized allocation"""
    current_recommendations: List[ReallocationRecommendation]
    current_state: Dict[str, AllocationScore]  # allocation_id -> score
    optimized_state: Dict[str, AllocationScore]  # after recommendations
    total_delay_risk_reduction: float
    total_cost_impact: float
    total_utilization_improvement: float
    recommendations_count: int
    high_confidence_count: int
    implementation_effort_hours: int
    analysis_timestamp: datetime


@dataclass
class ResourceAllocationContext:
    """Context for resource allocation analysis"""
    project_id: str
    all_workers: List[Worker]
    all_crews: List[Crew]
    all_subcontractors: List[Subcontractor]
    tasks: List[TaskResourceRequirement]
    current_allocations: List[CurrentTaskAllocation]
    
    # Historical context
    historical_productivity: Dict[str, float]  # worker_id -> productivity %
    season: str  # "winter", "spring", "summer", "fall"
    project_phase: str  # "planning", "execution", "closing"
    
    # Risk and performance context from other features
    workforce_reliability_scores: Dict[str, float]  # from Feature 3
    subcontractor_performance_scores: Dict[str, float]  # from Feature 4
    task_delay_risks: Dict[str, float]  # from Feature 1
    
    # Constraints
    budget_constraints: Optional[float]  # max additional cost
    time_constraints: Optional[int]  # max delay allowed
    no_reallocation_task_ids: List[str] = field(default_factory=list)  # locked


@dataclass
class AllocationRequest:
    """Request for resource allocation optimization"""
    project_id: str
    optimization_goal: str  # "minimize_delay", "minimize_cost", "balance"
    max_recommendations: int = 10
    include_resource_types: Optional[List[ResourceType]] = None
    min_confidence_threshold: float = 0.60
    allow_subcontractor_substitution: bool = True
    preserve_crews: bool = True  # don't break up crews
    consider_learning_curve: bool = True
    analysis_depth: str = "standard"  # "quick", "standard", "thorough"


@dataclass
class AllocationOutput:
    """Complete output from allocation optimization"""
    project_id: str
    recommendations: List[ReallocationRecommendation]
    comparison: AllocationComparison
    optimization_goal: str
    total_delay_risk_reduction_potential: float
    total_cost_reduction_potential: float
    total_utilization_improvement: float
    top_recommendation: Optional[ReallocationRecommendation]
    confidence_level: float
    generated_at: datetime
    
    # Integration hooks
    feature_3_worker_risks: Dict[str, float] = field(default_factory=dict)
    feature_4_subcontractor_risks: Dict[str, float] = field(default_factory=dict)
    feature_9_inputs: Dict[str, any] = field(default_factory=dict)
    feature_10_if_statements: List[str] = field(default_factory=list)
    
    # Monday.com ready
    monday_fields: Dict[str, any] = field(default_factory=dict)


@dataclass
class ImpactProjection:
    """Projected impact of allocation change"""
    task_id: str
    delay_risk_current: float
    delay_risk_projected: float
    delay_risk_delta: float
    cost_current: float
    cost_projected: float
    cost_delta: float
    worker_utilization_current: float
    worker_utilization_projected: float
    deadline_confidence_current: float
    deadline_confidence_projected: float
    critical_path_proximity: float  # 0-1, how close to critical path


@dataclass
class MondayComMapping:
    """Mapping of allocation data to monday.com"""
    allocation_item_id: str
    recommendation_id: str
    monday_task_id: str
    field_mappings: Dict[str, str] = field(default_factory=dict)
    # Common fields:
    # "Recommended Reallocation": str
    # "Predicted Risk Reduction": float
    # "Cost Impact": float
    # "Implementation Effort": str
    # "Confidence": float
    # "From Task": str
    # "To Task": str


@dataclass
class ResourceAllocationMetrics:
    """Metrics for resource allocation effectiveness"""
    total_workers: int 
    total_crew_hours: int
    total_subcontractor_hours: int
    average_worker_utilization: float  # 0-1
    average_reliability_score: float  # 0-1
    under_utilized_workers: List[str]
    over_utilized_workers: List[str]
    skill_gaps: Dict[str, int]  # skill -> missing count
    cost_per_hour_weighted_avg: float
    projected_on_time_completion_percent: float  # 0-1
    projected_total_cost: float
