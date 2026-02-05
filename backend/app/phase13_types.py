"""
Phase 13 Feedback Schema (Frozen v1.0) - Python Implementation

Strict, immutable schema for capturing analyst decisions on Phase 12 recommendations.
This schema is versioned and MUST NOT CHANGE without major version bump.

Philosophy: Evidence collection for future improvement (no learning, no inference yet)
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum
import json


class AnalystAction(str, Enum):
    """Analyst action on a recommendation"""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ReasonCode(str, Enum):
    """Structured reason codes for feedback decisions (controlled vocabulary)"""
    
    # Acceptance reasons
    ALIGNS_WITH_PLAN = "aligns_with_plan"
    RISK_JUSTIFIES_ACTION = "risk_justifies_action"
    TIMING_OPTIMAL = "timing_optimal"
    BUDGET_AVAILABLE = "budget_available"
    TEAM_CAPACITY = "team_capacity"
    STAKEHOLDER_AGREEMENT = "stakeholder_agreement"
    
    # Rejection reasons
    ALREADY_PLANNED = "already_planned"
    BUDGET_INSUFFICIENT = "budget_insufficient"
    TIMING_INAPPROPRIATE = "timing_inappropriate"
    TEAM_UNAVAILABLE = "team_unavailable"
    STAKEHOLDER_DISAGREEMENT = "stakeholder_disagreement"
    RISK_ACCEPTABLE = "risk_acceptable"
    CONFLICTING_PRIORITY = "conflicting_priority"
    INSUFFICIENT_CONFIDENCE = "insufficient_confidence"
    ALTERNATIVE_APPROACH = "alternative_approach"
    
    # Modification reasons
    SCOPE_REDUCTION = "scope_reduction"
    IMPLEMENTATION_CHANGE = "implementation_change"
    TIMELINE_ADJUSTMENT = "timeline_adjustment"
    BUDGET_CONSTRAINT = "budget_constraint"
    RESOURCE_ALLOCATION = "resource_allocation"
    STAKEHOLDER_FEEDBACK = "stakeholder_feedback"
    ADDITIONAL_VALIDATION_NEEDED = "additional_validation_needed"


class ModificationConfidence(str, Enum):
    """Confidence in modified approach"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FeedbackRecord:
    """
    Feedback from analyst on a Phase 12 recommendation.
    
    Immutable once written. Links recommendation back to project context,
    analyst decision, and structured reasoning.
    
    This is the foundation for future feedback aggregation and (much later)
    potential retraining - but Phase 13 is ONLY capture and audit, no learning.
    """
    
    # Schema versioning (immutable)
    schema_version: str = "1.0"
    
    # Correlation to Phase 12 & Phase 9
    recommendation_id: str = ""  # From Phase 12
    project_id: str = ""         # From Phase 12 → Phase 9
    
    # Analyst decision (required)
    analyst_action: AnalystAction = AnalystAction.ACCEPTED
    
    # Structured reasoning (required for non-accepted)
    reason_codes: List[str] = field(default_factory=list)  # Multi-select allowed
    
    # Optional structured modification details
    modification_summary: Optional[str] = None
    modification_confidence: Optional[str] = None
    
    # Analyst identity (hashed or pseudonymous)
    analyst_id: str = ""
    
    # Temporal context (ISO 8601)
    decided_at: str = ""  # When analyst made this decision
    
    # Optional: Why changed mind from initial review
    initial_action: Optional[str] = None
    decision_time_seconds: Optional[int] = None
    
    # Audit trail
    recorded_at: str = ""  # When feedback was stored (server timestamp)
    
    # Optional context (never changes recommendations, only for audit)
    notes: Optional[str] = None
    
    # Governance
    is_final: bool = False
    
    def __post_init__(self):
        """Validate feedback record on creation"""
        if not self.recommendation_id:
            raise ValueError("recommendation_id is required")
        if not self.project_id:
            raise ValueError("project_id is required")
        if not self.analyst_id:
            raise ValueError("analyst_id is required")
        if not self.decided_at:
            raise ValueError("decided_at is required (ISO 8601)")
        if not self.recorded_at:
            raise ValueError("recorded_at is required (ISO 8601)")
        if not self.reason_codes:
            raise ValueError("reason_codes is required (at least one)")
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['analyst_action'] = self.analyst_action.value
        if self.initial_action:
            data['initial_action'] = self.initial_action
        if self.modification_confidence:
            data['modification_confidence'] = self.modification_confidence
        return data
    
    def to_jsonl(self) -> str:
        """Convert to JSONL format (one record per line)"""
        return json.dumps(self.to_dict(), separators=(',', ':'))
    
    def make_immutable(self):
        """Mark this record as immutable (final)"""
        self.is_final = True
        return self


# Recommended reason code combinations
REASON_CODE_GUIDANCE = {
    "accepted": [
        ReasonCode.ALIGNS_WITH_PLAN,
        ReasonCode.RISK_JUSTIFIES_ACTION,
        ReasonCode.TIMING_OPTIMAL,
        ReasonCode.BUDGET_AVAILABLE,
        ReasonCode.TEAM_CAPACITY,
        ReasonCode.STAKEHOLDER_AGREEMENT,
    ],
    "rejected": [
        ReasonCode.ALREADY_PLANNED,
        ReasonCode.BUDGET_INSUFFICIENT,
        ReasonCode.TIMING_INAPPROPRIATE,
        ReasonCode.TEAM_UNAVAILABLE,
        ReasonCode.STAKEHOLDER_DISAGREEMENT,
        ReasonCode.RISK_ACCEPTABLE,
        ReasonCode.CONFLICTING_PRIORITY,
        ReasonCode.INSUFFICIENT_CONFIDENCE,
        ReasonCode.ALTERNATIVE_APPROACH,
    ],
    "modified": [
        ReasonCode.SCOPE_REDUCTION,
        ReasonCode.IMPLEMENTATION_CHANGE,
        ReasonCode.TIMELINE_ADJUSTMENT,
        ReasonCode.BUDGET_CONSTRAINT,
        ReasonCode.RESOURCE_ALLOCATION,
        ReasonCode.STAKEHOLDER_FEEDBACK,
        ReasonCode.ADDITIONAL_VALIDATION_NEEDED,
    ],
}


def validate_feedback_record(feedback: FeedbackRecord) -> tuple[bool, Optional[str]]:
    """
    Validate feedback record against schema constraints.
    
    Returns:
        (is_valid, error_message)
    """
    
    # Check required fields
    if not feedback.recommendation_id or not feedback.recommendation_id.strip():
        return False, "recommendation_id cannot be empty"
    
    if not feedback.project_id or not feedback.project_id.strip():
        return False, "project_id cannot be empty"
    
    if not feedback.analyst_id or not feedback.analyst_id.strip():
        return False, "analyst_id cannot be empty"
    
    if not feedback.decided_at or not feedback.decided_at.strip():
        return False, "decided_at must be ISO 8601 timestamp"
    
    if not feedback.recorded_at or not feedback.recorded_at.strip():
        return False, "recorded_at must be ISO 8601 timestamp"
    
    # Check reason codes not empty
    if not feedback.reason_codes or len(feedback.reason_codes) == 0:
        return False, "reason_codes must have at least one code"
    
    # Validate reason codes are in controlled vocabulary
    valid_codes = {rc.value for rc in ReasonCode}
    for code in feedback.reason_codes:
        if code not in valid_codes:
            return False, f"Invalid reason_code: {code}"
    
    # Validate reason codes match action
    action_str = feedback.analyst_action.value if isinstance(feedback.analyst_action, AnalystAction) else feedback.analyst_action
    recommended_codes = {rc.value for rc in REASON_CODE_GUIDANCE[action_str]}
    feedback_codes = set(feedback.reason_codes)
    
    if not feedback_codes.issubset(recommended_codes):
        bad_codes = feedback_codes - recommended_codes
        return False, f"Reason codes {bad_codes} don't match action '{action_str}'"
    
    # For modified action, must have modification_summary
    if feedback.analyst_action == AnalystAction.MODIFIED or feedback.analyst_action == "modified":
        if not feedback.modification_summary or not feedback.modification_summary.strip():
            return False, "modification_summary required for 'modified' action"
    
    return True, None


@dataclass
class FeedbackStorageContract:
    """Schema for feedback storage (append-only, immutable)"""
    schema_version: str = "1.0"
    append_only: bool = True
    immutable_after_write: bool = True
    
    required_fields: List[str] = field(default_factory=lambda: [
        "schema_version",
        "recommendation_id",
        "project_id",
        "analyst_action",
        "reason_codes",
        "analyst_id",
        "decided_at",
        "recorded_at",
        "is_final",
    ])


@dataclass
class FeedbackAnalytics:
    """
    Analytics aggregates computed from feedback (read-only, no mutations).
    
    These are computed from feedback records but NEVER modify recommendations.
    """
    
    # Time range
    period_start: str
    period_end: str
    
    # Counts
    total_feedback_records: int = 0
    
    # Acceptance rates by action type
    acceptance_rates: Dict[str, float] = field(default_factory=dict)
    
    # Rejection reasons frequency
    rejection_reasons: List[Dict[str, any]] = field(default_factory=list)
    
    # Override patterns
    override_patterns: List[Dict[str, any]] = field(default_factory=list)
    
    # Time to decision
    time_to_decision: Dict[str, float] = field(default_factory=dict)
    
    # Analyst consistency
    analyst_consistency: List[Dict[str, any]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict"""
        return asdict(self)
