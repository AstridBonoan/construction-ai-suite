"""
Phase 19: Integration hooks to feed subcontractor intelligence into core risk engine
and produce monday.com-friendly updates.
"""
import logging
from typing import Dict, Any
from phase19_subcontractor_types import SubcontractorIntelligence

logger = logging.getLogger(__name__)


def _score_to_tier(score: float) -> str:
    if score > 0.8:
        return "excellent"
    if score > 0.6:
        return "good"
    if score > 0.4:
        return "fair"
    if score > 0.2:
        return "poor"
    return "critical"


def feed_subcontractor_to_core_risk_engine(intel: SubcontractorIntelligence) -> None:
    payload = {
        "source": "subcontractor_performance_phase19",
        "project_id": intel.project_id,
        "project_name": intel.project_name,
        "subcontractor_risk_score": intel.subcontractor_risk_score,
        "avg_reliability": intel.project_summary.avg_reliability_score if intel.project_summary else 1.0,
        "high_risk_count": len(intel.project_summary.high_risk_subcontractors) if intel.project_summary else 0,
        "estimated_schedule_impact_days": intel.project_summary.estimated_schedule_impact_days if intel.project_summary else 0.0,
        "estimated_cost_impact": intel.project_summary.estimated_cost_impact if intel.project_summary else 0.0,
        "key_insights": intel.project_summary.key_insights if intel.project_summary else [],
        "recommendations": intel.project_summary.recommendations if intel.project_summary else [],
    }

    try:
        import importlib
        candidates = (
            "backend.app.ml.core_risk_engine",
            "backend.app.core_risk_engine",
            "core_risk_engine",
        )
        core_mod = None
        for c in candidates:
            try:
                core_mod = importlib.import_module(c)
                break
            except ImportError:
                continue

        if core_mod and hasattr(core_mod, "update_project_risk"):
            try:
                core_mod.update_project_risk(payload)
                logger.info("Subcontractor intelligence fed to core risk engine")
            except Exception:
                logger.exception("Failed to call core risk engine with subcontractor payload")
        else:
            logger.debug("Core risk engine not found; logging subcontractor payload")
            logger.debug(payload)
    except Exception:
        logger.exception("Unexpected error while integrating subcontractor intelligence")


def create_subcontractor_risk_update(intel: SubcontractorIntelligence) -> Dict[str, Any]:
    summary = intel.project_summary
    return {
        "project_id": intel.project_id,
        "subcontractor_health_score": 1.0 - intel.subcontractor_risk_score,
        "reliability_tier": _score_to_tier(1.0 - intel.subcontractor_risk_score),
        "has_high_risk_subcontractors": bool(summary and summary.high_risk_subcontractors),
        "recommended_actions": summary.recommendations if summary else [],
        "monday_updates": {
            "subcontractor_reliability": 1.0 - intel.subcontractor_risk_score,
            "predicted_delay_contribution": f"{summary.estimated_schedule_impact_days:.1f} days" if summary else "0 days",
            "subcontractor_risk_flag": "yes" if summary and summary.high_risk_subcontractors else "no",
        }
    }
