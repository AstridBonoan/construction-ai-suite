"""Canonical monday.com mapping helpers for Phase 9.

Provide deterministic, auditable mapping functions that translate a
project-row dict into the column-id -> value mapping expected by
`monday_integration`'s clients. This module is import-safe and has no
external dependencies.
"""
from typing import Dict, Any


def canonicalize_columns(columns: Dict[str, str]) -> Dict[str, str]:
    """Return a canonical columns mapping with expected keys.

    Ensures the returned dict contains keys for 'project_id', 'predicted_delay',
    'revenue', 'risk', and 'status' (values may be placeholders).
    Non-crashing: missing keys are filled with an explicit placeholder.
    """
    keys = ["project_id", "predicted_delay", "revenue", "risk", "status"]
    out = {}
    for k in keys:
        out[k] = columns.get(k) if isinstance(columns.get(k), str) else f"{k.upper()}_COLUMN_PLACEHOLDER"
    return out


def row_to_column_values(row: Dict[str, Any], columns: Dict[str, str]) -> Dict[str, str]:
    """Map a project `row` to a monday column-values dict using `columns` mapping.

    Values are coerced to strings and placeholder column IDs are left as-is
    -- callers should ensure placeholders are replaced before live runs.
    """
    mapping = {}
    for key in ("predicted_delay", "revenue", "risk", "status"):
        col_id = columns.get(key)
        if not col_id:
            continue
        val = row.get(key, "")
        try:
            mapping[col_id] = str(val)
        except Exception:
            mapping[col_id] = ""
    return mapping
