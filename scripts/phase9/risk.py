"""Deterministic risk scoring and explanation helpers.

The scoring is a simple weighted linear combination over authoritative
features. We normalize to 0.0-1.0. Thresholds are documented here and fixed.
"""
from typing import Dict, List, Tuple

# simple weight table: feature -> weight contribution (positive increases risk)
# These weights are intentionally explicit and small in number for auditability.
WEIGHTS = {
    "schedule_slippage_pct": 0.5,
    "avg_delay_last_3_periods": 0.25,
    "subcontractor_changes": 0.12,
    "inspection_failure_rate": 0.08,
    "rolling_weekly_weather_volatility": 0.05,
}

# Normalize each raw input via a feature-specific transformer. Each transformer
# returns a value expected roughly in 0..1.
def _normalize_schedule_slippage(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    # cap extreme values; negative slippage reduces risk
    return max(0.0, min(1.0, v))

def _normalize_avg_delay(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    # scale typical delays (days) into 0..1 by dividing by 30, cap
    return max(0.0, min(1.0, v / 30.0))

def _normalize_count(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    # treat counts: 0 -> 0, 1 -> 0.2, 5+ -> 1.0
    if v <= 0:
        return 0.0
    if v == 1:
        return 0.2
    return min(1.0, v / 5.0)

def _normalize_rate(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, v))

NORMALIZERS = {
    "schedule_slippage_pct": _normalize_schedule_slippage,
    "avg_delay_last_3_periods": _normalize_avg_delay,
    "subcontractor_changes": _normalize_count,
    "inspection_failure_rate": _normalize_rate,
    "rolling_weekly_weather_volatility": _normalize_rate,
}

RISK_THRESHOLDS = {
    "low": 0.0,
    "medium": 0.25,
    "high": 0.6,
    "critical": 0.85,
}


def score(features: Dict[str, float]) -> Tuple[float, List[Dict[str, float]]]:
    """Compute normalized risk score (0.0-1.0) and return factor breakdown.

    Returns (risk_score, breakdown) where breakdown is ordered list of {factor, weight, contribution}.
    """
    contributions = []
    total_raw = 0.0
    # compute contributions
    for feat, w in WEIGHTS.items():
        normalizer = NORMALIZERS.get(feat, lambda x: 0.0)
        raw_val = features.get(feat, 0)
        norm = normalizer(raw_val)
        contrib = norm * w
        contributions.append({"factor": feat, "weight": w, "value": norm, "contribution": contrib})
        total_raw += contrib

    # total_raw is already in 0..sum(weights); normalize by sum(weights)
    weight_sum = sum(WEIGHTS.values())
    if weight_sum <= 0:
        normalized = 0.0
    else:
        normalized = max(0.0, min(1.0, total_raw / weight_sum))

    # sort breakdown by contribution desc
    breakdown = sorted(contributions, key=lambda x: x["contribution"], reverse=True)
    return normalized, breakdown


def risk_level_from_score(score_val: float) -> str:
    if score_val >= RISK_THRESHOLDS["critical"]:
        return "critical"
    if score_val >= RISK_THRESHOLDS["high"]:
        return "high"
    if score_val >= RISK_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def explain_score(score_val: float, breakdown: List[Dict[str, float]]) -> str:
    pieces = []
    for item in breakdown[:3]:
        name = item["factor"]
        contrib = item["contribution"]
        pieces.append(f"{name} (+{contrib:.2f})")
    return ", ".join(pieces)
