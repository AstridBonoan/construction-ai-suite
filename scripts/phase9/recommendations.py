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

    # Always include a simple next-step recommendation
    recs.append({
        "id": "monitor",
        "title": "Monitor and rerun scoring",
        "reason": "Recompute risk daily and track top contributors.",
    })

    return recs
