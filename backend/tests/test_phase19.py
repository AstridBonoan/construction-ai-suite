"""
Unit tests for Phase 19 Subcontractor Performance Analyzer
"""
import pytest
from phase19_subcontractor_types import Subcontractor, SubcontractorPerformanceRecord, SubcontractorIntelligence
from phase19_subcontractor_analyzer import SubcontractorPerformanceAnalyzer
from datetime import datetime


@pytest.fixture
def analyzer():
    return SubcontractorPerformanceAnalyzer()


def test_subcontractor_summary_basic(analyzer):
    s = Subcontractor(subcontractor_id='S001', name='Acme Trade')
    analyzer.add_subcontractor(s)

    # add a mix of on-time and late records
    for i in range(5):
        rec = SubcontractorPerformanceRecord(
            project_id='P1', task_id=f'T{i}', subcontractor_id='S001',
            scheduled_finish_date='2025-01-01', actual_finish_date='2025-01-01',
            days_delay=0.0, completed=True, quality_issues=0
        )
        analyzer.add_record(rec)

    # two late
    for i in range(2):
        rec = SubcontractorPerformanceRecord(
            project_id='P1', task_id=f'LT{i}', subcontractor_id='S001',
            scheduled_finish_date='2025-01-01', actual_finish_date='2025-01-03',
            days_delay=2.0, completed=True, quality_issues=1
        )
        analyzer.add_record(rec)

    summary = analyzer.calculate_subcontractor_summary('S001')
    assert summary.total_tasks == 7
    assert summary.late_count == 2
    assert summary.on_time_count >= 5
    assert 0.0 <= summary.reliability_score <= 1.0


def test_create_project_intelligence(analyzer):
    s = Subcontractor(subcontractor_id='S002', name='Builders Co')
    analyzer.add_subcontractor(s)

    # poor performance
    for i in range(6):
        rec = SubcontractorPerformanceRecord(
            project_id='P2', task_id=f'X{i}', subcontractor_id='S002',
            scheduled_finish_date='2025-01-01', actual_finish_date='2025-01-05',
            days_delay=4.0, completed=True, quality_issues=2
        )
        analyzer.add_record(rec)

    intel = analyzer.create_project_intelligence(project_id='P2', project_name='Proj2', subcontractor_ids=['S002'])
    assert intel.project_id == 'P2'
    assert intel.integration_ready
    assert 'S002' in intel.subcontractor_summaries
    assert 0.0 <= intel.subcontractor_risk_score <= 1.0

*** End Patch