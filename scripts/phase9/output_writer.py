"""Phase 9 output writer: validates outputs against the Phase 9 schema and
persists them using the shared reporting helper.

This module provides a single entrypoint `write_phase9_outputs(path, outputs)`
which will raise ValueError when validation fails.
"""
from pathlib import Path
from typing import List, Dict, Any

from . import reporting

try:
    from . import schema as phase9_schema
except Exception:
    try:
        from scripts.phase9 import schema as phase9_schema
    except Exception:
        phase9_schema = None


def write_phase9_outputs(path: Path, outputs: List[Dict[str, Any]]) -> None:
    """Validate Phase 9 outputs and write to `path`.

    Raises ValueError if validation fails.
    """
    if phase9_schema is None:
        # best-effort: attempt to import runtime schema when possible
        raise RuntimeError("phase9.schema is unavailable; cannot validate outputs")

    # validate (will raise ValueError on first failure)
    phase9_schema.validate_many(outputs)

    # write using reporting helper; pass explicit validator for clarity
    reporting.write_json_report(path, outputs, validator=lambda o: phase9_schema.validate_many(o))
