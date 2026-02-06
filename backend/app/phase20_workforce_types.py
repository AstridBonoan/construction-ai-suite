"""Phase 20 - Workforce Reliability & Attendance Intelligence

Type definitions for workforce performance, attendance patterns, and reliability scoring.
Tracks attendance behavior, identifies risk patterns, and links workforce reliability to
schedule and cost impacts.

Status: Production-ready type definitions (demo data mode)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Literal
from datetime import datetime


@dataclass
class AttendanceRecord:
    """Single workforce attendance/absence event."""
    worker_id: str
    worker_name: str
    date: str  # ISO 8601
    event_type: Literal['present', 'late', 'absent', 'early_departure', 'inspection_miss']
    hours_worked: Optional[float] = None
    minutes_late: Optional[int] = None
    reason_code: Optional[str] = None  # 'illness', 'transport', 'other', 'unknown'
    notes: Optional[str] = None


@dataclass
class WorkerReliabilityScore:
    """Aggregated reliability metrics for a single worker."""
    worker_id: str
    worker_name: str
    role: str  # 'foreman', 'laborer', 'electrician', 'safety_inspector', etc.
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    early_departure_days: int
    inspection_miss_count: int
    
    # Derived metrics (0-1 scale)
    attendance_rate: float  # (present + late where acceptable) / total_days
    punctuality_rate: float  # present_on_time / total_days
    reliability_score: float  # composite (0-1, higher is better)
    
    # Pattern flags (boolean)
    repeat_no_show: bool  # 3+ absences in 30 days
    chronic_lateness: bool  # 5+ late arrivals in 30 days
    inspection_risk: bool  # Inspection miss history
    declining_trend: bool  # Reliability declining over last 30 days
    
    # Risk categorization
    risk_level: Literal['low', 'medium', 'high']
    
    # Human-readable explanation
    explanation: str


@dataclass
class WorkforceImpactFactors:
    """How workforce issues affect schedule and cost."""
    project_id: str
    analysis_datetime: str  # ISO 8601
    
    # Schedule impacts
    critical_roles_at_risk: List[str]  # roles with high absence/lateness
    estimated_schedule_slippage_days: float
    productivity_loss_factor: float  # 0-1 multiplier on team output
    
    # Cost impacts
    overtime_acceleration_estimate: float  # days
    rework_risk_multiplier: float  # 1.0 = baseline
    
    # Specific risks
    inspection_delays_days: float
    regulatory_no_show_risk_pct: float  # likelihood inspection will fail due to staffing
    
    # Explanations
    detailed_risks: List[str]
    recommended_staffing_actions: List[str]


@dataclass
class ProjectWorkforceIntelligence:
    """Project-level workforce intelligence and risk synthesis."""
    project_id: str
    analysis_datetime: str  # ISO 8601
    
    # Workforce composition
    total_workers: int
    workers_by_role: Dict[str, int]
    
    # Workforce health
    team_reliability_score: float  # weighted average (0-1)
    high_risk_worker_count: int
    medium_risk_worker_count: int
    low_risk_worker_count: int
    
    # Integration with project risk
    workforce_risk_contribution_pct: float  # % of overall project risk attributable to workforce
    
    # Schedule/cost impact
    impact_factors: WorkforceImpactFactors
    
    # Summary
    summary: str
    confidence: Literal['high', 'medium', 'low']


def workforce_to_dict(obj: object) -> dict:
    """Serialize phase20 dataclass to dict."""
    if isinstance(obj, (AttendanceRecord, WorkerReliabilityScore, WorkforceImpactFactors, ProjectWorkforceIntelligence)):
        return asdict(obj)
    raise TypeError(f"Cannot serialize {type(obj)}")
