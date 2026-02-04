from scripts.phase9 import risk, recommendations


def test_risk_score_deterministic():
    features = {
        "schedule_slippage_pct": 0.4,
        "avg_delay_last_3_periods": 5,
        "subcontractor_changes": 2,
        "inspection_failure_rate": 0.15,
        "rolling_weekly_weather_volatility": 0.3,
    }
    s1, b1 = risk.score(features)
    s2, b2 = risk.score(features)
    assert s1 == s2
    assert b1 == b2


def test_recommendations_and_explainability_deterministic():
    features = {
        "schedule_slippage_pct": 0.9,
        "avg_delay_last_3_periods": 10,
        "subcontractor_changes": 3,
        "inspection_failure_rate": 0.25,
        "rolling_weekly_weather_volatility": 0.6,
    }
    score_val, breakdown = risk.score(features)
    r1 = recommendations.recommendations_from(features, score_val, breakdown)
    r2 = recommendations.recommendations_from(features, score_val, breakdown)
    assert r1 == r2
    # explain_score should also be stable
    e1 = risk.explain_score(score_val, breakdown)
    e2 = risk.explain_score(score_val, breakdown)
    assert e1 == e2
