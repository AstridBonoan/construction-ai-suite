"""
Phase 19: Subcontractor Performance Intelligence - Data Models

Defines subcontractor entities, performance records, and structured outputs
used for scoring, explainability, and integration with Feature 1.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Subcontractor:
    subcontractor_id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    monday_vendor_id: Optional[str] = None
    active: bool = True


@dataclass
class SubcontractorPerformanceRecord:
    """A single historical performance event for a subcontractor on a task."""
    project_id: str
    task_id: str
    subcontractor_id: str
    scheduled_finish_date: str  # ISO date
    actual_finish_date: Optional[str] = None  # ISO date or None if not finished
    days_delay: float = 0.0  # positive if late, negative if early
    completed: bool = True
    quality_issues: int = 0  # count of quality defects
    notes: str = ""


@dataclass
class SubcontractorSummary:
    subcontractor_id: str
    subcontractor_name: str
    total_tasks: int = 0
    on_time_count: int = 0
    late_count: int = 0
    avg_days_delay: float = 0.0
    quality_issues: int = 0
    reliability_score: float = 1.0  # 0-1, higher is better
    risk_level: str = "low"  # low/medium/high
    explanation: str = ""


@dataclass
class SubcontractorRiskInsight:
    subcontractor_id: str
    project_id: str
    identified_issue: str
    severity: str  # low/medium/high
    impact_on_schedule: str
    impact_on_cost: str
    confidence: float
    recommendation: str
    monday_column_suggestion: Optional[str] = None


@dataclass
class SubcontractorProjectSummary:
    project_id: str
    project_name: str
    total_subcontractors: int = 0
    avg_reliability_score: float = 1.0
    high_risk_subcontractors: List[str] = field(default_factory=list)
    estimated_schedule_impact_days: float = 0.0
    estimated_cost_impact: float = 0.0
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class SubcontractorIntelligence:
    project_id: str
    project_name: str
    generated_at: str  # ISO timestamp
    subcontractor_summaries: Dict[str, SubcontractorSummary] = field(default_factory=dict)
    risk_insights: List[SubcontractorRiskInsight] = field(default_factory=list)
    project_summary: Optional[SubcontractorProjectSummary] = None
    subcontractor_risk_score: float = 0.0  # 0-1, feeds into core risk engine
    integration_ready: bool = False
