"""
CI dry-run integration test for Phase 21: Material Ordering & Forecasting
Validates Phase 21 output flows correctly through monday.com mapping integration
"""
import pytest
from datetime import datetime, timedelta
from phase21_material_types import (
    Material, SupplierInfo, StockRecord, DemandRecord, MaterialType, UnitType
)
from phase21_material_analyzer import MaterialOrderingAnalyzer
from phase21_material_integration import (
    feed_material_to_core_risk_engine, create_material_risk_update,
    create_material_risk_score_detail, score_to_tier
)


@pytest.fixture
def sample_project_data():
    """Create a realistic multi-material project scenario"""
    return {
        "project_id": "P_CI_001",
        "project_name": "CI Test Building Project",
        "materials": [
            {
                "material_id": "MAT_CONCRETE",
                "name": "Concrete C40",
                "material_type": "CONCRETE",
                "unit_type": "CUBIC_METERS",
                "cost_per_unit": 120.0
            },
            {
                "material_id": "MAT_STEEL",
                "name": "Structural Steel",
                "material_type": "STEEL",
                "unit_type": "METRIC_TONS",
                "cost_per_unit": 500.0
            },
            {
                "material_id": "MAT_LUMBER",
                "name": "Formwork Lumber",
                "material_type": "LUMBER",
                "unit_type": "LINEAR_METERS",
                "cost_per_unit": 8.0
            }
        ],
        "suppliers": [
            {
                "supplier_id": "SUP_CONCRETE",
                "name": "FastConcrete Co",
                "lead_time_days": 7,
                "reliability_score": 0.95,
                "price_per_unit": 120.0,
                "primary_materials": ["MAT_CONCRETE"]
            },
            {
                "supplier_id": "SUP_STEEL",
                "name": "SteelWorks Inc",
                "lead_time_days": 14,
                "reliability_score": 0.85,
                "price_per_unit": 500.0,
                "primary_materials": ["MAT_STEEL"]
            },
            {
                "supplier_id": "SUP_LUMBER",
                "name": "Forest Supply Ltd",
                "lead_time_days": 5,
                "reliability_score": 0.92,
                "price_per_unit": 8.0,
                "primary_materials": ["MAT_LUMBER"]
            }
        ],
        "stock_records": [
            {
                "project_id": "P_CI_001",
                "material_id": "MAT_CONCRETE",
                "quantity_on_hand": 300.0,
                "quantity_on_order": 100.0,
                "supplier_id": "SUP_CONCRETE",
                "last_updated": datetime.now().isoformat()
            },
            {
                "project_id": "P_CI_001",
                "material_id": "MAT_STEEL",
                "quantity_on_hand": 50.0,
                "quantity_on_order": 0.0,
                "supplier_id": "SUP_STEEL",
                "last_updated": datetime.now().isoformat()
            },
            {
                "project_id": "P_CI_001",
                "material_id": "MAT_LUMBER",
                "quantity_on_hand": 5000.0,
                "quantity_on_order": 2000.0,
                "supplier_id": "SUP_LUMBER",
                "last_updated": datetime.now().isoformat()
            }
        ],
        "demand_records": [
            # Concrete demands
            *[
                {
                    "project_id": "P_CI_001",
                    "task_id": f"FOUNDATION_{i}",
                    "material_id": "MAT_CONCRETE",
                    "quantity_needed": 50.0,
                    "needed_by_date": (datetime.now() + timedelta(days=i+5)).date().isoformat(),
                    "task_duration_days": 3
                }
                for i in range(5)
            ],
            # Steel demands (will stress test the analyzer)
            *[
                {
                    "project_id": "P_CI_001",
                    "task_id": f"FRAMING_{i}",
                    "material_id": "MAT_STEEL",
                    "quantity_needed": 10.0,
                    "needed_by_date": (datetime.now() + timedelta(days=i+10)).date().isoformat(),
                    "task_duration_days": 5
                }
                for i in range(8)
            ],
            # Lumber demands
            *[
                {
                    "project_id": "P_CI_001",
                    "task_id": f"FORMWORK_{i}",
                    "material_id": "MAT_LUMBER",
                    "quantity_needed": 200.0,
                    "needed_by_date": (datetime.now() + timedelta(days=i+3)).date().isoformat(),
                    "task_duration_days": 7
                }
                for i in range(10)
            ]
        ]
    }


def test_phase21_material_intelligence_generation(sample_project_data):
    """Test that Phase 21 analyzer generates proper intelligence structure"""
    analyzer = MaterialOrderingAnalyzer()
    
    # Register materials
    for mat_data in sample_project_data["materials"]:
        material = Material(
            material_id=mat_data["material_id"],
            name=mat_data["name"],
            material_type=MaterialType[mat_data["material_type"].upper()],
            unit_type=UnitType[mat_data["unit_type"].upper()],
            cost_per_unit=mat_data.get("cost_per_unit", 0.0)
        )
        analyzer.add_material(material)
    
    # Register suppliers
    for sup_data in sample_project_data["suppliers"]:
        supplier = SupplierInfo(
            supplier_id=sup_data["supplier_id"],
            name=sup_data["name"],
            lead_time_days=sup_data["lead_time_days"],
            reliability_score=sup_data["reliability_score"],
            price_per_unit=sup_data.get("price_per_unit", 0.0)
        )
        analyzer.add_supplier(supplier)
    
    # Register stock
    for stock_data in sample_project_data["stock_records"]:
        stock = StockRecord(
            project_id=stock_data["project_id"],
            material_id=stock_data["material_id"],
            quantity_on_hand=stock_data["quantity_on_hand"],
            quantity_on_order=stock_data.get("quantity_on_order", 0.0),
            supplier_id=stock_data["supplier_id"],
            last_updated=stock_data.get("last_updated", "")
        )
        analyzer.add_stock_record(stock)
    
    # Register demands
    for demand_data in sample_project_data["demand_records"]:
        demand = DemandRecord(
            project_id=demand_data["project_id"],
            task_id=demand_data["task_id"],
            material_id=demand_data["material_id"],
            quantity_needed=demand_data["quantity_needed"],
            needed_by_date=demand_data["needed_by_date"],
            unit_type=UnitType[demand_data.get("unit_type", "PIECES").upper()],
            task_duration_days=demand_data.get("task_duration_days", 1)
        )
        analyzer.add_demand_record(demand)
    
    # Generate intelligence
    material_ids = [m["material_id"] for m in sample_project_data["materials"]]
    intelligence = analyzer.create_project_material_intelligence(
        sample_project_data["project_id"],
        sample_project_data["project_name"],
        material_ids
    )
    
    # Validate intelligence structure
    assert intelligence.project_id == "P_CI_001"
    assert intelligence.project_name == "CI Test Building Project"
    assert len(intelligence.material_summaries) == 3
    assert intelligence.integration_ready is True
    assert isinstance(intelligence.material_risk_score, float)
    assert 0.0 <= intelligence.material_risk_score <= 1.0
    assert isinstance(intelligence.schedule_impact_risk, float)
    assert 0.0 <= intelligence.schedule_impact_risk <= 1.0


def test_phase21_core_engine_integration(sample_project_data):
    """Test that Phase 21 intelligence feeds into core risk engine with proper fallback"""
    analyzer = MaterialOrderingAnalyzer()
    
    # Load project data (abbreviated)
    for mat_data in sample_project_data["materials"]:
        analyzer.add_material(Material(
            material_id=mat_data["material_id"],
            name=mat_data["name"],
            material_type=MaterialType[mat_data["material_type"].upper()],
            unit_type=UnitType[mat_data["unit_type"].upper()]
        ))
    
    for sup_data in sample_project_data["suppliers"]:
        analyzer.add_supplier(SupplierInfo(
            supplier_id=sup_data["supplier_id"],
            name=sup_data["name"],
            lead_time_days=sup_data["lead_time_days"],
            reliability_score=sup_data["reliability_score"]
        ))
    
    for stock_data in sample_project_data["stock_records"]:
        analyzer.add_stock_record(StockRecord(
            project_id=stock_data["project_id"],
            material_id=stock_data["material_id"],
            quantity_on_hand=stock_data["quantity_on_hand"],
            supplier_id=stock_data["supplier_id"]
        ))
    
    for demand_data in sample_project_data["demand_records"]:
        analyzer.add_demand_record(DemandRecord(
            project_id=demand_data["project_id"],
            task_id=demand_data["task_id"],
            material_id=demand_data["material_id"],
            quantity_needed=demand_data["quantity_needed"],
            needed_by_date=demand_data["needed_by_date"]
        ))
    
    intelligence = analyzer.create_project_material_intelligence(
        "P_CI_001",
        "CI Test Building Project",
        [m["material_id"] for m in sample_project_data["materials"]]
    )
    
    # Feed to core risk engine
    result = feed_material_to_core_risk_engine(intelligence)
    
    # Validate result structure
    assert result is not None
    assert isinstance(result, dict)
    # Should either have status="logged" (when core engine unavailable) or success (when available)
    assert "status" in result or "source" in result
    assert result.get("source", "").startswith("phase_21") or result.get("status") == "logged"


def test_phase21_monday_mapping_structure(sample_project_data):
    """Test that Phase 21 output maps correctly to monday.com column schema"""
    analyzer = MaterialOrderingAnalyzer()
    
    # Quick setup
    for mat_data in sample_project_data["materials"]:
        analyzer.add_material(Material(
            material_id=mat_data["material_id"],
            name=mat_data["name"],
            material_type=MaterialType[mat_data["material_type"].upper()],
            unit_type=UnitType[mat_data["unit_type"].upper()]
        ))
    
    for sup_data in sample_project_data["suppliers"]:
        analyzer.add_supplier(SupplierInfo(
            supplier_id=sup_data["supplier_id"],
            name=sup_data["name"],
            lead_time_days=sup_data["lead_time_days"],
            reliability_score=sup_data["reliability_score"]
        ))
    
    for stock_data in sample_project_data["stock_records"]:
        analyzer.add_stock_record(StockRecord(
            project_id=stock_data["project_id"],
            material_id=stock_data["material_id"],
            quantity_on_hand=stock_data["quantity_on_hand"],
            supplier_id=stock_data["supplier_id"]
        ))
    
    for demand_data in sample_project_data["demand_records"]:
        analyzer.add_demand_record(DemandRecord(
            project_id=demand_data["project_id"],
            task_id=demand_data["task_id"],
            material_id=demand_data["material_id"],
            quantity_needed=demand_data["quantity_needed"],
            needed_by_date=demand_data["needed_by_date"]
        ))
    
    intelligence = analyzer.create_project_material_intelligence(
        "P_CI_001",
        "CI Test Building Project",
        [m["material_id"] for m in sample_project_data["materials"]]
    )
    
    # Generate monday mapping
    mapping = create_material_risk_update(intelligence)
    
    # Validate mapping structure
    assert "material_updates" in mapping
    assert "project_update" in mapping
    assert isinstance(mapping["material_updates"], list)
    assert isinstance(mapping["project_update"], dict)
    
    # Validate material-level mappings
    for mat_update in mapping["material_updates"]:
        assert "material_id" in mat_update
        assert "material_name" in mat_update
        assert "current_stock" in mat_update
        assert "stock_status" in mat_update
        assert "days_of_supply" in mat_update
        assert mat_update["stock_status"] in ["adequate", "low", "critical", "out_of_stock"]
    
    # Validate project-level mappings
    project_update = mapping["project_update"]
    assert "material_risk_score" in project_update
    assert "critical_materials" in project_update
    assert "reorders_needed" in project_update
    assert "schedule_impact_risk" in project_update
    assert isinstance(float(project_update["material_risk_score"]), float)
    assert isinstance(int(project_update["critical_materials"]), int)


def test_phase21_risk_score_detail(sample_project_data):
    """Test that risk score detail provides proper breakdown for transparency"""
    analyzer = MaterialOrderingAnalyzer()
    
    for mat_data in sample_project_data["materials"]:
        analyzer.add_material(Material(
            material_id=mat_data["material_id"],
            name=mat_data["name"],
            material_type=MaterialType[mat_data["material_type"].upper()],
            unit_type=UnitType[mat_data["unit_type"].upper()]
        ))
    
    for sup_data in sample_project_data["suppliers"]:
        analyzer.add_supplier(SupplierInfo(
            supplier_id=sup_data["supplier_id"],
            name=sup_data["name"],
            lead_time_days=sup_data["lead_time_days"],
            reliability_score=sup_data["reliability_score"]
        ))
    
    for stock_data in sample_project_data["stock_records"]:
        analyzer.add_stock_record(StockRecord(
            project_id=stock_data["project_id"],
            material_id=stock_data["material_id"],
            quantity_on_hand=stock_data["quantity_on_hand"],
            supplier_id=stock_data["supplier_id"]
        ))
    
    for demand_data in sample_project_data["demand_records"]:
        analyzer.add_demand_record(DemandRecord(
            project_id=demand_data["project_id"],
            task_id=demand_data["task_id"],
            material_id=demand_data["material_id"],
            quantity_needed=demand_data["quantity_needed"],
            needed_by_date=demand_data["needed_by_date"]
        ))
    
    intelligence = analyzer.create_project_material_intelligence(
        "P_CI_001",
        "CI Test Building Project",
        [m["material_id"] for m in sample_project_data["materials"]]
    )
    
    # Get detailed score breakdown
    detail = create_material_risk_score_detail(intelligence)
    
    # Validate detail structure
    assert "material_risk_score" in detail
    assert "risk_tier" in detail
    assert "total_materials" in detail
    assert "critical_materials" in detail
    assert "shortage_risks" in detail
    assert "schedule_impact_risk" in detail
    
    # Validate risk tier is valid
    assert detail["risk_tier"] in ["critical", "high", "medium", "low", "minimal"]
    
    # Validate score consistency
    assert detail["material_risk_score"] == intelligence.material_risk_score


def test_score_to_tier_conversion():
    """Test that score-to-tier conversion works correctly"""
    assert score_to_tier(0.0) == "minimal"
    assert score_to_tier(0.15) == "low"
    assert score_to_tier(0.4) == "medium"
    assert score_to_tier(0.6) == "high"
    assert score_to_tier(0.8) == "critical"
    assert score_to_tier(1.0) == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
