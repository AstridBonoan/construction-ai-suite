"""
Phase 18: Workforce Reliability & Attendance Intelligence - Analyzer

Implements workforce scoring, pattern detection, and risk analysis.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from phase18_workforce_types import (
    Worker, AttendanceRecord, Team, AttendanceStatus,
    WorkerAttendanceSummary, TeamAttendanceSummary, WorkforceRiskInsight,
    WorkforceProjectSummary, WorkforceIntelligence
)

logger = logging.getLogger(__name__)


class WorkforceReliabilityAnalyzer:
    """Analyzes workforce attendance, reliability, and risk patterns"""
    
    def __init__(self):
        self.workers: Dict[str, Worker] = {}
        self.teams: Dict[str, Team] = {}
        self.attendance_records: List[AttendanceRecord] = []
    
    def add_worker(self, worker: Worker) -> None:
        """Add a worker to the workforce database"""
        self.workers[worker.worker_id] = worker
        logger.info(f"Added worker {worker.worker_id}: {worker.name}")
    
    def add_team(self, team: Team) -> None:
        """Add a team to the database"""
        self.teams[team.team_id] = team
        logger.info(f"Added team {team.team_id}: {team.team_name}")
    
    def add_attendance_record(self, record: AttendanceRecord) -> None:
        """Add an attendance record"""
        self.attendance_records.append(record)
    
    def add_attendance_records(self, records: List[AttendanceRecord]) -> None:
        """Bulk add attendance records"""
        self.attendance_records.extend(records)
        logger.info(f"Added {len(records)} attendance records")
    
    def calculate_worker_summary(self, worker_id: str) -> WorkerAttendanceSummary:
        """Calculate attendance summary for a worker"""
        worker = self.workers.get(worker_id)
        if not worker:
            logger.warning(f"Worker {worker_id} not found")
            return WorkerAttendanceSummary(worker_id=worker_id, worker_name="Unknown")
        
        # Filter records for this worker (records have task_id matching worker_id)
        worker_records = [r for r in self.attendance_records if r.task_id == worker_id]
        
        if not worker_records:
            return WorkerAttendanceSummary(
                worker_id=worker_id,
                worker_name=worker.name,
                reliability_score=1.0,
                explanation="No attendance data available"
            )
        
        # Calculate metrics
        total_shifts = len(worker_records)
        shifts_present = sum(1 for r in worker_records if r.status == AttendanceStatus.PRESENT)
        shifts_late = sum(1 for r in worker_records if r.status == AttendanceStatus.LATE)
        shifts_absent = sum(1 for r in worker_records if r.status == AttendanceStatus.ABSENT)
        shifts_excused = sum(1 for r in worker_records if r.status in (
            AttendanceStatus.EXCUSED, AttendanceStatus.SICK_LEAVE, AttendanceStatus.VACATION
        ))
        
        avg_minutes_late = (sum(r.minutes_late for r in worker_records if r.status == AttendanceStatus.LATE) / 
                           max(shifts_late, 1) if shifts_late > 0 else 0)
        absence_rate = (shifts_absent + shifts_excused) / total_shifts if total_shifts > 0 else 0
        tardiness_rate = shifts_late / total_shifts if total_shifts > 0 else 0
        
        # Reliability score: penalize absences and tardiness
        reliability_score = max(0.0, 1.0 
                               - (absence_rate * 0.4)  # Absences hurt more
                               - (tardiness_rate * 0.2))  # Tardiness hurts less
        
        # Confidence: higher with more data points
        confidence_score = min(1.0, total_shifts / 20)
        
        # Detect patterns
        recent_records = worker_records[-5:] if len(worker_records) > 5 else worker_records
        recent_absence_rate = sum(1 for r in recent_records if r.status == AttendanceStatus.ABSENT) / len(recent_records)
        overall_absence_rate = absence_rate
        
        if recent_absence_rate > overall_absence_rate + 0.1:
            recent_pattern = "declining"
            risk_level = "high" if absence_rate > 0.2 else "medium"
        elif recent_absence_rate < overall_absence_rate - 0.1:
            recent_pattern = "improving"
            risk_level = "low"
        else:
            recent_pattern = "stable"
            risk_level = "high" if absence_rate > 0.25 else "medium" if absence_rate > 0.1 else "low"
        
        explanation = f"{worker.name}: {shifts_present}/{total_shifts} present, "
        if shifts_late > 0:
            explanation += f"{shifts_late} late (avg {avg_minutes_late:.1f} min), "
        if shifts_absent > 0:
            explanation += f"{shifts_absent} absent. "
        explanation += f"Pattern: {recent_pattern}."
        
        return WorkerAttendanceSummary(
            worker_id=worker_id,
            worker_name=worker.name,
            total_shifts=total_shifts,
            shifts_present=shifts_present,
            shifts_late=shifts_late,
            shifts_absent=shifts_absent,
            shifts_excused=shifts_excused,
            avg_minutes_late=avg_minutes_late,
            absence_rate=absence_rate,
            tardiness_rate=tardiness_rate,
            reliability_score=reliability_score,
            confidence_score=confidence_score,
            explanation=explanation,
            risk_level=risk_level,
            recent_pattern=recent_pattern
        )
    
    def calculate_team_summary(self, team_id: str) -> TeamAttendanceSummary:
        """Calculate attendance summary for a team"""
        team = self.teams.get(team_id)
        if not team:
            logger.warning(f"Team {team_id} not found")
            return TeamAttendanceSummary(team_id=team_id, team_name="Unknown")
        
        member_summaries = [self.calculate_worker_summary(wid) for wid in team.members]
        
        if not member_summaries:
            return TeamAttendanceSummary(
                team_id=team_id,
                team_name=team.team_name,
                member_count=0,
                avg_reliability_score=1.0,
                explanation="No team members or data"
            )
        
        avg_reliability = sum(s.reliability_score for s in member_summaries) / len(member_summaries)
        total_absences = sum(s.shifts_absent for s in member_summaries)
        total_late = sum(s.shifts_late for s in member_summaries)
        
        team_risk_level = "high" if avg_reliability < 0.6 else "medium" if avg_reliability < 0.8 else "low"
        
        explanation = f"Team {team.team_name}: {len(member_summaries)} members, "
        explanation += f"avg reliability {avg_reliability:.2f}. Total absences: {total_absences}, late shifts: {total_late}."
        
        return TeamAttendanceSummary(
            team_id=team_id,
            team_name=team.team_name,
            member_count=len(member_summaries),
            avg_reliability_score=avg_reliability,
            total_absences=total_absences,
            total_late_shifts=total_late,
            team_risk_level=team_risk_level,
            explanation=explanation
        )
    
    def identify_risk_insights(self, project_id: str, task_id: str) -> List[WorkforceRiskInsight]:
        """Identify risk insights for a specific task or project"""
        insights = []
        
        # Find records for this task (task_id is worker_id in our model)
        task_records = [r for r in self.attendance_records 
                       if r.project_id == project_id and r.task_id == task_id]
        
        if not task_records:
            return insights
        
        # Get the worker
        worker = self.workers.get(task_id)
        if not worker:
            return insights
        
        summary = self.calculate_worker_summary(task_id)
        
        # Generate insights based on patterns
        if summary.absence_rate > 0.2:
            insights.append(WorkforceRiskInsight(
                worker_id=worker.worker_id,
                project_id=project_id,
                task_id=task_id,
                identified_issue="high_absence_rate",
                risk_severity="high",
                impact_on_schedule=f"High absence rate ({summary.absence_rate:.0%}) may cause {summary.absence_rate * 10:.0f} day delays",
                impact_on_cost=f"Lost productivity: ${summary.absence_rate * 5000:.0f}",
                confidence_score=summary.confidence_score,
                recommendation=f"Monitor {worker.name} closely or allocate backup resources",
                monday_column_suggestion="Workforce_Risk_Flag"
            ))
        
        if summary.tardiness_rate > 0.3:
            insights.append(WorkforceRiskInsight(
                worker_id=worker.worker_id,
                project_id=project_id,
                task_id=task_id,
                identified_issue="chronic_tardiness",
                risk_severity="medium",
                impact_on_schedule=f"Chronic tardiness (avg {summary.avg_minutes_late:.0f} min) may cause 2-3 day delays on long projects",
                impact_on_cost=f"Reduced productivity: ${summary.tardiness_rate * 2000:.0f}",
                confidence_score=summary.confidence_score,
                recommendation=f"Set clear start time expectations or adjust task scheduling",
                monday_column_suggestion="Attendance_Flag"
            ))
        
        return insights
    
    def create_project_intelligence(
        self,
        project_id: str,
        project_name: str,
        worker_ids: List[str],
        team_ids: List[str]
    ) -> WorkforceIntelligence:
        """Create complete workforce intelligence for a project"""
        
        # Generate worker and team summaries
        worker_summaries = {wid: self.calculate_worker_summary(wid) for wid in worker_ids}
        team_summaries = {tid: self.calculate_team_summary(tid) for tid in team_ids}
        
        # Gather all risk insights for this project
        all_insights = []
        for record in self.attendance_records:
            if record.project_id == project_id:
                insights = self.identify_risk_insights(project_id, record.task_id)
                all_insights.extend(insights)
        
        # Calculate project-level summary
        avg_team_reliability = (sum(s.avg_reliability_score for s in team_summaries.values()) / 
                               len(team_summaries) if team_summaries else 1.0)
        
        high_risk_workers = [wid for wid, summary in worker_summaries.items() 
                            if summary.risk_level == "high"]
        
        total_schedule_risk = sum(
            (1 - summary.reliability_score) * 5  # Up to 5 days per worker
            for summary in worker_summaries.values()
        )
        
        total_cost_impact = sum(
            (1 - summary.reliability_score) * 3000  # Up to $3k per worker
            for summary in worker_summaries.values()
        )
        
        overall_workforce_risk_score = 1.0 - avg_team_reliability
        
        key_insights = []
        if len(high_risk_workers) > 0:
            key_insights.append(f"{len(high_risk_workers)} high-risk workers detected")
        if total_schedule_risk > 0:
            key_insights.append(f"Estimated schedule risk: {total_schedule_risk:.1f} days")
        if avg_team_reliability < 0.7:
            key_insights.append("Workforce reliability below acceptable threshold")
        
        recommendations = []
        if len(high_risk_workers) > 0:
            recommendations.append("Allocate backup resources for high-risk workers")
        if total_schedule_risk > 5:
            recommendations.append("Add schedule buffer (10-15% contingency)")
        if avg_team_reliability < 0.8:
            recommendations.append("Conduct workforce performance review and training")
        
        project_summary = WorkforceProjectSummary(
            project_id=project_id,
            project_name=project_name,
            total_workers=len(worker_ids),
            avg_team_reliability=avg_team_reliability,
            high_risk_workers=high_risk_workers,
            critical_absences_count=sum(s.shifts_absent for s in worker_summaries.values()),
            total_schedule_risk_days=total_schedule_risk,
            total_cost_impact=total_cost_impact,
            overall_workforce_risk_score=overall_workforce_risk_score,
            key_insights=key_insights,
            recommendations=recommendations,
            explanation=f"Project {project_name}: {len(worker_ids)} workers across {len(team_ids)} teams. "
                       f"Avg reliability {avg_team_reliability:.2f}. "
                       f"Estimated schedule impact: {total_schedule_risk:.1f} days, cost impact: ${total_cost_impact:.0f}."
        )
        
        intelligence = WorkforceIntelligence(
            project_id=project_id,
            project_name=project_name,
            generated_at=datetime.utcnow().isoformat() + 'Z',
            worker_summaries=worker_summaries,
            team_summaries=team_summaries,
            risk_insights=all_insights[:10],  # Top 10 insights
            project_summary=project_summary,
            workforce_risk_score=overall_workforce_risk_score,
            integration_ready=True
        )
        
        logger.info(f"Created workforce intelligence for {project_name}: risk_score={overall_workforce_risk_score:.2f}")
        
        return intelligence
