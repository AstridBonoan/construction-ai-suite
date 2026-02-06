"""Deterministic risk scoring and explanation helpers.

This extends the Phase 9 linear risk scorer with additive inputs from
Phase 20 (Workforce) and Phase 21 (Compliance & Safety) and treats
Phase 22 (IoT / Site Conditions) as multiplicative amplifiers.

The original linear scoring is preserved; new inputs are added with
explicit, auditable weights and simple normalizers to keep outputs
deterministic for demo mode.
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
    # Phase 20 - Workforce (additive)
    "workforce_unreliability_score": 0.06,
    "workforce_pattern_penalty": 0.03,
    # Phase 21 - Compliance & Safety (additive)
    "safety_incident_probability": 0.07,
    "compliance_exposure_score": 0.04,
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


def _normalize_workforce_score(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    # workforce-provided scores are expected 0..1 already; cap
    return max(0.0, min(1.0, v))


def _normalize_incident_probability(raw) -> float:
    try:
        v = float(raw)
    except Exception:
        return 0.0
    # probability 0..1
    return max(0.0, min(1.0, v))


NORMALIZERS = {
    "schedule_slippage_pct": _normalize_schedule_slippage,
    "avg_delay_last_3_periods": _normalize_avg_delay,
    "subcontractor_changes": _normalize_count,
    "inspection_failure_rate": _normalize_rate,
    "rolling_weekly_weather_volatility": _normalize_rate,
    # Phase 20/21 normalizers
    "workforce_unreliability_score": _normalize_workforce_score,
    "workforce_pattern_penalty": _normalize_workforce_score,
    "safety_incident_probability": _normalize_incident_probability,
    "compliance_exposure_score": _normalize_workforce_score,
}


RISK_THRESHOLDS = {
    "low": 0.0,
    "medium": 0.25,
    "high": 0.6,
    "critical": 0.85,
}


def score(features: Dict[str, float]) -> Tuple[float, List[Dict[str, float]]]:
    """Compute normalized risk score (0.0-1.0) and return factor breakdown.

    This function preserves the existing Phase 9 linear scoring and adds
    deterministic, auditable inputs from Phase 20 and Phase 21. Phase 22
    IoT/site signals are applied as a bounded multiplicative amplifier so
    they increase or decrease the final score proportionally rather than
    becoming standalone additive drivers.

    Returns (risk_score, breakdown) where breakdown is ordered list of {factor, weight, value, contribution}.
    """
    contributions = []
    total_raw = 0.0

    # compute core additive contributions (Phase 9 + Phase 20/21)
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

    # keep base value for attribution before IoT amplification
    base_normalized = normalized

    # Phase 22 - IoT/site conditions act as amplifiers (multiplicative)
    # Collect IoT signals if present and compute an amplification factor
    iot_keys = [
        "iot_weather_severity",
        "iot_environmental_hazard_index",
        "iot_activity_anomaly_score",
    ]
    # small per-signal weights to control amplification magnitude
    iot_weight_map = {"iot_weather_severity": 0.6, "iot_environmental_hazard_index": 0.3, "iot_activity_anomaly_score": 0.4}
    iot_norm_total = 0.0
    iot_weight_sum = 0.0
    for k in iot_keys:
        if k in features:
            try:
                v = float(features.get(k, 0))
            except Exception:
                v = 0.0
            v = max(0.0, min(1.0, v))
            w = iot_weight_map.get(k, 0.0)
            iot_norm_total += v * w
            iot_weight_sum += w
            # add to breakdown with zero additive contribution (acts via multiplier)
            contributions.append({"factor": k, "weight": 0.0, "value": v, "contribution": 0.0})

    if iot_weight_sum > 0 and iot_norm_total > 0:
        # Base amplification: between 1.0 and 1.25 depending on IoT severity
        iot_avg = iot_norm_total / iot_weight_sum
        amplification = 1.0 + min(0.25, iot_avg * 0.25)
        normalized = max(0.0, min(1.0, normalized * amplification))
    else:
        amplification = 1.0

    # record IoT amplification as a breakdown entry (small, for explainability)
    iot_added = max(0.0, normalized - base_normalized)
    if iot_added > 0:
        contributions.append({"factor": "iot_amplification", "weight": 0.0, "value": amplification, "contribution": iot_added})

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
        contrib = item.get("contribution", 0.0)
        pieces.append(f"{name} (+{contrib:.2f})")
    return ", ".join(pieces)
