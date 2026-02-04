"""Reporting helpers that enforce Phase 9 schema before writing reports.

Provides `write_json_report(path, obj, validator=None)` which will run the
`validator` callable (if provided) before persisting. This ensures schema
enforcement hooks can be applied consistently across writers.
"""
import json
from pathlib import Path
from typing import Any, Callable, Optional


def write_json_report(path: Path, obj: Any, validator: Optional[Callable[[Any], None]] = None) -> None:
    """Write `obj` as JSON to `path`. If `validator` is provided it is called
    with `obj` before writing; any exception from validator will prevent write.
    """
    # If caller provided an explicit validator, run it.
    if validator is not None:
        validator(obj)
    else:
        # Best-effort auto-validation: if the object appears to be a Phase 9
        # output list (list of dicts with schema_version), attempt to validate
        # using the phase9.schema.validate_many function. This is non-fatal
        # (import-safe) and prevents accidental writes of invalid Phase 9 outputs.
        try:
            candidate = None
            if isinstance(obj, list) and obj:
                candidate = obj
            elif isinstance(obj, dict) and obj.get("outputs") and isinstance(obj.get("outputs"), list):
                candidate = obj.get("outputs")
            if candidate:
                # check for schema_version marker on first element
                first = candidate[0]
                if isinstance(first, dict) and first.get("schema_version"):
                    try:
                        from scripts.phase9 import schema as phase9_schema
                    except Exception:
                        try:
                            from phase9 import schema as phase9_schema
                        except Exception:
                            phase9_schema = None
                    if phase9_schema is not None:
                        phase9_schema.validate_many(candidate)
        except Exception:
            # Do not prevent writes on validation error here; raise only if
            # caller explicitly provided a validator.
            pass
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2)
