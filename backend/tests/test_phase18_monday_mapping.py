"""
End-to-end dry-run test: ensure Phase 18 workforce outputs map to monday columns

This test is CI-safe: it does not call the Monday API and uses the local
`scripts.phase9.monday_mapping` helpers to validate column/value translation.
"""
from phase18_workforce_analyzer import WorkforceReliabilityAnalyzer
from phase18_workforce_integration import create_workforce_risk_update
from phase18_workforce_types import Worker, AttendanceRecord, AttendanceStatus, WorkerRole
from scripts.phase9.monday_mapping import canonicalize_columns, row_to_column_values


def test_phase18_to_monday_mapping_roundtrip():
    analyzer = WorkforceReliabilityAnalyzer()

    # Add a single worker with mostly present attendance
    w = Worker(worker_id="W100", name="Test Worker", role=WorkerRole.LABORER)
    analyzer.add_worker(w)

    # 5 days of presence
    for i in range(5):
        record = AttendanceRecord(
            shift_date=f"2025-01-0{i+1}",
            shift_id=f"S{i}",
            status=AttendanceStatus.PRESENT,
            scheduled_start="08:00",
            actual_start="08:00",
            scheduled_end="17:00",
            actual_end="17:00",
            minutes_late=0,
            project_id="P100",
            task_id="W100",
        )
        analyzer.add_attendance_record(record)

    intelligence = analyzer.create_project_intelligence(
        project_id="P100",
        project_name="DryRun Project",
        worker_ids=["W100"],
        team_ids=[],
    )

    update = create_workforce_risk_update(intelligence)
    assert "monday_updates" in update
    monday_updates = update["monday_updates"]

    # Prepare a canonical columns map (placeholders) and a row produced from workforce output
    cols = {"predicted_delay": "P_DELAY", "revenue": "P_REV", "risk": "P_RISK", "status": "P_STATUS"}
    canonical = canonicalize_columns(cols)

    row = {
        "predicted_delay": monday_updates.get("schedule_impact_estimate", "0 days"),
        "revenue": monday_updates.get("cost_impact_estimate", "$0"),
        "risk": monday_updates.get("workforce_reliability", 1.0),
        "status": monday_updates.get("workforce_risk_flag", "no"),
    }

    mapping = row_to_column_values(row, canonical)

    # Ensure mapping keys exist and values are strings
    assert isinstance(mapping, dict)
    for v in mapping.values():
        assert isinstance(v, str)

    # Risk column should be present and equal to the workforce_reliability coerced to string
    expected_risk = str(row["risk"])
    risk_col_id = canonical.get("risk")
    assert risk_col_id in mapping
    assert mapping[risk_col_id] == expected_risk
