"""
Phase 18: Workforce Reliability & Attendance Intelligence - Data Models

Defines workforce entities for tracking attendance, tardiness, no-shows,
and worker reliability patterns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class AttendanceStatus(Enum):
    """Attendance status for a shift"""
    PRESENT = "present"
    LATE = "late"
    ABSENT = "absent"
    EXCUSED = "excused"
    SICK_LEAVE = "sick_leave"
    VACATION = "vacation"


class WorkerRole(Enum):
    """Role or skill level of a worker"""
    LABORER = "laborer"
    SKILLED_TRADES = "skilled_trades"
    EQUIPMENT_OPERATOR = "equipment_operator"
    SUPERVISOR = "supervisor"
    SUBCONTRACTOR = "subcontractor"
    INSPECTOR = "inspector"


@dataclass
class AttendanceRecord:
    """Single attendance record for a worker"""
    shift_date: str  # ISO format date
    shift_id: str
    status: AttendanceStatus
    scheduled_start: str  # ISO format time
    actual_start: Optional[str] = None  # Null if absent
    scheduled_end: str = ""
    actual_end: Optional[str] = None
    minutes_late: int = 0
    project_id: str = ""
    task_id: str = ""
    notes: str = ""
    monday_task_id: Optional[str] = None  # For monday.com integration


@dataclass
class Worker:
    """Worker or subcontractor entity"""
    worker_id: str
    name: str
    role: WorkerRole
    email: Optional[str] = None
    phone: Optional[str] = None
    team_id: Optional[str] = None
    is_subcontractor: bool = False
    hire_date: Optional[str] = None
    active: bool = True
    monday_user_id: Optional[str] = None  # For monday.com integration


@dataclass
class Team:
    """Team of workers"""
    team_id: str
    team_name: str
    lead_worker_id: Optional[str] = None
    members: List[str] = field(default_factory=list)  # worker_ids
    project_ids: List[str] = field(default_factory=list)
    avg_reliability_score: float = 0.0


@dataclass
class WorkerAttendanceSummary:
    """Summary statistics for a worker's attendance"""
    worker_id: str
    worker_name: str
    total_shifts: int = 0
    shifts_present: int = 0
    shifts_late: int = 0
    shifts_absent: int = 0
    shifts_excused: int = 0
    avg_minutes_late: float = 0.0
    absence_rate: float = 0.0  # 0-1
    tardiness_rate: float = 0.0  # 0-1
    reliability_score: float = 1.0  # 0-1, higher is better
    confidence_score: float = 0.0  # Confidence in the score (0-1)
    explanation: str = ""
    risk_level: str = "low"  # low, medium, high
    recent_pattern: str = ""  # "improving", "stable", "declining"


@dataclass
class TeamAttendanceSummary:
    """Summary statistics for a team's attendance"""
    team_id: str
    team_name: str
    member_count: int = 0
    avg_reliability_score: float = 1.0  # Average of member scores
    total_absences: int = 0
    total_late_shifts: int = 0
    team_risk_level: str = "low"
    explanation: str = ""


@dataclass
class WorkforceRiskInsight:
    """Risk insight linked to schedule/cost impact"""
    worker_id: str
    project_id: str
    task_id: str
    identified_issue: str  # e.g., "chronic_tardiness", "high_absence_rate"
    risk_severity: str  # low, medium, high
    impact_on_schedule: str  # e.g., "5 days delay expected if pattern continues"
    impact_on_cost: str  # e.g., "Lost productivity: $2500"
    confidence_score: float
    recommendation: str
    monday_column_suggestion: Optional[str] = None  # e.g., which monday column to flag


@dataclass
class WorkforceProjectSummary:
    """Project-level workforce reliability summary"""
    project_id: str
    project_name: str
    total_workers: int = 0
    avg_team_reliability: float = 1.0
    high_risk_workers: List[str] = field(default_factory=list)  # worker_ids
    critical_absences_count: int = 0
    total_schedule_risk_days: float = 0.0  # Expected schedule slip due to workforce
    total_cost_impact: float = 0.0  # Expected cost impact due to workforce
    overall_workforce_risk_score: float = 0.0  # 0-1, fed to Feature 1
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class WorkforceIntelligence:
    """Complete workforce intelligence output for Feature 1 integration"""
    project_id: str
    project_name: str
    generated_at: str  # ISO timestamp
    worker_summaries: Dict[str, WorkerAttendanceSummary] = field(default_factory=dict)
    team_summaries: Dict[str, TeamAttendanceSummary] = field(default_factory=dict)
    risk_insights: List[WorkforceRiskInsight] = field(default_factory=list)
    project_summary: Optional[WorkforceProjectSummary] = None
    # Integration with Feature 1
    workforce_risk_score: float = 0.0  # 0-1, to feed into core risk engine
    integration_ready: bool = False
