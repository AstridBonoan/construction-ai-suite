"""Phase 21 - Automated Compliance & Safety Intelligence

Type definitions for compliance risk scoring, safety incident modeling, and
regulatory audit readiness.

Status: Production-ready type definitions (demo data mode)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Literal
from datetime import datetime


@dataclass
class SafetyIncident:
    """Safety or near-miss event on project."""
    incident_id: str
    project_id: str
    date: str  # ISO 8601
    incident_type: Literal['injury', 'near_miss', 'violation_notice', 'equipment_damage']
    severity: Literal['critical', 'major', 'minor']
    location: str
    involved_workers: List[str]
    root_cause: str
    corrective_action: str
    closed: bool = False


@dataclass
class ComplianceCheckpoint:
    """Single compliance requirement/checkpoint."""
    checkpoint_id: str
    category: Literal['site_safety', 'environmental', 'labor', 'structural', 'building_code', 'accessibility']
    title: str
    description: str
    requirement_id: Optional[str] = None  # OSHA, EPA, etc.


@dataclass
class ComplianceAssessment:
    """Assessment result for a single checkpoint."""
    checkpoint_id: str
    checkpoint_title: str
    assessment_date: str  # ISO 8601
    status: Literal['pass', 'fail', 'warning', 'not_assessed']
    finding: Optional[str] = None
    corrective_action_required: bool = False
    deadline: Optional[str] = None  # ISO 8601, when remediation needed
    remediated: bool = False


@dataclass
class SafetyRiskScore:
    """Aggregated safety and compliance risk for project."""
    project_id: str
    analysis_datetime: str  # ISO 8601
    
    # Historical incidents
    total_incidents: int
    critical_incidents: int
    major_incidents: int
    minor_incidents: int
    near_miss_count: int
    violation_notices: int
    
    # Incident rate (per 100K hours worked, OSHA standard)
    incident_rate: float
    near_miss_rate: float
    
    # Compliance
    total_checkpoints: int
    passed_checkpoints: int
    failed_checkpoints: int
    warning_checkpoints: int
    compliance_score: float  # (passed / total), 0-1
    
    # Risk assessment
    safety_risk_level: Literal['low', 'medium', 'high']
    regulatory_shutdown_probability_pct: float  # likelihood of citation/shutdown
    audit_readiness: Literal['poor', 'fair', 'good']
    
    # Schedule/cost impact
    estimated_rework_days: float
    estimated_citation_cost: float  # financial exposure
    
    # Summary
    summary: str
    open_findings: List[str]
    recommended_actions: List[str]


@dataclass
class ProjectComplianceSafety:
    """Project-level compliance and safety intelligence."""
    project_id: str
    analysis_datetime: str  # ISO 8601
    
    # Safety history
    incidents: List[SafetyIncident]
    safety_risk_score: SafetyRiskScore
    
    # Compliance status
    assessments: List[ComplianceAssessment]
    high_priority_findings: List[str]
    
    # Integration with project risk
    safety_risk_contribution_pct: float  # % of overall project risk
    
    # Audit trail
    last_inspection_date: Optional[str]
    last_inspection_finding: Optional[str]
    upcoming_inspection: bool
    
    # Summary
    summary: str
    confidence: Literal['high', 'medium', 'low']


def compliance_to_dict(obj: object) -> dict:
    """Serialize phase21 dataclass to dict."""
    if isinstance(obj, (SafetyIncident, ComplianceCheckpoint, ComplianceAssessment,
                        SafetyRiskScore, ProjectComplianceSafety)):
        data = asdict(obj)
        # Handle nested lists
        if 'incidents' in data and data['incidents']:
            data['incidents'] = [asdict(i) if not isinstance(i, dict) else i for i in data['incidents']]
        if 'assessments' in data and data['assessments']:
            data['assessments'] = [asdict(a) if not isinstance(a, dict) else a for a in data['assessments']]
        if 'safety_risk_score' in data and data['safety_risk_score']:
            if not isinstance(data['safety_risk_score'], dict):
                data['safety_risk_score'] = asdict(data['safety_risk_score'])
        return data
    raise TypeError(f"Cannot serialize {type(obj)}")
