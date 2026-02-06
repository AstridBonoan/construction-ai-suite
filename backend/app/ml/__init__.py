"""
Demo ml package initializer exposing a minimal core_risk_engine for tests.
DEMO STUB — replaced with full implementation in Phase 16/Integration.
"""
from types import SimpleNamespace
from typing import Any, Optional


class _CoreRiskEngine:
    def __init__(self):
        self.last_update: Optional[Any] = None

    def update(self, payload: Any) -> None:
        # deterministic assignment for test validation
        self.last_update = payload

    def reset(self) -> None:
        self.last_update = None


core_risk_engine = _CoreRiskEngine()

__all__ = ["core_risk_engine"]
