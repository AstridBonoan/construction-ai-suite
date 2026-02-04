from pathlib import Path
import json

from scripts.phase9 import output_writer


def make_valid_output(tmp_path):
    o = {
        "schema_version": "phase9-v1",
        "project_id": "proj1",
        "project_name": "Project 1",
        "risk_score": 0.5,
        "risk_level": "medium",
        "predicted_delay_days": 3,
        "delay_probability": 0.1,
        "confidence_score": 0.8,
        "primary_risk_factors": [{"factor": "schedule_slippage_pct", "contribution": 0.5}],
        "recommended_actions": ["monitor"],
        "explanation": "Schedule slippage and subcontractor churn are top contributors.",
        "model_version": "v1",
        "generated_at": "2025-01-01T00:00:00",
    }
    return [o]


def test_write_valid_outputs(tmp_path):
    outputs = make_valid_output(tmp_path)
    p = tmp_path / "phase9_outputs.json"
    output_writer.write_phase9_outputs(p, outputs)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data, list)


def test_write_invalid_outputs_raises(tmp_path):
    outputs = make_valid_output(tmp_path)
    # break required field
    outputs[0].pop("risk_score", None)
    p = tmp_path / "bad_phase9.json"
    try:
        output_writer.write_phase9_outputs(p, outputs)
        raised = False
    except ValueError:
        raised = True
    assert raised
