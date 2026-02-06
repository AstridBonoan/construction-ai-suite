"""
Phase 18: Workforce Reliability Integration with Core Risk Engine (Feature 1)

Feeds workforce intelligence into the core AI risk engine for holistic project risk scoring.
"""

import logging
from typing import Dict, Any, Optional
from phase18_workforce_types import WorkforceIntelligence

logger = logging.getLogger(__name__)


def feed_workforce_to_core_risk_engine(intelligence: WorkforceIntelligence) -> Dict[str, Any]:
    """
    Feed workforce intelligence into the core AI risk engine (Feature 1).
    
    This hook allows workforce reliability scores to propagate into the overall
    project risk scoring. The core engine will integrate workforce risk with
    schedule risk (Feature 2) and cost forecasting for holistic project health.
    
    If no core risk engine is available, output is logged for debugging.
    
    Args:
        intelligence: WorkforceIntelligence object with project-level summary
        
    Returns:
        Dict with status and result from core engine or error info
    """
    
    # Prepare structured output for the core risk engine
    structured_output = _prepare_workforce_payload(intelligence)
    
    logger.info(f"Feeding workforce intelligence for {intelligence.project_id} to core risk engine")
    
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
        
        if core_mod and hasattr(core_mod, "register_workforce_risk"):
            try:
                # Call the specific workforce handler
                result = core_mod.register_workforce_risk(structured_output)
                logger.info("Workforce intelligence integrated with core risk engine successfully")
                return result
            except Exception as e:
                logger.exception(f"Core risk engine call failed: {e}")
                logger.debug(f"Payload was: {structured_output}")
                return {"status": "error", "error": str(e)}
        else:
            logger.debug("No core risk engine found; logging output only.")
            logger.debug(f"Workforce intelligence: {structured_output}")
            return {"status": "logged", "source": "phase18_workforce"}
    
    except Exception as e:
        logger.exception(f"Unexpected error while attempting to feed core risk engine: {e}")
        return {"status": "error", "error": str(e)}


def _prepare_workforce_payload(intelligence: WorkforceIntelligence) -> Dict[str, Any]:
    """Prepare structured payload for core risk engine integration"""
    
    summary = intelligence.project_summary
    
    return {
        "source": "workforce_intelligence_phase18",
        "project_id": intelligence.project_id,
        "project_name": intelligence.project_name,
        "generated_at": intelligence.generated_at,
        
        # Workforce metrics
        "workforce_risk_score": intelligence.workforce_risk_score,
        "avg_team_reliability": summary.avg_team_reliability if summary else 0.0,
        "total_workers": summary.total_workers if summary else 0,
        "high_risk_worker_count": len(summary.high_risk_workers) if summary else 0,
        
        # Schedule and cost impacts
        "estimated_schedule_slip_days": summary.total_schedule_risk_days if summary else 0,
        "estimated_cost_impact": summary.total_cost_impact if summary else 0,
        
        # Key insights and recommendations
        "key_insights": summary.key_insights if summary else [],
        "recommendations": summary.recommendations if summary else [],
        "explanation": summary.explanation if summary else "",
        
        # Per-worker risk indicators (sample of high-risk workers)
        "high_risk_workers": [
            {
                "worker_id": wid,
                "name": intelligence.worker_summaries[wid].worker_name,
                "reliability_score": intelligence.worker_summaries[wid].reliability_score,
                "risk_level": intelligence.worker_summaries[wid].risk_level,
                "absence_rate": intelligence.worker_summaries[wid].absence_rate,
            }
            for wid in (summary.high_risk_workers if summary else [])[:5]
        ],
        
        # Integration metadata
        "integration_source": "Feature 3 - Workforce Reliability",
        "confidence": 0.8,  # Confidence in this assessment
        "should_cascade_to_project_risk": True,
    }


def create_workforce_risk_update(intelligence: WorkforceIntelligence) -> Dict[str, Any]:
    """
    Create a risk update object suitable for monday.com or dashboard integration.
    
    Returns a dictionary that can be:
    - Fed to the core risk engine via feed_workforce_to_core_risk_engine
    - Posted to monday.com API to update task/board status
    - Displayed in dashboards/alerts
    """
    
    summary = intelligence.project_summary
    
    return {
        "project_id": intelligence.project_id,
        "workforce_health_score": 1.0 - intelligence.workforce_risk_score,  # Inverted for "health"
        "reliability_tier": _score_to_tier(intelligence.workforce_risk_score),
        "has_critical_issues": len(summary.high_risk_workers) > 0 if summary else False,
        "recommended_actions": summary.recommendations if summary else [],
        
        # For monday.com column mapping
        "monday_updates": {
            "workforce_reliability": 1.0 - intelligence.workforce_risk_score,  # 0-1
            "workforce_risk_flag": "yes" if intelligence.workforce_risk_score > 0.3 else "no",
            "schedule_impact_estimate": f"{summary.total_schedule_risk_days:.0f} days" if summary else "0 days",
            "cost_impact_estimate": f"${summary.total_cost_impact:,.0f}" if summary else "$0",
        }
    }


def _score_to_tier(risk_score: float) -> str:
    """Convert risk score (0-1) to health tier"""
    if risk_score < 0.2:
        return "critical"
    elif risk_score < 0.4:
        return "poor"
    elif risk_score < 0.6:
        return "fair"
    elif risk_score < 0.8:
        return "good"
    else:
        return "excellent"
