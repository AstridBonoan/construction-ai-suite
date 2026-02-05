"""
Phase 16: Smart Schedule Dependencies & Delay Propagation - Type Definitions

Data structures for task dependencies, critical path analysis, and delay propagation.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    DELAYED = "delayed"


class DependencyType(str, Enum):
    """Types of task dependencies (PMBOK standard)"""
    FINISH_TO_START = "finish_to_start"      # Task B can't start until Task A finishes
    START_TO_START = "start_to_start"        # Task B starts when Task A starts (parallel)
    FINISH_TO_FINISH = "finish_to_finish"    # Task B finishes when Task A finishes
    START_TO_FINISH = "start_to_finish"      # Task B finishes when Task A starts (rare)


@dataclass
class Task:
    """Represents a construction project task"""
    task_id: str
    name: str
    duration_days: int
    status: TaskStatus = TaskStatus.NOT_STARTED
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_completion_days: int = 0
    actual_delay_days: int = 0
    complexity_factor: float = 1.0  # 0.5-2.0, affects delay likelihood
    weather_dependency: bool = False
    resource_constrained: bool = False
    critical_path_member: bool = False
    
    def __hash__(self):
        return hash(self.task_id)
    
    def __eq__(self, other):
        if isinstance(other, Task):
            return self.task_id == other.task_id
        return False


@dataclass
class TaskDependency:
    """Represents a dependency relationship between two tasks"""
    dependency_id: str
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: DependencyType
    lag_days: int = 0  # Time buffer between predecessor finish and successor start
    criticality_score: float = 0.0  # 0-1, how critical this dependency is to delays
    
    def __hash__(self):
        return hash(self.dependency_id)


@dataclass
class CriticalPathAnalysis:
    """Results of critical path analysis"""
    critical_path: List[str]  # List of task IDs on critical path
    project_duration_days: int
    slack_by_task: Dict[str, int]  # Task ID -> days of slack/float
    critical_tasks: Set[str]
    bottleneck_tasks: List[str]  # Tasks with zero slack that are delay risks


@dataclass
class DelayPropagation:
    """Model of how a delay cascades through the project"""
    initial_task_id: str
    initial_delay_days: int
    affected_tasks: Dict[str, int]  # Task ID -> cumulative delay propagated to it
    propagation_path: List[str]  # Path through dependencies
    total_project_delay_days: int  # Impact on final project completion
    confidence_score: float  # 0-1
    explanation: str


@dataclass
class ScheduleRiskFactors:
    """Quantified risk factors for schedule delays"""
    task_id: str
    base_delay_probability: float  # 0-1
    weather_risk: float  # 0-1
    resource_risk: float  # 0-1
    dependency_risk: float  # 0-1
    complexity_risk: float  # 0-1
    combined_delay_probability: float  # 0-1, aggregated
    expected_delay_days: float  # Expected value of delay
    worst_case_delay_days: int
    confidence_level: str  # Low/Medium/High


@dataclass
class ProjectScheduleIntelligence:
    """Complete schedule intelligence for a project"""
    project_id: str
    project_name: str
    total_tasks: int
    critical_path_analysis: CriticalPathAnalysis
    task_risk_factors: Dict[str, ScheduleRiskFactors]
    delay_scenarios: List[DelayPropagation]  # Simulated scenarios
    schedule_resilience_score: float  # 0-1, how resilient schedule is to delays
    high_risk_dependencies: List[TaskDependency]
    recommended_buffer_days: int
    integration_risk_score: float  # For Feature 1 integration (0-1)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "total_tasks": self.total_tasks,
            "critical_path": self.critical_path_analysis.critical_path,
            "project_duration_days": self.critical_path_analysis.project_duration_days,
            "schedule_resilience_score": self.schedule_resilience_score,
            "high_risk_task_count": len(self.high_risk_dependencies),
            "recommended_buffer_days": self.recommended_buffer_days,
            "integration_risk_score": self.integration_risk_score,
        }
