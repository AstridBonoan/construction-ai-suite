"""
Unit tests for Phase 20: Predictive Equipment Maintenance
"""
import pytest
from phase20_equipment_types import (
    Equipment, MaintenanceRecord, FailureEvent, EquipmentType,
    EquipmentStatus, EquipmentIntelligence
)
from phase20_equipment_analyzer import EquipmentMaintenanceAnalyzer
from datetime import datetime, timedelta


@pytest.fixture
def analyzer():
    return EquipmentMaintenanceAnalyzer()


def test_equipment_health_summary_basic(analyzer):
    """Test basic equipment health calculation"""
    eq = Equipment(
        equipment_id='EQ001',
        name='Excavator A',
        equipment_type=EquipmentType.EXCAVATOR,
        acquisition_date='2020-01-01'
    )
    analyzer.add_equipment(eq)
    
    # Add some maintenance records
    for i in range(3):
        rec = MaintenanceRecord(
            project_id='P1',
            equipment_id='EQ001',
            maintenance_date=f'2025-0{i+1}-01',
            maintenance_type='preventive',
            duration_hours=8.0,
            cost=1000.0,
            completed=True
        )
        analyzer.add_maintenance_record(rec)
    
    health = analyzer.calculate_equipment_health('EQ001')
    assert health.equipment_id == 'EQ001'
    assert health.total_maintenance_events == 3
    assert 0.0 <= health.failure_probability <= 1.0
    assert health.explanation != ""


def test_equipment_health_with_failures(analyzer):
    """Test equipment health with past failures"""
    eq = Equipment(
        equipment_id='EQ002',
        name='Crane B',
        equipment_type=EquipmentType.CRANE,
        acquisition_date='2019-01-01'
    )
    analyzer.add_equipment(eq)
    
    # Add maintenance
    for i in range(2):
        rec = MaintenanceRecord(
            project_id='P1',
            equipment_id='EQ002',
            maintenance_date=f'2025-0{i+1}-01',
            maintenance_type='corrective',
            duration_hours=16.0,
            cost=3000.0,
            completed=True
        )
        analyzer.add_maintenance_record(rec)
    
    # Add failures
    for i in range(2):
        evt = FailureEvent(
            project_id='P1',
            task_id=f'T{i}',
            equipment_id='EQ002',
            failure_date=f'2024-{(i+1):02d}-01',
            failure_type='engine_failure',
            repair_duration_hours=24.0,
            repair_cost=5000.0,
            downtime_impact_days=2.0
        )
        analyzer.add_failure_event(evt)
    
    health = analyzer.calculate_equipment_health('EQ002')
    assert health.total_failure_events == 2
    assert health.failure_probability > 0.2  # Should be elevated due to past failures
    assert health.risk_level in ('low', 'medium', 'high')


def test_create_project_intelligence(analyzer):
    """Test creation of complete equipment intelligence"""
    eq1 = Equipment(equipment_id='EQ003', name='Pump 1', equipment_type=EquipmentType.CONCRETE_PUMP, acquisition_date='2021-01-01')
    eq2 = Equipment(equipment_id='EQ004', name='Generator 1', equipment_type=EquipmentType.GENERATOR, acquisition_date='2020-06-01')
    
    analyzer.add_equipment(eq1)
    analyzer.add_equipment(eq2)
    
    # Add maintenance for eq1
    rec1 = MaintenanceRecord(
        project_id='P2',
        equipment_id='EQ003',
        maintenance_date='2025-01-15',
        maintenance_type='preventive',
        duration_hours=4.0,
        cost=500.0,
        completed=True
    )
    analyzer.add_maintenance_record(rec1)
    
    # Add failure for eq2
    evt1 = FailureEvent(
        project_id='P2',
        task_id='T1',
        equipment_id='EQ004',
        failure_date='2024-12-01',
        failure_type='generator_failure',
        repair_duration_hours=12.0,
        repair_cost=2000.0,
        downtime_impact_days=1.0
    )
    analyzer.add_failure_event(evt1)
    
    intel = analyzer.create_project_intelligence(
        project_id='P2',
        project_name='Site A',
        equipment_ids=['EQ003', 'EQ004']
    )
    
    assert intel.project_id == 'P2'
    assert intel.integration_ready
    assert 'EQ003' in intel.equipment_summaries
    assert 'EQ004' in intel.equipment_summaries
    assert 0.0 <= intel.equipment_risk_score <= 1.0
    assert intel.project_summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
