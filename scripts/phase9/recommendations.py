"""Rule-first recommendation engine for Phase 9.

Given a project record and risk breakdown, emit structured, explainable
recommendations. Rules are deterministic and auditable.
"""
from typing import Dict, List


def recommendations_from(features: Dict[str, float], risk_score: float, breakdown: List[Dict[str, float]]) -> List[Dict[str, str]]:
    recs = []

    # High-level rules
    if risk_score >= 0.85:
        recs.append({
            "id": "expedite-mitigation",
            "title": "Expedite mitigation planning",
            "reason": "Risk score is critical; convene mitigation and rebaseline schedule.",
        })

    # If schedule slippage is a top contributor
    top = breakdown[0]["factor"] if breakdown else None
    if top == "schedule_slippage_pct":
        recs.append({
            "id": "schedule-audit",
            "title": "Run schedule audit",
            "reason": "Recent schedule slippage is the largest contributor to risk.",
        })

    # Subcontractor churn
    subs = features.get("subcontractor_changes", 0)
    try:
        subs_f = float(subs)
    except Exception:
        subs_f = 0
    if subs_f >= 2:
        recs.append({
            "id": "stabilize-subcontractors",
            "title": "Stabilize subcontractor assignments",
            "reason": f"Detected {int(subs_f)} subcontractor changes; consider lock-in contracts.",
        })

    # Inspection failure handling
    insp = features.get("inspection_failure_rate", 0.0)
    try:
        insp_f = float(insp)
    except Exception:
        insp_f = 0.0
    if insp_f >= 0.2:
        recs.append({
            "id": "quality-review",
            "title": "Initiate quality review",
            "reason": "Inspection failure rate exceeds 20%; review QC processes.",
        })

    # Weather volatility
    wv = features.get("rolling_weekly_weather_volatility", 0.0)
    try:
        wv_f = float(wv)
    except Exception:
        wv_f = 0.0
    if wv_f >= 0.5:
        recs.append({
            "id": "adjust-weather-contingency",
            "title": "Adjust weather contingency",
            "reason": "High recent weather volatility; increase contingency planning.",
        })

    # Phase 20 - Workforce recommendations
    wf_unrel = features.get("workforce_unreliability_score", 0.0)
    try:
        wf_f = float(wf_unrel)
    except Exception:
        wf_f = 0.0
    if wf_f >= 0.4:
        recs.append({
            "id": "improve-attendance",
            "title": "Improve workforce attendance",
            "reason": "Detected workforce unreliability; consider incentives and backup crews.",
        })
    wf_pen = features.get("workforce_pattern_penalty", 0.0)
    try:
        wf_pen_f = float(wf_pen)
    except Exception:
        wf_pen_f = 0.0
    if wf_pen_f >= 0.2:
        recs.append({
            "id": "address-patterns",
            "title": "Address repeated no-shows",
            "reason": "Pattern-based penalties detected; perform crew-level audits and retraining.",
        })

    # Phase 21 - Compliance & Safety recommendations
    incident_p = features.get("safety_incident_probability", 0.0)
    try:
        incident_f = float(incident_p)
    except Exception:
        incident_f = 0.0
    if incident_f >= 0.25:
        recs.append({
            "id": "safety-remediation",
            "title": "Implement safety remediation",
            "reason": "Elevated incident probability; prioritize safety interventions and inspections.",
        })
    comp_exp = features.get("compliance_exposure_score", 0.0)
    try:
        comp_f = float(comp_exp)
    except Exception:
        comp_f = 0.0
    if comp_f >= 0.3:
        recs.append({
            "id": "prepare-audit",
            "title": "Prepare for potential compliance citations",
            "reason": "Compliance exposure is high; ensure documentation and corrective actions.",
        })

    # Always include a simple next-step recommendation
    recs.append({
        "id": "monitor",
        "title": "Monitor and rerun scoring",
        "reason": "Recompute risk daily and track top contributors.",
    })

    return recs
