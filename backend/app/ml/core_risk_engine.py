"""
Core Risk Engine (Feature 1) - Aggregates risk signals from all features
Integrates workforce, subcontractor, equipment, material, and schedule risks
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state for feature risk registrations
last_update = None
risk_registry: Dict[str, Dict[str, Any]] = {}  # project_id -> {feature -> risk_data}


def reset():
    """Reset engine state (for testing)"""
    global last_update, risk_registry
    last_update = None
    risk_registry = {}


def update_project_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy method for backward compatibility.
    Routes to appropriate handler based on source.
    """
    global last_update
    last_update = payload
    
    source = payload.get("source", "unknown")
    project_id = payload.get("project_id", "unknown")
    
    # Route to appropriate handler
    if "workforce" in source.lower():
        return register_workforce_risk(payload)
    elif "subcontractor" in source.lower():
        return register_subcontractor_risk(payload)
    elif "equipment" in source.lower() or "phase20" in source.lower():
        return register_equipment_risk(payload)
    elif "material" in source.lower() or "phase21" in source.lower():
        return register_material_risk(payload)
    elif "schedule" in source.lower() or "phase16" in source.lower():
        return register_schedule_risk(payload)
    else:
        return register_generic_risk(payload)


def register_workforce_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register workforce reliability risk (Feature 3 / Phase 18)"""
    project_id = payload.get("project_id", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id]["workforce"] = {
        "source": "phase18_workforce_reliability",
        "risk_score": payload.get("workforce_risk_score", 0.5),
        "avg_reliability": payload.get("avg_team_reliability", 0.8),
        "high_risk_count": payload.get("total_high_risk_workers", 0),
        "schedule_slip_days": payload.get("estimated_schedule_slip_days", 0.0),
        "cost_impact": payload.get("estimated_cost_impact", 0.0),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Workforce risk registered for {project_id}: "
                f"score={payload.get('workforce_risk_score', 0.5)}")
    return {"status": "registered", "feature": "workforce"}


def register_subcontractor_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register subcontractor performance risk (Feature 4 / Phase 19)"""
    project_id = payload.get("project_id", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id]["subcontractor"] = {
        "source": "phase19_subcontractor_performance",
        "risk_score": payload.get("subcontractor_risk_score", 0.5),
        "avg_reliability": payload.get("avg_subcontractor_reliability", 0.8),
        "high_risk_count": payload.get("total_high_risk_subcontractors", 0),
        "schedule_slip_days": payload.get("estimated_schedule_slip_days", 0.0),
        "cost_impact": payload.get("estimated_cost_impact", 0.0),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Subcontractor risk registered for {project_id}: "
                f"score={payload.get('subcontractor_risk_score', 0.5)}")
    return {"status": "registered", "feature": "subcontractor"}


def register_equipment_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register equipment maintenance risk (Feature 5 / Phase 20)"""
    project_id = payload.get("project_id", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id]["equipment"] = {
        "source": "phase20_equipment_maintenance",
        "risk_score": payload.get("equipment_risk_score", 0.5),
        "failure_probability": payload.get("avg_failure_probability", 0.2),
        "critical_count": payload.get("high_risk_count", 0),
        "downtime_days": payload.get("estimated_downtime_days", 0.0),
        "cost_impact": payload.get("estimated_cost_impact", 0.0),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Equipment risk registered for {project_id}: "
                f"score={payload.get('equipment_risk_score', 0.5)}")
    return {"status": "registered", "feature": "equipment"}


def register_material_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register material ordering & forecasting risk (Feature 6 / Phase 21)"""
    project_id = payload.get("project_id", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id]["material"] = {
        "source": "phase21_material_ordering",
        "risk_score": payload.get("material_risk_score", 0.5),
        "critical_count": payload.get("critical_material_count", 0),
        "schedule_impact": payload.get("schedule_impact_risk", 0.0),
        "reorder_count": payload.get("reorder_count", 0),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Material risk registered for {project_id}: "
                f"score={payload.get('material_risk_score', 0.5)}")
    return {"status": "registered", "feature": "material"}


def register_schedule_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register schedule delay propagation risk (Feature 2 / Phase 16)"""
    project_id = payload.get("project_id", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id]["schedule"] = {
        "source": "phase16_schedule_dependencies",
        "integration_risk": payload.get("integration_risk_score", 0.5),
        "resilience": payload.get("schedule_resilience", 0.5),
        "critical_path_length": payload.get("critical_path_length", 0),
        "avg_task_risk": payload.get("avg_task_risk", 0.3),
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Schedule risk registered for {project_id}: "
                f"integration_risk={payload.get('integration_risk_score', 0.5)}")
    return {"status": "registered", "feature": "schedule"}


def register_generic_risk(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register generic/unknown risk payload"""
    project_id = payload.get("project_id", "unknown")
    source = payload.get("source", "unknown")
    
    if project_id not in risk_registry:
        risk_registry[project_id] = {}
    
    risk_registry[project_id][source] = payload
    logger.info(f"Generic risk registered for {project_id} from {source}")
    return {"status": "registered", "feature": source}


def calculate_project_risk(project_id: str, base_ai_risk: float = 0.5) -> Dict[str, Any]:
    """
    Calculate holistic project risk by aggregating all feature risks.
    
    Args:
        project_id: Project identifier
        base_ai_risk: Base risk score from Feature 1 AI model (0-1)
    
    Returns:
        Aggregated risk assessment with component breakdown
    """
    if project_id not in risk_registry:
        # No features have registered yet, return base risk
        return {
            "project_id": project_id,
            "overall_risk_score": base_ai_risk,
            "risk_level": _score_to_tier(base_ai_risk),
            "breakdown": {},
            "note": "No feature risks registered yet"
        }
    
    features = risk_registry[project_id]
    risk_scores = {}
    weights = {}
    
    # Extract risk scores from each feature
    if "workforce" in features:
        risk_scores["workforce"] = features["workforce"].get("risk_score", 0.0)
        weights["workforce"] = 0.15
    
    if "subcontractor" in features:
        risk_scores["subcontractor"] = features["subcontractor"].get("risk_score", 0.0)
        weights["subcontractor"] = 0.15
    
    if "equipment" in features:
        risk_scores["equipment"] = features["equipment"].get("risk_score", 0.0)
        weights["equipment"] = 0.10
    
    if "material" in features:
        risk_scores["material"] = features["material"].get("risk_score", 0.0)
        weights["material"] = 0.10
    
    if "schedule" in features:
        # Use integration_risk if available, else use placeholder
        schedule_risk = features["schedule"].get("integration_risk", 
                                                  features["schedule"].get("avg_task_risk", 0.0))
        risk_scores["schedule"] = schedule_risk
        weights["schedule"] = 0.20
    
    # Feature 1 base AI risk gets highest weight
    weights["base_ai"] = 0.30
    
    # Calculate weighted average
    total_weight = sum(weights.values()) if weights else 1.0
    weighted_sum = (base_ai_risk * weights.get("base_ai", 0.30))
    
    for feature, score in risk_scores.items():
        weighted_sum += score * weights.get(feature, 0.0)
    
    overall_risk = weighted_sum / total_weight if total_weight > 0 else base_ai_risk
    overall_risk = max(0.0, min(1.0, overall_risk))  # Clamp to [0, 1]
    
    return {
        "project_id": project_id,
        "overall_risk_score": round(overall_risk, 3),
        "risk_level": _score_to_tier(overall_risk),
        "breakdown": {
            "base_ai_risk": round(base_ai_risk, 3),
            "workforce_risk": risk_scores.get("workforce"),
            "subcontractor_risk": risk_scores.get("subcontractor"),
            "equipment_risk": risk_scores.get("equipment"),
            "material_risk": risk_scores.get("material"),
            "schedule_risk": risk_scores.get("schedule")
        },
        "weights": weights,
        "components_registered": len(risk_scores),
        "aggregation_timestamp": datetime.now().isoformat()
    }


def get_project_risks(project_id: str) -> Dict[str, Any]:
    """Get all registered risks for a project"""
    if project_id not in risk_registry:
        return {
            "project_id": project_id,
            "features_registered": [],
            "status": "no_features_registered"
        }
    
    features = risk_registry[project_id]
    return {
        "project_id": project_id,
        "features_registered": list(features.keys()),
        "details": features,
        "aggregated_risk": calculate_project_risk(project_id, base_ai_risk=0.5)
    }


def _score_to_tier(score: float) -> str:
    """Convert score (0-1) to risk tier"""
    if score >= 0.7:
        return "critical"
    elif score >= 0.5:
        return "high"
    elif score >= 0.3:
        return "medium"
    elif score > 0.0:
        return "low"
    else:
        return "minimal"
