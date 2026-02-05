"""
Phase 20: Predictive Equipment Maintenance - Data Models

Defines equipment entities, maintenance records, failure events, and
structured outputs for failure risk prediction and integration with Feature 1.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class EquipmentStatus(Enum):
    """Equipment operational status"""
    OPERATIONAL = "operational"
    MAINTENANCE_DUE = "maintenance_due"
    MAINTENANCE_OVERDUE = "maintenance_overdue"
    FAILED = "failed"
    OUT_OF_SERVICE = "out_of_service"


class EquipmentType(Enum):
    """Equipment category"""
    EXCAVATOR = "excavator"
    BULLDOZER = "bulldozer"
    CRANE = "crane"
    CONCRETE_PUMP = "concrete_pump"
    COMPRESSOR = "compressor"
    GENERATOR = "generator"
    OTHER = "other"


@dataclass
class Equipment:
    equipment_id: str
    name: str
    equipment_type: EquipmentType
    acquisition_date: str  # ISO date
    current_status: EquipmentStatus = EquipmentStatus.OPERATIONAL
    monday_asset_id: Optional[str] = None
    active: bool = True


@dataclass
class MaintenanceRecord:
    """Historical maintenance event"""
    project_id: str
    equipment_id: str
    maintenance_date: str  # ISO date
    maintenance_type: str  # "preventive" or "corrective"
    duration_hours: float
    cost: float
    completed: bool = True
    notes: str = ""


@dataclass
class FailureEvent:
    """Historical equipment failure"""
    project_id: str
    task_id: str
    equipment_id: str
    failure_date: str  # ISO date
    failure_type: str  # e.g., "engine_failure", "hydraulic_leak"
    repair_duration_hours: float
    repair_cost: float
    downtime_impact_days: float
    notes: str = ""


@dataclass
class EquipmentHealthSummary:
    equipment_id: str
    equipment_name: str
    total_operational_days: float = 0.0
    total_maintenance_events: int = 0
    total_failure_events: int = 0
    average_maintenance_interval_days: float = 0.0
    days_since_last_maintenance: float = 0.0
    maintenance_cost_total: float = 0.0
    failure_cost_total: float = 0.0
    failure_probability: float = 0.0  # 0-1
    risk_level: str = "low"
    explanation: str = ""


@dataclass
class EquipmentRiskInsight:
    equipment_id: str
    project_id: str
    identified_issue: str
    severity: str
    impact_on_schedule: str
    impact_on_cost: str
    confidence: float
    recommendation: str
    monday_column_suggestion: Optional[str] = None


@dataclass
class EquipmentProjectSummary:
    project_id: str
    project_name: str
    total_equipment: int = 0
    avg_failure_probability: float = 0.0
    high_risk_equipment: List[str] = field(default_factory=list)
    estimated_maintenance_downtime_days: float = 0.0
    estimated_maintenance_cost: float = 0.0
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    explanation: str = ""


@dataclass
class EquipmentIntelligence:
    project_id: str
    project_name: str
    generated_at: str  # ISO timestamp
    equipment_summaries: Dict[str, EquipmentHealthSummary] = field(default_factory=dict)
    risk_insights: List[EquipmentRiskInsight] = field(default_factory=list)
    project_summary: Optional[EquipmentProjectSummary] = None
    equipment_risk_score: float = 0.0  # 0-1, feeds into core risk engine
    integration_ready: bool = False
