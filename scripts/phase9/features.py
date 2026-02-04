"""Authoritative feature list for delay prediction and risk scoring.

Each feature is documented inline with why it exists and whether it's used for
delay prediction, risk scoring, or both. Experimental/unused features are not
exposed here.
"""
FEATURES = {
    # Core schedule features
    "planned_duration_days": {
        "used_for": ["delay_prediction", "risk_scoring"],
        "description": "Planned project duration in days; core denominator for relative slippage.",
    },
    "elapsed_days": {
        "used_for": ["delay_prediction", "risk_scoring"],
        "description": "Elapsed days since start; used to compute schedule slippage.",
    },
    "schedule_slippage_pct": {
        "used_for": ["delay_prediction", "risk_scoring"],
        "description": "(elapsed - planned) / planned. Primary signal of delays.",
    },

    # Resourcing & procurement
    "subcontractor_changes": {
        "used_for": ["risk_scoring"],
        "description": "Number of subcontractor replacements/firings; indicates churn and risk.",
    },
    "procurement_lags_days": {
        "used_for": ["risk_scoring"],
        "description": "Average days delay in procuring critical items; directly impacts schedule.",
    },

    # Quality & inspection
    "inspection_failure_rate": {
        "used_for": ["risk_scoring"],
        "description": "Fraction of failed inspections over recent window; proxy for rework.",
    },

    # External factors
    "rolling_weekly_weather_volatility": {
        "used_for": ["risk_scoring"],
        "description": "Rolling volatility metric of weather impacting workability.",
    },

    # Derived signals
    "avg_delay_last_3_periods": {
        "used_for": ["delay_prediction", "risk_scoring"],
        "description": "Smoothed recent delay metric to capture trend (lagged/rolling).",
    },
    "pct_tasks_overdue": {
        "used_for": ["delay_prediction"],
        "description": "Percentage of open tasks past their due date; direct operational signal.",
    },

    # Governance/financial
    "cost_variance_pct": {
        "used_for": ["risk_scoring"],
        "description": "Percent deviation of actual vs baseline cost; large variance may indicate trouble.",
    },
}

def authoritative_feature_list():
    """Return a list of features and their docs suitable for generation and
    for use by downstream UI builders.
    """
    out = []
    for name, meta in FEATURES.items():
        out.append({"name": name, "used_for": meta["used_for"], "description": meta["description"]})
    return out
