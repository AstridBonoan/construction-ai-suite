"""Phase 9: output schema and validation helpers.

This module defines the canonical output schema (phase9-v1) and functions to
validate project output dicts. Validation is intentionally implemented without
external dependencies so CI remains offline-safe.
"""
from datetime import datetime
from typing import Any, Dict, List

SCHEMA_VERSION = "phase9-v1"

REQUIRED_FIELDS = {
    "project_id": str,
    "project_name": (str, type(None)),
    "risk_score": float,
    "risk_level": str,
    "predicted_delay_days": (float, int, type(None)),
    "confidence_score": float,
    "delay_probability": float,
    "primary_risk_factors": list,
    "recommended_actions": list,
    "explanation": str,
    "model_version": str,
    "generated_at": str,
}


def _type_name(pyobj):
    return type(pyobj).__name__


def validate_project_output(obj: Dict[str, Any]) -> None:
    """Validate a single project output dict against the Phase 9 schema.

    Raises ValueError with a clear message on failure.
    """
    if not isinstance(obj, dict):
        raise ValueError("project output must be a dict")

    # schema version
    ver = obj.get("schema_version")
    if ver != SCHEMA_VERSION:
        raise ValueError(f"invalid schema_version: expected {SCHEMA_VERSION}, got {ver}")

    # required fields and types
    for k, expected in REQUIRED_FIELDS.items():
        if k not in obj:
            raise ValueError(f"missing required field: {k}")
        val = obj[k]
        if not isinstance(val, expected):
            # expected may be tuple of types
            if isinstance(expected, tuple):
                if not any(isinstance(val, t) for t in expected):
                    raise ValueError(f"field '{k}' has wrong type: { _type_name(val)} expected one of {[t.__name__ for t in expected]}")
            else:
                raise ValueError(f"field '{k}' has wrong type: { _type_name(val)} expected {expected.__name__}")

    # validate risk_score range
    rs = obj["risk_score"]
    if not (0.0 <= rs <= 1.0):
        raise ValueError(f"risk_score out of range 0.0-1.0: {rs}")

    cs = obj["confidence_score"]
    if not (0.0 <= cs <= 1.0):
        raise ValueError(f"confidence_score out of range 0.0-1.0: {cs}")

    # primary_risk_factors structure
    prf = obj["primary_risk_factors"]
    if not isinstance(prf, list):
        raise ValueError("primary_risk_factors must be a list")
    for i, item in enumerate(prf):
        if not isinstance(item, dict):
            raise ValueError(f"primary_risk_factors[{i}] must be dict")
        if "factor" not in item or "contribution" not in item:
            raise ValueError(f"primary_risk_factors[{i}] missing 'factor' or 'contribution'")
        # contribution must be numeric and in 0..1
        try:
            c = float(item.get("contribution", 0))
        except Exception:
            raise ValueError("primary_risk_factors.contribution must be numeric")
        if c < 0 or c > 1:
            raise ValueError("primary_risk_factors.contribution must be between 0 and 1")

    # generated_at must be ISO timestamp parseable
    try:
        datetime.fromisoformat(obj["generated_at"])
    except Exception as e:
        raise ValueError(f"generated_at must be ISO timestamp: {e}")

    # delay_probability must be in 0..1
    dp = obj.get("delay_probability")
    try:
        dpf = float(dp)
    except Exception:
        raise ValueError("delay_probability must be numeric")
    if dpf < 0.0 or dpf > 1.0:
        raise ValueError(f"delay_probability out of range 0.0-1.0: {dpf}")

    # explanation must be a non-empty string
    expl = obj.get("explanation")
    if not isinstance(expl, str) or not expl.strip():
        raise ValueError("explanation must be a non-empty string")


def validate_many(outputs: List[Dict[str, Any]]) -> None:
    """Validate a list of outputs; raises first encountered ValueError."""
    for o in outputs:
        validate_project_output(o)
