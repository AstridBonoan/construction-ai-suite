"""
Unit tests for Phase 18: Workforce Reliability & Attendance Intelligence
"""

import pytest
from datetime import datetime, timedelta
from phase18_workforce_types import (
    Worker, Team, AttendanceRecord, AttendanceStatus, WorkerRole,
    WorkerAttendanceSummary
)
from phase18_workforce_analyzer import WorkforceReliabilityAnalyzer


@pytest.fixture
def analyzer():
    """Create a fresh analyzer for each test"""
    return WorkforceReliabilityAnalyzer()


@pytest.fixture
def sample_workers():
    """Create sample workers for testing"""
    return [
        Worker(
            worker_id="W001",
            name="Alice",
            role=WorkerRole.SKILLED_TRADES,
            email="alice@example.com"
        ),
        Worker(
            worker_id="W002",
            name="Bob",
            role=WorkerRole.LABORER,
            email="bob@example.com"
        ),
        Worker(
            worker_id="W003",
            name="Charlie",
            role=WorkerRole.SUPERVISOR,
            email="charlie@example.com"
        ),
    ]


@pytest.fixture
def sample_teams(sample_workers):
    """Create sample teams"""
    return [
        Team(
            team_id="T001",
            team_name="Foundation Team",
            lead_worker_id="W003",
            members=["W001", "W002", "W003"]
        ),
    ]


@pytest.fixture
def sample_attendance_records():
    """Create sample attendance records"""
    records = []
    base_date = datetime(2025, 1, 1)
    
    # Alice: mostly present, occasional tardiness (reliable)
    for i in range(20):
        date = (base_date + timedelta(days=i)).isoformat().split('T')[0]
        if i % 20 == 5:
            status = AttendanceStatus.LATE
            minutes_late = 15
        else:
            status = AttendanceStatus.PRESENT
            minutes_late = 0
        
        records.append(AttendanceRecord(
            shift_date=date,
            shift_id=f"SHIFT_{i}",
            status=status,
            scheduled_start="08:00",
            actual_start="08:15" if minutes_late > 0 else "08:00",
            scheduled_end="17:00",
            actual_end="17:00",
            minutes_late=minutes_late,
            project_id="P001",
            task_id="W001",
            notes=""
        ))
    
    # Bob: frequent absences and tardiness (unreliable)
    for i in range(20):
        date = (base_date + timedelta(days=i)).isoformat().split('T')[0]
        if i % 4 == 0:
            status = AttendanceStatus.ABSENT
            minutes_late = 0
        elif i % 5 == 0:
            status = AttendanceStatus.LATE
            minutes_late = 30
        else:
            status = AttendanceStatus.PRESENT
            minutes_late = 0
        
        records.append(AttendanceRecord(
            shift_date=date,
            shift_id=f"SHIFT_{i}_B",
            status=status,
            scheduled_start="08:00",
            actual_start="08:30" if minutes_late > 0 else "08:00" if status == AttendanceStatus.PRESENT else None,
            scheduled_end="17:00",
            actual_end="17:00" if status == AttendanceStatus.PRESENT else None,
            minutes_late=minutes_late,
            project_id="P001",
            task_id="W002",
            notes=""
        ))
    
    # Charlie: perfect attendance (very reliable)
    for i in range(20):
        date = (base_date + timedelta(days=i)).isoformat().split('T')[0]
        records.append(AttendanceRecord(
            shift_date=date,
            shift_id=f"SHIFT_{i}_C",
            status=AttendanceStatus.PRESENT,
            scheduled_start="08:00",
            actual_start="08:00",
            scheduled_end="17:00",
            actual_end="17:00",
            minutes_late=0,
            project_id="P001",
            task_id="W003",
            notes=""
        ))
    
    return records


class TestWorkforceModels:
    """Test workforce data models"""
    
    def test_create_worker(self):
        worker = Worker(
            worker_id="W001",
            name="Test Worker",
            role=WorkerRole.LABORER,
            email="test@example.com"
        )
        assert worker.worker_id == "W001"
        assert worker.name == "Test Worker"
        assert worker.role == WorkerRole.LABORER
    
    def test_create_team(self):
        team = Team(
            team_id="T001",
            team_name="Test Team",
            members=["W001", "W002"]
        )
        assert team.team_id == "T001"
        assert len(team.members) == 2
    
    def test_attendance_record(self):
        record = AttendanceRecord(
            shift_date="2025-01-01",
            shift_id="S001",
            status=AttendanceStatus.PRESENT,
            scheduled_start="08:00",
            actual_start="08:00",
            scheduled_end="17:00"
        )
        assert record.status == AttendanceStatus.PRESENT
        assert record.minutes_late == 0


class TestWorkforceAnalyzer:
    """Test the workforce analyzer"""
    
    def test_add_worker(self, analyzer, sample_workers):
        analyzer.add_worker(sample_workers[0])
        assert "W001" in analyzer.workers
        assert analyzer.workers["W001"].name == "Alice"
    
    def test_add_team(self, analyzer, sample_teams):
        analyzer.add_team(sample_teams[0])
        assert "T001" in analyzer.teams
        assert analyzer.teams["T001"].team_name == "Foundation Team"
    
    def test_add_attendance_records(self, analyzer, sample_attendance_records):
        analyzer.add_attendance_records(sample_attendance_records)
        assert len(analyzer.attendance_records) == 60  # 20 per worker
    
    def test_calculate_worker_summary_reliable(self, analyzer, sample_workers, sample_attendance_records):
        """Test scoring of reliable worker (Alice)"""
        for worker in sample_workers:
            analyzer.add_worker(worker)
        analyzer.add_attendance_records(sample_attendance_records)
        
        summary = analyzer.calculate_worker_summary("W001")
        assert summary.worker_id == "W001"
        assert summary.total_shifts == 20
        assert summary.reliability_score > 0.85  # Alice is very reliable
        assert summary.risk_level == "low"
    
    def test_calculate_worker_summary_unreliable(self, analyzer, sample_workers, sample_attendance_records):
        """Test scoring of unreliable worker (Bob)"""
        for worker in sample_workers:
            analyzer.add_worker(worker)
        analyzer.add_attendance_records(sample_attendance_records)
        
        summary = analyzer.calculate_worker_summary("W002")
        assert summary.worker_id == "W002"
        assert summary.reliability_score < 0.90  # Bob is less reliable than Alice/Charlie
        assert summary.risk_level in ("low", "medium")  # Might be medium due to absences
        assert summary.absence_rate > 0.15  # Bob has significant absences
        assert summary.tardiness_rate > 0.1  # Bob is also frequently late
    
    def test_calculate_worker_summary_perfect(self, analyzer, sample_workers, sample_attendance_records):
        """Test scoring of perfect worker (Charlie)"""
        for worker in sample_workers:
            analyzer.add_worker(worker)
        analyzer.add_attendance_records(sample_attendance_records)
        
        summary = analyzer.calculate_worker_summary("W003")
        assert summary.reliability_score > 0.95  # Charlie has perfect attendance
        assert summary.absence_rate == 0.0
        assert summary.tardiness_rate == 0.0
    
    def test_calculate_team_summary(self, analyzer, sample_workers, sample_teams, sample_attendance_records):
        """Test team-level scoring"""
        for worker in sample_workers:
            analyzer.add_worker(worker)
        for team in sample_teams:
            analyzer.add_team(team)
        analyzer.add_attendance_records(sample_attendance_records)
        
        summary = analyzer.calculate_team_summary("T001")
        assert summary.team_id == "T001"
        assert summary.member_count == 3
        # With proper filtering: Alice is reliable (95%+), Bob is medium (87%), Charlie is perfect (100%)
        # Team average should be high overall but pulled down slightly by Bob
        assert summary.avg_reliability_score > 0.85
    
    def test_create_project_intelligence(self, analyzer, sample_workers, sample_teams, sample_attendance_records):
        """Test complete project intelligence generation"""
        for worker in sample_workers:
            analyzer.add_worker(worker)
        for team in sample_teams:
            analyzer.add_team(team)
        analyzer.add_attendance_records(sample_attendance_records)
        
        intelligence = analyzer.create_project_intelligence(
            project_id="P001",
            project_name="Foundation Project",
            worker_ids=["W001", "W002", "W003"],
            team_ids=["T001"]
        )
        
        assert intelligence.project_id == "P001"
        assert intelligence.integration_ready
        assert "W001" in intelligence.worker_summaries
        assert "T001" in intelligence.team_summaries
        assert intelligence.project_summary is not None
        assert intelligence.workforce_risk_score >= 0.0
        assert intelligence.workforce_risk_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
