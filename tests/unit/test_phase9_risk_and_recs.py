import pytest

from scripts.phase9 import risk, recommendations


def test_score_basic():
    features = {
        "schedule_slippage_pct": 0.3,
        "avg_delay_last_3_periods": 6,
        "subcontractor_changes": 1,
        "inspection_failure_rate": 0.1,
        "rolling_weekly_weather_volatility": 0.2,
    }
    score_val, breakdown = risk.score(features)
    assert 0.0 <= score_val <= 1.0
    assert isinstance(breakdown, list)


def test_recommendations_trigger():
    features = {"schedule_slippage_pct": 0.9, "subcontractor_changes": 3, "inspection_failure_rate": 0.25, "rolling_weekly_weather_volatility": 0.6}
    score_val, breakdown = risk.score(features)
    recs = recommendations.recommendations_from(features, score_val, breakdown)
    # expect at least the monitor recommendation + others
    ids = {r["id"] for r in recs}
    assert "monitor" in ids
    assert any(r["id"] == "stabilize-subcontractors" for r in recs)
