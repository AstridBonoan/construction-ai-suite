"""
Data types for Phase 22: Automated Compliance & Safety Intelligence
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime


class RegulationCategory(Enum):
    """Types of regulations and compliance requirements"""
    OSHA_SAFETY = "osha_safety"
    ENVIRONMENTAL = "environmental"
    BUILDING_CODE = "building_code"
    LABOR_LAW = "labor_law"
    FIRE_SAFETY = "fire_safety"
    ELECTRICAL = "electrical_safety"
    HAZMAT = "hazmat"
    ACCESSIBILITY = "accessibility"
    OTHER = "other"


class ViolationSeverity(Enum):
    """Severity levels for compliance violations"""
    MINOR = "minor"
    SERIOUS = "serious"
    WILLFUL = "willful"
    REPEAT = "repeat"
    CRITICAL = "critical"


class InspectionStatus(Enum):
    """Status of compliance/safety inspections"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PASSED = "passed"
    FAILED = "failed"
    FAILED_WITH_VIOLATIONS = "failed_with_violations"


class ComplianceRiskLevel(Enum):
    """Compliance risk classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ShutdownRiskLevel(Enum):
    """Likelihood of project/site shutdown due to violations"""
    NONE = "none"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass
class Regulation:
    """A specific compliance regulation or safety requirement"""
    regulation_id: str
    name: str
    category: RegulationCategory
    description: str = ""
    applicable_industries: List[str] = field(default_factory=list)
    typical_fine_usd: float = 0.0
    is_osha: bool = False
    notes: str = ""


@dataclass
class SafetyInspection:
    """Record of a safety or compliance inspection"""
    inspection_id: str
    project_id: str
    inspection_date: str = ""  # ISO date
    task_id: Optional[str] = None
    site_id: str = ""
    inspection_type: str = ""  # e.g., "routine", "follow-up", "investigation"
    inspector_name: str = ""
    status: InspectionStatus = InspectionStatus.PENDING
    passed: bool = False
    violations_found: int = 0
    notes: str = ""
    follow_up_required: bool = False


@dataclass
class ComplianceViolation:
    """A specific compliance or safety violation found"""
    violation_id: str
    project_id: str
    regulation_id: str
    regulation_name: str
    violation_date: str = ""  # ISO date
    task_id: Optional[str] = None
    severity: ViolationSeverity = ViolationSeverity.SERIOUS
    description: str = ""
    citation_issued: bool = False
    fine_amount_usd: float = 0.0
    mitigation_required: bool = True
    mitigation_deadline: Optional[str] = None  # ISO date
    mitigation_completed: bool = False
    mitigation_completion_date: Optional[str] = None


@dataclass
class MitigationAction:
    """Corrective action to address a violation"""
    action_id: str
    violation_id: str
    project_id: str
    action_description: str
    action_type: str = ""  # e.g., "equipment_upgrade", "training", "process_change"
    estimated_cost_usd: float = 0.0
    target_completion_date: str = ""  # ISO date
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_to: str = ""
    notes: str = ""


@dataclass
class ComplianceHealthSummary:
    """Health summary for a single project's compliance/safety"""
    project_id: str
    project_name: str
    last_inspection_date: Optional[str] = None
    total_inspections: int = 0
    inspections_passed: int = 0
    inspections_failed: int = 0
    active_violations: int = 0
    resolved_violations: int = 0
    total_violations_ever: int = 0
    compliance_risk_score: float = 0.0  # 0.0-1.0
    compliance_risk_level: ComplianceRiskLevel = ComplianceRiskLevel.LOW
    shutdown_risk_score: float = 0.0  # 0.0-1.0
    shutdown_risk_level: ShutdownRiskLevel = ShutdownRiskLevel.NONE
    estimated_fine_exposure_usd: float = 0.0
    days_since_last_inspection: int = 0
    explanation: str = ""
    integration_ready: bool = True
    generated_at: str = ""


@dataclass
class ComplianceRiskInsight:
    """Identified compliance or safety risk"""
    project_id: str
    task_id: Optional[str] = None
    insight_type: str = "violation_risk"  # violation_risk, inspection_overdue, shutdown_risk, citation_likely
    severity: str = "medium"  # low, medium, high, critical
    description: str = ""
    affected_regulations: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    estimated_cost_to_remediate: float = 0.0
    estimated_timeline_days: int = 0
    confidence_percentage: float = 0.0


@dataclass
class ComplianceIntelligence:
    """Project-level compliance and safety intelligence"""
    project_id: str
    project_name: str
    compliance_health_summary: Optional[ComplianceHealthSummary] = None
    compliance_risk_insights: List[ComplianceRiskInsight] = field(default_factory=list)
    active_violations: List[ComplianceViolation] = field(default_factory=list)
    pending_inspections: int = 0
    compliance_risk_score: float = 0.0  # 0.0-1.0 aggregate
    shutdown_risk_score: float = 0.0  # 0.0-1.0
    project_summary: str = ""
    critical_violation_count: int = 0
    estimated_total_fine_exposure: float = 0.0
    audit_ready_status: bool = False
    recommended_immediate_actions: List[str] = field(default_factory=list)
    integration_ready: bool = True
    generated_at: str = ""
    monday_updates: Dict[str, str] = field(default_factory=dict)  # For monday mapping


@dataclass
class AuditReport:
    """Audit-ready compliance report for a project"""
    report_id: str
    project_id: str
    project_name: str
    report_date: str = ""  # ISO datetime
    period_start_date: str = ""  # ISO date
    period_end_date: str = ""  # ISO date
    total_inspections: int = 0
    total_violations: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)  # severity -> count
    critical_findings: List[str] = field(default_factory=list)
    corrective_actions_required: int = 0
    corrective_actions_completed: int = 0
    estimated_financial_exposure: float = 0.0
    compliance_status: str = "in_compliance"  # in_compliance, at_risk, non_compliant
    executive_summary: str = ""
    detailed_findings: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
