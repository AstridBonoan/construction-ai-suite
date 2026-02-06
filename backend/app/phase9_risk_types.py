"""
Data Types for Feature 9: Multi-Factor AI Risk Synthesis
Aggregates risk factors from Features 1-8 into holistic project risk intelligence
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class RiskCategory(Enum):
    """Risk factor categories from prior features"""
    COST = "cost"  # Feature 1
    SCHEDULE = "schedule"  # Feature 2
    WORKFORCE = "workforce"  # Feature 3
    SUBCONTRACTOR = "subcontractor"  # Feature 4
    EQUIPMENT = "equipment"  # Feature 5
    MATERIALS = "materials"  # Feature 6
    COMPLIANCE = "compliance"  # Feature 7
    ENVIRONMENTAL = "environmental"  # Feature 8


class RiskSeverity(Enum):
    """Risk severity classification"""
    LOW = "low"  # 0.0-0.25
    MEDIUM = "medium"  # 0.25-0.50
    HIGH = "high"  # 0.50-0.75
    CRITICAL = "critical"  # 0.75-1.0


class AggregationMethod(Enum):
    """Risk aggregation method"""
    WEIGHTED_AVERAGE = "weighted_average"  # Weighted mean across factors
    MAXIMUM = "maximum"  # Worst-case scenario
    COMPOUND = "compound"  # Multiplicative risk accumulation
    HIERARCHICAL = "hierarchical"  # Dependency-aware aggregation


@dataclass
class RiskFactorInput:
    """Individual risk factor from a feature"""
    category: RiskCategory
    score: float  # 0.0-1.0
    severity: Optional[RiskSeverity] = None
    confidence: float = 1.0  # 0.0-1.0, trust level
    contributing_issues: List[str] = field(default_factory=list)  # What's driving the risk
    trend: str = "stable"  # stable, increasing, decreasing
    timestamp: str = ""  # When this factor was calculated


@dataclass
class FactorContribution:
    """How much a single factor contributes to overall risk"""
    category: RiskCategory
    raw_score: float  # Original 0-1 score
    normalized_score: float  # Adjusted for weighting
    weight: float  # Percentage of overall risk (0-1)
    contribution_to_total: float  # Actual impact on final score (0-1)
    reason: str  # Human-readable why it matters
    recommendations: List[str] = field(default_factory=list)  # Mitigation actions


@dataclass
class MultiFactorRiskInput:
    """Complete input aggregating risks from Features 1-8"""
    project_id: str
    task_id: Optional[str] = None
    timestamp: str = ""
    
    # Risk factors from each feature
    cost_risk: Optional[RiskFactorInput] = None  # Feature 1
    schedule_risk: Optional[RiskFactorInput] = None  # Feature 2
    workforce_risk: Optional[RiskFactorInput] = None  # Feature 3
    subcontractor_risk: Optional[RiskFactorInput] = None  # Feature 4
    equipment_risk: Optional[RiskFactorInput] = None  # Feature 5
    materials_risk: Optional[RiskFactorInput] = None  # Feature 6
    compliance_risk: Optional[RiskFactorInput] = None  # Feature 7
    environmental_risk: Optional[RiskFactorInput] = None  # Feature 8
    
    # Context
    project_phase: str = "planning"  # planning, execution, closing
    criticality: str = "medium"  # low, medium, high, critical
    dependencies_count: int = 0  # Number of external dependencies
    stakeholder_confidence: float = 0.7  # 0-1, how confident stakeholders are


@dataclass
class SynthesizedRiskMetric:
    """Single synthesized risk metric with explanation"""
    metric_name: str  # e.g., "Overall Project Risk", "Cost Overrun Risk"
    score: float  # 0.0-1.0
    severity: RiskSeverity
    confidence: float  # 0.0-1.0, how certain we are
    primary_drivers: List[str]  # Top 3 factors driving this risk
    secondary_drivers: List[str]  # Contributing but less critical
    explanation: str  # Human-readable explanation
    trend: str  # stable, increasing, decreasing
    outlook_next_14_days: str  # Expected short-term behavior


@dataclass
class SynthesizedRiskOutput:
    """Complete synthesized risk output for a project or task"""
    synthesis_id: str
    project_id: str
    task_id: Optional[str] = None
    timestamp: str = ""
    
    # Primary metrics
    overall_risk_score: float = 0.0  # Holistic project/task risk (0-1)
    overall_severity: RiskSeverity = RiskSeverity.MEDIUM
    overall_confidence: float = 0.8  # How certain the synthesis is
    
    # Factor-specific metrics
    cost_risk_metric: Optional[SynthesizedRiskMetric] = None
    schedule_risk_metric: Optional[SynthesizedRiskMetric] = None
    workforce_risk_metric: Optional[SynthesizedRiskMetric] = None
    subcontractor_risk_metric: Optional[SynthesizedRiskMetric] = None
    equipment_risk_metric: Optional[SynthesizedRiskMetric] = None
    materials_risk_metric: Optional[SynthesizedRiskMetric] = None
    compliance_risk_metric: Optional[SynthesizedRiskMetric] = None
    environmental_risk_metric: Optional[SynthesizedRiskMetric] = None
    
    # Factor contributions
    factor_contributions: List[FactorContribution] = field(default_factory=list)
    
    # Synthesis reasoning
    primary_risk_drivers: List[str] = field(default_factory=list)  # Top 3 risks
    secondary_risk_drivers: List[str] = field(default_factory=list)  # Next 3
    key_interdependencies: List[str] = field(default_factory=list)  # How risks interact
    
    # Actionable intelligence
    executive_summary: str = ""  # One-sentence executive overview
    detailed_explanation: str = ""  # Full technical explanation
    risk_mitigation_plan: List[str] = field(default_factory=list)  # Recommended actions
    short_term_outlook: str = ""  # Next 2 weeks
    medium_term_outlook: str = ""  # Next 1-2 months
    
    # Aggregation metadata
    aggregation_method: AggregationMethod = AggregationMethod.WEIGHTED_AVERAGE
    input_count: int = 0  # How many factors were included
    missing_factors: List[str] = field(default_factory=list)  # Which features had no data
    
    # Monday.com integration
    monday_risk_status: str = "🟢 Low"  # Emoji-prefixed status
    monday_primary_concern: str = ""  # Main risk for dashboard
    monday_action_items: List[str] = field(default_factory=list)  # Linked to monday tasks


@dataclass
class RiskWeightConfig:
    """Configuration for risk factor weighting"""
    cost_weight: float = 0.18  # Feature 1: 18% of overall risk
    schedule_weight: float = 0.18  # Feature 2: 18%
    workforce_weight: float = 0.15  # Feature 3: 15%
    subcontractor_weight: float = 0.12  # Feature 4: 12%
    equipment_weight: float = 0.12  # Feature 5: 12%
    materials_weight: float = 0.10  # Feature 6: 10%
    compliance_weight: float = 0.10  # Feature 7: 10%
    environmental_weight: float = 0.05  # Feature 8: 5%
    
    # Interaction multipliers
    cost_schedule_interaction: float = 0.1  # Cost overruns compound schedule risk
    schedule_workforce_interaction: float = 0.15  # Schedule pressure increases labor risk
    equipment_schedule_interaction: float = 0.12  # Equipment failures impact timeline
    compliance_safety_interaction: float = 0.08  # Compliance gaps increase safety risk
    
    # Phase-specific adjustments
    planning_phase_boost: float = 1.0  # Risks uniform in planning
    execution_phase_boost: float = 1.3  # Risks amplified during execution (30%)
    closing_phase_boost: float = 0.7  # Risks diminish in closing
    
    def total_weight(self) -> float:
        """Verify weights sum to 1.0"""
        return (
            self.cost_weight + self.schedule_weight + self.workforce_weight +
            self.subcontractor_weight + self.equipment_weight + self.materials_weight +
            self.compliance_weight + self.environmental_weight
        )


@dataclass
class RiskPropagationPath:
    """Tracks how a risk flows through project structure"""
    source_task_id: str  # Where risk originated
    source_feature: RiskCategory  # Which feature detected it
    affected_task_ids: List[str]  # Direct dependencies affected
    propagation_strength: float  # 0-1: how strongly it propagates
    time_to_impact_hours: int  # When impact will be felt
    estimated_cost_impact: Optional[float] = None  # Actual cost increase
    estimated_schedule_impact: Optional[int] = None  # Days of delay


@dataclass
class RiskComparison:
    """Compare risk across multiple scenarios or time periods"""
    baseline_score: float  # Current risk
    if_mitigated_score: float  # Risk after mitigation
    best_case_score: float  # Optimistic scenario
    worst_case_score: float  # Pessimistic scenario
    probability_baseline: float  # 0-1, chance baseline occurs
    probability_mitigated: float  # 0-1, chance mitigation works
    confidence_baseline: float  # How certain we are of baseline
    confidence_worst: float  # How certain of worst case


@dataclass
class RiskAlert:
    """Alert when risk crosses threshold"""
    alert_id: str
    project_id: str
    task_id: Optional[str] = None
    risk_category: RiskCategory
    alert_type: str  # threshold_exceeded, trend_negative, interaction_detected
    severity: RiskSeverity
    triggered_at: str  # ISO datetime
    threshold_value: float
    current_value: float
    message: str
    recommended_action: str
    escalation_level: int = 1  # 1=info, 2=warning, 3=critical
