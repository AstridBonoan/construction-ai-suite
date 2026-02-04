import json
import os
import subprocess
import sys
from pathlib import Path


def test_process_account_config_dry_run(tmp_path, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setenv("MOCK_CENTRAL_HANDLER", "1")
    monkeypatch.setenv("ENABLE_CENTRAL_LOGS", "1")

    # create a minimal CSV
    csv_path = tmp_path / "input.csv"
    csv_path.write_text("project_id,predicted_delay,revenue,risk,status\nproj1,2,1000,low,active\n")

    # prepare a config dict
    cfg = {"board_id": 12345678, "columns": {"project_id": "proj_col", "predicted_delay": "d1", "revenue": "d2", "risk": "d3", "status": "d4"}}

    # import module and run process_account_config directly
    import importlib

    mi = importlib.import_module("scripts.monday_integration")
    out_path, report = mi.process_account_config(cfg, "test_account", csv_path, tmp_path)
    assert out_path.exists()
    assert isinstance(report, dict)


def test_script_runs_dry_run(tmp_path, monkeypatch):
    monkeypatch.setenv("DRY_RUN", "1")
    monkeypatch.setenv("MOCK_CENTRAL_HANDLER", "1")
    monkeypatch.setenv("ENABLE_CENTRAL_LOGS", "1")

    configs = tmp_path / "configs"
    configs.mkdir()
    cfg_file = configs / "test_account.json"
    cfg_file.write_text(json.dumps({"board_id": 12345678, "columns": {"project_id": "proj_col", "predicted_delay": "d1", "revenue": "d2", "risk": "d3", "status": "d4"}}))

    data_dir = tmp_path / "data_splits"
    data_dir.mkdir()
    input_csv = data_dir / "project_level_for_monday.csv"
    input_csv.write_text("project_id,predicted_delay,revenue,risk,status\nproj1,2,1000,low,active\n")

    # run the script as a subprocess pointing to our temp configs and csv
    env = dict(**os.environ)
    env.update({"DRY_RUN": "1", "MOCK_CENTRAL_HANDLER": "1", "ENABLE_CENTRAL_LOGS": "1"})
    cmd = [sys.executable, "scripts/monday_integration.py", "--configs-dir", str(configs)]
    res = subprocess.run(cmd, env=env, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
    assert res.returncode == 0, f"script failed: {res.stdout}\n{res.stderr}"

    # ensure report file exists under reports/
    reports = list((Path(__file__).resolve().parents[2] / "reports").glob("monday_integration_report_*.json"))
    assert reports, "No report files created by script"
