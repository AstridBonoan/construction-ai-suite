"""
Phase 12: Decision Support & Recommendation Engine (Python)

Transforms Phase 9 intelligence into deterministic, traceable decision guidance.
All recommendations are advisory-only, with full traceability to Phase 9.

Core Principle: DEFENSIBLE DECISION SUPPORT
- Every recommendation traced to specific Phase 9 factors
- No auto-execution capabilities
- Deterministic output (same input → same output always)
"""

from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime
import uuid
import json


@dataclass
class RecommendationTraceability:
    """Links recommendation back to Phase 9 intelligence."""
    source_phase: str  # "phase9"
    risk_score: float
    delay_probability: float
    linked_risk_factors: List[str]
    confidence_score: Optional[float] = None


@dataclass
class Recommendation:
    """Individual decision recommendation derived from Phase 9."""
    recommendation_id: str
    project_id: str
    recommended_action: str  # Constrained to action library
    confidence_level: str  # high, medium, low
    supporting_risks: List[str]
    tradeoffs: str
    no_action_risk: str
    rationale: str
    traceability: RecommendationTraceability
    timestamp: str
    is_advisory: bool = True  # Always True - cannot be executed


@dataclass
class DecisionOutput:
    """Complete decision support output for a project."""
    schema_version: str  # "phase12-v1"
    project_id: str
    source_phase: str  # "phase9"
    recommendations: List[Recommendation]
    summary: str
    analyst_context: Optional[str] = None
    generated_at: str = None
    deterministic_seed: Optional[str] = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.utcnow().isoformat() + 'Z'


# Action library - allowed actions only
ACTION_LIBRARY = {
    'schedule_buffer_increase': 'Increase project buffer time',
    'subcontractor_review': 'Review subcontractor performance and contracts',
    'material_procurement_check': 'Expedite material procurement',
    'site_inspection_priority': 'Prioritize site inspections',
    'monitoring_only': 'Increase monitoring frequency, no interventions'
}

# Risk-to-action mapping (deterministic rules)
RISK_ACTION_RULES = {
    'schedule_slippage_pct': ['schedule_buffer_increase', 'monitoring_only'],
    'subcontractor_changes': ['subcontractor_review', 'monitoring_only'],
    'inspection_failure_rate': ['site_inspection_priority', 'monitoring_only'],
    'material_delays': ['material_procurement_check', 'monitoring_only'],
    'weather_impact': ['monitoring_only'],
    'labor_shortage': ['subcontractor_review', 'monitoring_only']
}


def generate_recommendation_id(project_id: str, action: str, index: int) -> str:
    """Deterministic recommendation ID based on project, action, and index."""
    seed = f"{project_id}-{action}-{index}"
    # Use deterministic UUID generation
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed))


def map_risk_to_actions(risk_factor: str) -> List[str]:
    """Deterministically map risk factors to actions."""
    return RISK_ACTION_RULES.get(risk_factor, ['monitoring_only'])


def generate_recommendations(phase9_output: dict) -> DecisionOutput:
    """
    Deterministically generate recommendations from Phase 9 intelligence.
    
    Args:
        phase9_output: Phase 9 intelligence output (dict)
        
    Returns:
        DecisionOutput with traceable recommendations
    """
    project_id = phase9_output.get('project_id', 'UNKNOWN')
    risk_score = phase9_output.get('risk_score', 0.0)
    delay_probability = phase9_output.get('delay_probability', 0.0)
    risk_factors = phase9_output.get('primary_risk_factors', [])
    confidence_score = phase9_output.get('confidence_score')
    explanation = phase9_output.get('explanation', '')

    recommendations = []
    recommended_actions_set = set()

    # Rule 1: High-risk projects get schedule review
    if risk_score > 0.7:
        recommended_actions_set.add('schedule_buffer_increase')

    # Rule 2: High delay probability triggers monitoring
    if delay_probability > 0.6:
        recommended_actions_set.add('monitoring_only')

    # Rule 3: Map specific risk factors to actions
    for rf in risk_factors:
        factor_name = rf.get('factor') if isinstance(rf, dict) else rf
        mapped_actions = map_risk_to_actions(factor_name)
        recommended_actions_set.update(mapped_actions)

    # Rule 4: Extreme risk triggers inspection priority
    if risk_score > 0.8:
        recommended_actions_set.add('site_inspection_priority')

    # Generate recommendation for each action (deterministic order)
    for idx, action in enumerate(sorted(recommended_actions_set)):
        rec_id = generate_recommendation_id(project_id, action, idx)
        
        # Determine confidence level (deterministic)
        if risk_score > 0.7:
            conf_level = 'high'
        elif risk_score > 0.5:
            conf_level = 'medium'
        else:
            conf_level = 'low'

        # Generate supporting risks from Phase 9 factors
        supporting_risks = [
            rf.get('factor') if isinstance(rf, dict) else rf
            for rf in risk_factors
        ]

        # Generate rationale (deterministic text)
        rationale = f"Risk score {risk_score:.0%} and delay probability {delay_probability:.0%} indicate {action.replace('_', ' ')} is warranted. "
        if supporting_risks:
            rationale += f"Primary factors: {', '.join(supporting_risks)}."

        # Generate tradeoffs (construction-specific)
        tradeoffs_map = {
            'schedule_buffer_increase': 'May increase project duration and cost. Benefits: reduced schedule risk.',
            'subcontractor_review': 'Requires management time. Benefits: stability and performance assurance.',
            'material_procurement_check': 'May advance spending timeline. Benefits: material availability assurance.',
            'site_inspection_priority': 'Increases inspection costs. Benefits: early defect detection.',
            'monitoring_only': 'Minimal cost. Benefits: data visibility without intervention.'
        }
        tradeoffs = tradeoffs_map.get(action, 'Requires resources.')

        # Generate no_action_risk
        no_action_risk_map = {
            'schedule_buffer_increase': f'{delay_probability:.0%} probability of project delay.',
            'subcontractor_review': 'Risk of continued performance issues or unexpected departures.',
            'material_procurement_check': 'Material shortages could halt construction.',
            'site_inspection_priority': f'Undetected quality issues may compound; risk score is {risk_score:.0%}.',
            'monitoring_only': 'Risks remain unaddressed; only awareness is increased.'
        }
        no_action_risk = no_action_risk_map.get(action, 'Risks may escalate.')

        traceability = RecommendationTraceability(
            source_phase='phase9',
            risk_score=risk_score,
            delay_probability=delay_probability,
            linked_risk_factors=supporting_risks,
            confidence_score=confidence_score
        )

        rec = Recommendation(
            recommendation_id=rec_id,
            project_id=project_id,
            recommended_action=action,
            confidence_level=conf_level,
            supporting_risks=supporting_risks,
            tradeoffs=tradeoffs,
            no_action_risk=no_action_risk,
            rationale=rationale,
            traceability=traceability,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            is_advisory=True
        )
        recommendations.append(rec)

    # Generate summary
    action_summary = ', '.join(sorted(recommended_actions_set)) if recommended_actions_set else 'monitoring_only'
    summary = (
        f"Project {project_id}: Risk score {risk_score:.0%}, "
        f"Delay probability {delay_probability:.0%}. "
        f"Recommended actions: {action_summary}. "
        f"All recommendations are advisory and require analyst review."
    )

    decision_output = DecisionOutput(
        schema_version='phase12-v1',
        project_id=project_id,
        source_phase='phase9',
        recommendations=recommendations,
        summary=summary,
        analyst_context='Analysts should review recommendations for feasibility and appropriateness in project context.'
    )

    return decision_output


def serialize_decision_output(decision_output: DecisionOutput) -> dict:
    """Convert DecisionOutput to JSON-serializable dict."""
    return {
        'schema_version': decision_output.schema_version,
        'project_id': decision_output.project_id,
        'source_phase': decision_output.source_phase,
        'recommendations': [
            {
                'recommendation_id': rec.recommendation_id,
                'project_id': rec.project_id,
                'recommended_action': rec.recommended_action,
                'confidence_level': rec.confidence_level,
                'supporting_risks': rec.supporting_risks,
                'tradeoffs': rec.tradeoffs,
                'no_action_risk': rec.no_action_risk,
                'rationale': rec.rationale,
                'traceability': {
                    'source_phase': rec.traceability.source_phase,
                    'risk_score': rec.traceability.risk_score,
                    'delay_probability': rec.traceability.delay_probability,
                    'linked_risk_factors': rec.traceability.linked_risk_factors,
                    'confidence_score': rec.traceability.confidence_score
                },
                'timestamp': rec.timestamp,
                'is_advisory': rec.is_advisory
            }
            for rec in decision_output.recommendations
        ],
        'summary': decision_output.summary,
        'analyst_context': decision_output.analyst_context,
        'generated_at': decision_output.generated_at,
        'deterministic_seed': decision_output.deterministic_seed or project_id
    }
