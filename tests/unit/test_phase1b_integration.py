import pytest

from scripts.phase9 import risk, recommendations


def test_workforce_increases_risk_and_recommendation():
    base = {
        "schedule_slippage_pct": 0.1,
        "avg_delay_last_3_periods": 2,
        "subcontractor_changes": 0,
        "inspection_failure_rate": 0.0,
        "rolling_weekly_weather_volatility": 0.1,
    }
    base_score, base_bd = risk.score(base)

    # now add poor workforce reliability
    wf = base.copy()
    wf["workforce_unreliability_score"] = 0.8
    wf_score, wf_bd = risk.score(wf)

    assert wf_score >= base_score

    recs = recommendations.recommendations_from(wf, wf_score, wf_bd)
    ids = {r["id"] for r in recs}
    assert "improve-attendance" in ids


def test_compliance_triggers_audit_and_shutschedule_risk():
    base = {
        "schedule_slippage_pct": 0.05,
        "avg_delay_last_3_periods": 1,
        "subcontractor_changes": 0,
        "inspection_failure_rate": 0.0,
        "rolling_weekly_weather_volatility": 0.05,
    }
    base_score, _ = risk.score(base)

    cmp = base.copy()
    cmp["safety_incident_probability"] = 0.5
    cmp["compliance_exposure_score"] = 0.6
    cmp_score, _ = risk.score(cmp)

    assert cmp_score >= base_score

    recs = recommendations.recommendations_from(cmp, cmp_score, [])
    ids = {r["id"] for r in recs}
    assert "safety-remediation" in ids
    assert "prepare-audit" in ids


def test_iot_amplifies_not_overrides():
    base = {
        "schedule_slippage_pct": 0.2,
        "avg_delay_last_3_periods": 3,
        "subcontractor_changes": 1,
        "inspection_failure_rate": 0.05,
        "rolling_weekly_weather_volatility": 0.1,
    }
    base_score, _ = risk.score(base)

    iot = base.copy()
    iot["iot_activity_anomaly_score"] = 0.9
    iot_score, iot_bd = risk.score(iot)

    # IoT should amplify (increase) the baseline but not act as standalone high risk
    assert iot_score >= base_score
    # amplification should be modest (bounded by design)
    assert iot_score - base_score <= 0.3
