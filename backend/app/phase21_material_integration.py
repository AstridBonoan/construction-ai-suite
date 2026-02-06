"""
Integration hooks for Phase 21: Material Ordering & Forecasting
Feeds material risk intelligence into Core Risk Engine (Feature 1)
Provides monday.com data mapping
"""
import logging
from typing import Dict, List, Any, Optional
from phase21_material_types import MaterialIntelligence, MaterialRiskInsight

logger = logging.getLogger(__name__)


def feed_material_to_core_risk_engine(intelligence: MaterialIntelligence) -> Dict[str, Any]:
    """
    Feed material ordering & forecasting intelligence into Feature 1 core risk engine.
    Falls back gracefully if core engine is unavailable (CI-safe).
    """
    payload = {
        "source": "phase_21_material_ordering",
        "project_id": intelligence.project_id,
        "material_risk_score": intelligence.material_risk_score,
        "critical_material_count": intelligence.critical_material_count,
        "schedule_impact_risk": intelligence.schedule_impact_risk,
        "reorder_count": len(intelligence.reorder_recommendations),
        "material_summaries": {
            mid: {
                "material_name": summary.material_name,
                "current_stock": summary.current_stock,
                "stock_status": summary.stock_status.value,
                "days_of_supply": summary.days_of_supply,
                "risks_count": len(summary.risks)
            }
            for mid, summary in intelligence.material_summaries.items()
        },
        "risk_insights": [
            {
                "material_id": insight.material_id,
                "material_name": insight.material_name,
                "insight_type": insight.insight_type,
                "severity": insight.severity,
                "affected_tasks": insight.affected_tasks,
                "estimated_delay_days": insight.estimated_delay_days
            }
            for insight in intelligence.material_risk_insights
        ]
    }
    
    try:
        import importlib
        core_mod = None
        candidates = (
            "backend.app.ml.core_risk_engine",
            "backend.app.core_risk_engine",
            "core_risk_engine",
        )
        for candidate in candidates:
            try:
                core_mod = importlib.import_module(candidate)
                break
            except ImportError:
                continue
        
        if core_mod and hasattr(core_mod, "register_material_risk"):
            result = core_mod.register_material_risk(payload)
            logger.info(f"Phase 21 material risks registered with core engine: {result}")
            return result
        else:
            logger.warning("Core risk engine not available; material risk will be logged locally")
            return {"status": "logged", "source": "phase_21_material_ordering"}
    except Exception as e:
        logger.error(f"Error feeding material risks to core engine: {e}")
        return {"status": "error", "error": str(e)}


def create_material_risk_update(intelligence: MaterialIntelligence) -> Dict[str, Any]:
    """
    Create structured material risk update suitable for monday.com integration
    Returns dict with material-level updates ready for column mapping
    """
    updates_list = []
    
    for material_id, summary in intelligence.material_summaries.items():
        update = {
            "material_id": material_id,
            "material_name": summary.material_name,
            "current_stock": summary.current_stock,
            "stock_status": summary.stock_status.value,
            "days_of_supply": round(summary.days_of_supply, 1),
            "consumption_rate_daily": round(summary.consumption_rate_per_day, 2),
        }
        
        # Add forecast info if available
        if summary.forecast:
            update["shortage_predicted"] = "Yes" if summary.forecast.predicted_shortage else "No"
            if summary.forecast.shortage_date:
                update["shortage_date"] = summary.forecast.shortage_date
            if summary.forecast.days_until_shortage is not None:
                update["days_until_shortage"] = summary.forecast.days_until_shortage
            update["reorder_needed"] = "Yes" if summary.forecast.reorder_needed else "No"
            update["reorder_urgency"] = summary.forecast.reorder_urgency.value
            update["reorder_quantity"] = round(summary.forecast.reorder_quantity, 1)
            update["recommended_action"] = summary.forecast.recommended_action
        
        # Add risks
        if summary.risks:
            update["risks_count"] = len(summary.risks)
            update["highest_severity"] = max([r.severity for r in summary.risks], default="low")
        
        updates_list.append(update)
    
    # Project-level update
    project_update = {
        "material_risk_score": round(intelligence.material_risk_score, 2),
        "critical_materials": intelligence.critical_material_count,
        "reorders_needed": len(intelligence.reorder_recommendations),
        "schedule_impact_risk": round(intelligence.schedule_impact_risk, 2),
        "project_summary": intelligence.project_summary
    }
    
    return {
        "material_updates": updates_list,
        "project_update": project_update
    }


def score_to_tier(risk_score: float) -> str:
    """
    Convert material risk score (0.0-1.0) to human-readable tier
    Used for status indicators and alerts
    """
    if risk_score >= 0.7:
        return "critical"
    elif risk_score >= 0.5:
        return "high"
    elif risk_score >= 0.3:
        return "medium"
    elif risk_score > 0.0:
        return "low"
    else:
        return "minimal"


def create_material_risk_score_detail(intelligence: MaterialIntelligence) -> Dict[str, Any]:
    """
    Create detailed breakdown of material risk score for transparency and debugging
    """
    shortage_risks = len([i for i in intelligence.material_risk_insights 
                          if i.insight_type == "shortage_risk"])
    cost_risks = len([i for i in intelligence.material_risk_insights 
                      if i.insight_type == "cost_escalation"])
    
    shortages_per_material = shortage_risks / len(intelligence.material_summaries) if intelligence.material_summaries else 0.0
    
    return {
        "material_risk_score": intelligence.material_risk_score,
        "risk_tier": score_to_tier(intelligence.material_risk_score),
        "total_materials": len(intelligence.material_summaries),
        "critical_materials": intelligence.critical_material_count,
        "shortage_risks": shortage_risks,
        "cost_risks": cost_risks,
        "average_shortage_risk_per_material": round(shortages_per_material, 3),
        "schedule_impact_risk": intelligence.schedule_impact_risk,
        "reorder_recommendations_pending": len(intelligence.reorder_recommendations),
        "generated_at": intelligence.generated_at
    }
