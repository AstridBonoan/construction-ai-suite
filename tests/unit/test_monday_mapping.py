from scripts.phase9 import monday_mapping


def test_canonicalize_columns_defaults():
    cols = {}
    canon = monday_mapping.canonicalize_columns(cols)
    assert "project_id" in canon
    assert canon["project_id"].endswith("_COLUMN_PLACEHOLDER")


def test_row_to_column_values():
    cols = {"predicted_delay": "col_pd", "revenue": "col_rev", "risk": "col_r", "status": "col_s"}
    row = {"predicted_delay": 5, "revenue": 1000, "risk": "high", "status": "active"}
    mapping = monday_mapping.row_to_column_values(row, cols)
    assert mapping["col_pd"] == "5"
    assert mapping["col_rev"] == "1000"
    assert mapping["col_r"] == "high"
    assert mapping["col_s"] == "active"
