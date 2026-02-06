"""
Unit tests for Phase 21: Automated Material Ordering & Forecasting
"""
import pytest
from datetime import datetime, timedelta
from phase21_material_types import (
    Material, SupplierInfo, StockRecord, DemandRecord, MaterialType,
    UnitType, StockStatus, ForecastUrgency
)
from phase21_material_analyzer import MaterialOrderingAnalyzer


@pytest.fixture
def analyzer():
    return MaterialOrderingAnalyzer()


@pytest.fixture
def sample_material():
    return Material(
        material_id="MAT001",
        name="Concrete",
        material_type=MaterialType.CONCRETE,
        unit_type=UnitType.CUBIC_METERS,
        cost_per_unit=120.0
    )


@pytest.fixture
def sample_supplier():
    return SupplierInfo(
        supplier_id="SUP001",
        name="Concrete Co",
        lead_time_days=7,
        reliability_score=0.95,
        price_per_unit=120.0
    )


def test_material_health_calculation_adequate_stock(analyzer, sample_material, sample_supplier):
    """Test forecast when stock is adequate with minimal consumption"""
    analyzer.add_material(sample_material)
    analyzer.add_supplier(sample_supplier)
    
    stock = StockRecord(
        project_id='P001',
        material_id='MAT001',
        quantity_on_hand=500.0,
        supplier_id='SUP001'
    )
    analyzer.add_stock_record(stock)
    
    # Add small distributed demands over 30 days
    for i in range(30):
        demand = DemandRecord(
            project_id='P001',
            task_id=f'T{i:03d}',
            material_id='MAT001',
            quantity_needed=0.5,
            needed_by_date=(datetime.now() + timedelta(days=i+1)).date().isoformat()
        )
        analyzer.add_demand_record(demand)
    
    forecast = analyzer.calculate_material_forecast('P001', 'MAT001')
    
    assert forecast.material_id == 'MAT001'
    assert forecast.current_stock == 500.0
    assert forecast.predicted_shortage is False
    assert forecast.reorder_needed is False


def test_material_shortage_prediction(analyzer, sample_material, sample_supplier):
    """Test shortage prediction with high consumption rate"""
    analyzer.add_material(sample_material)
    analyzer.add_supplier(sample_supplier)
    
    stock = StockRecord(
        project_id='P002',
        material_id='MAT001',
        quantity_on_hand=50.0,
        supplier_id='SUP001'
    )
    analyzer.add_stock_record(stock)
    
    # Add heavy demand that will deplete stock
    for i in range(10):
        demand = DemandRecord(
            project_id='P002',
            task_id=f'T{i}',
            material_id='MAT001',
            quantity_needed=15.0,
            needed_by_date=(datetime.now() + timedelta(days=i+1)).date().isoformat()
        )
        analyzer.add_demand_record(demand)
    
    forecast = analyzer.calculate_material_forecast('P002', 'MAT001')
    
    assert forecast.current_stock == 50.0
    assert forecast.predicted_shortage is True
    assert forecast.days_until_shortage is not None
    assert forecast.days_until_shortage <= 5  # Will run out soon
    assert forecast.reorder_needed is True
    assert forecast.reorder_quantity > 0.0


def test_reorder_quantity_calculation(analyzer):
    """Test optimal reorder quantity calculation"""
    material = Material(
        material_id='MAT002',
        name='Steel Beams',
        material_type=MaterialType.STEEL,
        unit_type=UnitType.METRIC_TONS,
        cost_per_unit=500.0
    )
    supplier = SupplierInfo(
        supplier_id='SUP002',
        name='Steel Supply',
        lead_time_days=14,
        reliability_score=0.90
    )
    
    analyzer.add_material(material)
    analyzer.add_supplier(supplier)
    
    stock = StockRecord(
        project_id='P003',
        material_id='MAT002',
        quantity_on_hand=20.0,
        supplier_id='SUP002'
    )
    analyzer.add_stock_record(stock)
    
    # Add sustained demand
    for i in range(20):
        demand = DemandRecord(
            project_id='P003',
            task_id=f'TASK{i}',
            material_id='MAT002',
            quantity_needed=5.0,
            needed_by_date=(datetime.now() + timedelta(days=i+1)).date().isoformat()
        )
        analyzer.add_demand_record(demand)
    
    forecast = analyzer.calculate_material_forecast('P003', 'MAT002')
    
    assert forecast.reorder_quantity > 0.0
    # Reorder should cover lead time + safety stock
    assert forecast.reorder_quantity >= (5.0 * 14.0)  # At minimum: 5/day × 14 days lead time


def test_project_material_intelligence(analyzer, sample_material, sample_supplier):
    """Test aggregation of material intelligence at project level"""
    analyzer.add_material(sample_material)
    analyzer.add_supplier(sample_supplier)
    
    stock = StockRecord(
        project_id='P004',
        material_id='MAT001',
        quantity_on_hand=75.0,
        supplier_id='SUP001'
    )
    analyzer.add_stock_record(stock)
    
    # Add multiple demand records from different tasks
    for i in range(3):
        demand = DemandRecord(
            project_id='P004',
            task_id=f'TASK{i}',
            material_id='MAT001',
            quantity_needed=20.0,
            needed_by_date=(datetime.now() + timedelta(days=i+5)).date().isoformat()
        )
        analyzer.add_demand_record(demand)
    
    intelligence = analyzer.create_project_material_intelligence(
        'P004',
        'Downtown Build',
        ['MAT001']
    )
    
    assert intelligence.project_id == 'P004'
    assert intelligence.project_name == 'Downtown Build'
    assert 'MAT001' in intelligence.material_summaries
    assert intelligence.integration_ready is True
    assert isinstance(intelligence.material_risk_score, float)
    assert 0.0 <= intelligence.material_risk_score <= 1.0
    assert 'material_risk_score' in intelligence.monday_updates


def test_multiple_materials_and_suppliers(analyzer):
    """Test forecasting with multiple materials and suppliers"""
    # Material 1: Concrete
    mat1 = Material('MAT1', 'Concrete', MaterialType.CONCRETE, UnitType.CUBIC_METERS, cost_per_unit=120.0)
    sup1 = SupplierInfo('SUP1', 'Concrete Co', 7, 0.95)
    
    # Material 2: Steel
    mat2 = Material('MAT2', 'Steel', MaterialType.STEEL, UnitType.METRIC_TONS, cost_per_unit=500.0)
    sup2 = SupplierInfo('SUP2', 'Steel Inc', 14, 0.85)
    
    analyzer.add_material(mat1)
    analyzer.add_material(mat2)
    analyzer.add_supplier(sup1)
    analyzer.add_supplier(sup2)
    
    # Stock records
    analyzer.add_stock_record(StockRecord('P5', 'MAT1', 100.0, supplier_id='SUP1'))
    analyzer.add_stock_record(StockRecord('P5', 'MAT2', 50.0, supplier_id='SUP2'))
    
    # Demands
    for i in range(5):
        analyzer.add_demand_record(DemandRecord(
            'P5', f'T{i}', 'MAT1', 10.0,
            (datetime.now() + timedelta(days=i+1)).date().isoformat()
        ))
        analyzer.add_demand_record(DemandRecord(
            'P5', f'T{i}', 'MAT2', 5.0,
            (datetime.now() + timedelta(days=i+1)).date().isoformat()
        ))
    
    intelligence = analyzer.create_project_material_intelligence('P5', 'Multi-Mat Project', ['MAT1', 'MAT2'])
    
    assert len(intelligence.material_summaries) == 2
    assert intelligence.material_risk_score >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
