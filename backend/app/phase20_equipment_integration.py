"""
Phase 20: Equipment Maintenance Integration with Core Risk Engine

Feeds equipment intelligence into Feature 1's project risk engine and
produces monday.com-friendly risk updates.
"""
import logging
from typing import Dict, Any
from phase20_equipment_types import EquipmentIntelligence

logger = logging.getLogger(__name__)


def _score_to_tier(score: float) -> str:
    if score >= 0.7:
        return "critical"
    if score >= 0.5:
        return "high"
    if score >= 0.3:
        return "medium"
    if score >= 0.1:
        return "low"
    return "minimal"


def feed_equipment_to_core_risk_engine(intel: EquipmentIntelligence) -> Dict[str, Any]:
    """Feed equipment intelligence into the core risk engine (Feature 1)."""
    payload = {
        "source": "equipment_maintenance_phase20",
        "project_id": intel.project_id,
        "project_name": intel.project_name,
        "equipment_risk_score": intel.equipment_risk_score,
        "avg_failure_probability": intel.project_summary.avg_failure_probability if intel.project_summary else 0.0,
        "high_risk_count": len(intel.project_summary.high_risk_equipment) if intel.project_summary else 0,
        "estimated_downtime_days": intel.project_summary.estimated_maintenance_downtime_days if intel.project_summary else 0.0,
        "estimated_cost_impact": intel.project_summary.estimated_maintenance_cost if intel.project_summary else 0.0,
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
        
        if core_mod and hasattr(core_mod, "register_equipment_risk"):
            try:
                result = core_mod.register_equipment_risk(payload)
                logger.info("Equipment intelligence fed to core risk engine")
                return result
            except Exception as e:
                logger.exception("Failed to call core risk engine with equipment payload")
                return {"status": "error", "error": str(e)}
        else:
            logger.debug("Core risk engine not found; logging equipment payload")
            logger.debug(payload)
            return {"status": "logged", "source": "phase20_equipment"}
    except Exception as e:
        logger.exception("Unexpected error while integrating equipment intelligence")
        return {"status": "error", "error": str(e)}


def create_equipment_risk_update(intel: EquipmentIntelligence) -> Dict[str, Any]:
    """Create risk update suitable for monday.com or dashboard integration."""
    summary = intel.project_summary
    return {
        "project_id": intel.project_id,
        "equipment_health_score": 1.0 - intel.equipment_risk_score,
        "risk_tier": _score_to_tier(intel.equipment_risk_score),
        "has_critical_equipment": bool(summary and intel.equipment_risk_score > 0.6),
        "recommended_actions": summary.recommendations if summary else [],
        "monday_updates": {
            "equipment_reliability": 1.0 - intel.equipment_risk_score,
            "predicted_downtime_days": f"{summary.estimated_maintenance_downtime_days:.1f}" if summary else "0",
            "equipment_maintenance_flag": "yes" if summary and summary.high_risk_equipment else "no",
        }
    }
