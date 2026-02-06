"""
Integration test for Core Risk Engine (Feature 1)
Validates that all features (3-6) feed their risks correctly into the core engine
and that holistic project risk is calculated properly
"""
import pytest
import sys
sys.path.insert(0, 'backend/app')

from backend.app.ml import core_risk_engine


def test_core_engine_reset():
    """Test that engine state can be reset"""
    core_risk_engine.reset()
    assert core_risk_engine.risk_registry == {}
    assert core_risk_engine.last_update is None


def test_register_workforce_risk():
    """Test Feature 3 (Workforce) risk registration"""
    core_risk_engine.reset()
    
    workforce_payload = {
        "project_id": "P001",
        "source": "phase18_workforce_reliability",
        "workforce_risk_score": 0.35,
        "avg_team_reliability": 0.92,
        "total_high_risk_workers": 2,
        "estimated_schedule_slip_days": 1.2,
        "estimated_cost_impact": 5000.0
    }
    
    result = core_risk_engine.register_workforce_risk(workforce_payload)
    
    assert result["status"] == "registered"
    assert result["feature"] == "workforce"
    assert "P001" in core_risk_engine.risk_registry
    assert "workforce" in core_risk_engine.risk_registry["P001"]
    assert core_risk_engine.risk_registry["P001"]["workforce"]["risk_score"] == 0.35


def test_register_subcontractor_risk():
    """Test Feature 4 (Subcontractor) risk registration"""
    core_risk_engine.reset()
    
    subcontractor_payload = {
        "project_id": "P001",
        "source": "phase19_subcontractor_performance",
        "subcontractor_risk_score": 0.42,
        "avg_subcontractor_reliability": 0.88,
        "total_high_risk_subcontractors": 1,
        "estimated_schedule_slip_days": 2.5,
        "estimated_cost_impact": 8000.0
    }
    
    result = core_risk_engine.register_subcontractor_risk(subcontractor_payload)
    
    assert result["status"] == "registered"
    assert result["feature"] == "subcontractor"
    assert core_risk_engine.risk_registry["P001"]["subcontractor"]["risk_score"] == 0.42


def test_register_equipment_risk():
    """Test Feature 5 (Equipment) risk registration"""
    core_risk_engine.reset()
    
    equipment_payload = {
        "project_id": "P001",
        "source": "phase20_equipment_maintenance",
        "equipment_risk_score": 0.28,
        "avg_failure_probability": 0.15,
        "high_risk_count": 1,
        "estimated_downtime_days": 0.5,
        "estimated_cost_impact": 3000.0
    }
    
    result = core_risk_engine.register_equipment_risk(equipment_payload)
    
    assert result["status"] == "registered"
    assert result["feature"] == "equipment"
    assert core_risk_engine.risk_registry["P001"]["equipment"]["risk_score"] == 0.28


def test_register_material_risk():
    """Test Feature 6 (Materials) risk registration"""
    core_risk_engine.reset()
    
    material_payload = {
        "project_id": "P001",
        "source": "phase21_material_ordering",
        "material_risk_score": 0.32,
        "critical_material_count": 2,
        "schedule_impact_risk": 0.25,
        "reorder_count": 5
    }
    
    result = core_risk_engine.register_material_risk(material_payload)
    
    assert result["status"] == "registered"
    assert result["feature"] == "material"
    assert core_risk_engine.risk_registry["P001"]["material"]["risk_score"] == 0.32


def test_register_schedule_risk():
    """Test Feature 2 (Schedule) risk registration"""
    core_risk_engine.reset()
    
    schedule_payload = {
        "project_id": "P001",
        "source": "phase16_schedule_dependencies",
        "integration_risk_score": 0.38,
        "schedule_resilience": 0.65,
        "critical_path_length": 12,
        "avg_task_risk": 0.25
    }
    
    result = core_risk_engine.register_schedule_risk(schedule_payload)
    
    assert result["status"] == "registered"
    assert result["feature"] == "schedule"
    assert core_risk_engine.risk_registry["P001"]["schedule"]["integration_risk"] == 0.38


def test_calculate_project_risk_single_feature():
    """Test risk calculation with single feature"""
    core_risk_engine.reset()
    
    core_risk_engine.register_workforce_risk({
        "project_id": "P001",
        "workforce_risk_score": 0.40,
    })
    
    agg = core_risk_engine.calculate_project_risk("P001", base_ai_risk=0.5)
    
    assert agg["project_id"] == "P001"
    assert "overall_risk_score" in agg
    assert "risk_level" in agg
    assert "breakdown" in agg
    assert agg["breakdown"]["workforce_risk"] == 0.40


def test_calculate_project_risk_all_features():
    """Test risk calculation with all features registered"""
    core_risk_engine.reset()
    
    # Register all features
    core_risk_engine.register_workforce_risk({
        "project_id": "P001",
        "workforce_risk_score": 0.35,
    })
    core_risk_engine.register_subcontractor_risk({
        "project_id": "P001",
        "subcontractor_risk_score": 0.42,
    })
    core_risk_engine.register_equipment_risk({
        "project_id": "P001",
        "equipment_risk_score": 0.28,
    })
    core_risk_engine.register_material_risk({
        "project_id": "P001",
        "material_risk_score": 0.32,
    })
    core_risk_engine.register_schedule_risk({
        "project_id": "P001",
        "integration_risk_score": 0.38,
    })
    
    agg = core_risk_engine.calculate_project_risk("P001", base_ai_risk=0.45)
    
    assert agg["project_id"] == "P001"
    assert 0.0 <= agg["overall_risk_score"] <= 1.0
    assert agg["components_registered"] == 5
    assert agg["breakdown"]["base_ai_risk"] == 0.45
    assert agg["breakdown"]["workforce_risk"] == 0.35
    assert agg["breakdown"]["subcontractor_risk"] == 0.42
    assert agg["breakdown"]["equipment_risk"] == 0.28
    assert agg["breakdown"]["material_risk"] == 0.32
    assert agg["breakdown"]["schedule_risk"] == 0.38


def test_calculate_project_risk_weighting():
    """Test that features are weighted correctly in aggregation"""
    core_risk_engine.reset()
    
    # Register feature with moderate risk
    core_risk_engine.register_workforce_risk({
        "project_id": "P002",
        "workforce_risk_score": 0.5,
    })
    
    agg = core_risk_engine.calculate_project_risk("P002", base_ai_risk=0.5)
    
    # Overall should be between 0.5 and weighted average
    # With workforce (0.15 weight) at 0.5 and base_ai (0.30 weight) at 0.5,
    # and other features absent but their default contributions minimal...
    assert 0.4 <= agg["overall_risk_score"] <= 0.6


def test_risk_level_classification():
    """Test risk level tier assignment"""
    assert core_risk_engine._score_to_tier(0.0) == "minimal"
    assert core_risk_engine._score_to_tier(0.15) == "low"
    assert core_risk_engine._score_to_tier(0.4) == "medium"
    assert core_risk_engine._score_to_tier(0.6) == "high"
    assert core_risk_engine._score_to_tier(0.8) == "critical"
    assert core_risk_engine._score_to_tier(1.0) == "critical"


def test_get_project_risks():
    """Test retrieval of all risks for a project"""
    core_risk_engine.reset()
    
    core_risk_engine.register_workforce_risk({
        "project_id": "P003",
        "workforce_risk_score": 0.35,
    })
    core_risk_engine.register_material_risk({
        "project_id": "P003",
        "material_risk_score": 0.32,
    })
    
    risks = core_risk_engine.get_project_risks("P003")
    
    assert risks["project_id"] == "P003"
    assert "workforce" in risks["features_registered"]
    assert "material" in risks["features_registered"]
    assert "aggregated_risk" in risks
    assert risks["aggregated_risk"]["components_registered"] == 2


def test_update_project_risk_delegation():
    """Test that update_project_risk delegates to correct handlers"""
    core_risk_engine.reset()
    
    # Test workforce delegation
    result = core_risk_engine.update_project_risk({
        "project_id": "P004",
        "source": "phase18_workforce_reliability",
        "workforce_risk_score": 0.3,
    })
    assert result["feature"] == "workforce"
    
    # Test material delegation
    result = core_risk_engine.update_project_risk({
        "project_id": "P004",
        "source": "phase21_material_ordering",
        "material_risk_score": 0.4,
    })
    assert result["feature"] == "material"
    
    # Test equipment delegation
    result = core_risk_engine.update_project_risk({
        "project_id": "P004",
        "source": "phase20_equipment_maintenance",
        "equipment_risk_score": 0.25,
    })
    assert result["feature"] == "equipment"


def test_no_features_registered():
    """Test behavior when no features have registered"""
    core_risk_engine.reset()
    
    agg = core_risk_engine.calculate_project_risk("P_EMPTY", base_ai_risk=0.6)
    
    assert agg["project_id"] == "P_EMPTY"
    assert agg["overall_risk_score"] == 0.6  # Should return base_ai_risk
    assert agg["note"] == "No feature risks registered yet"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
