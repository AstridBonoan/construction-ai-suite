"""
Phase 16: Smart Schedule Dependencies - Core Dependency Analysis

Analyzes task dependencies, computes critical path, and identifies schedule risks.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque
from phase16_types import (
    Task, TaskDependency, DependencyType, CriticalPathAnalysis,
    ScheduleRiskFactors, TaskStatus
)

logger = logging.getLogger(__name__)


class ScheduleDependencyAnalyzer:
    """Analyzes task dependencies and critical path in construction schedules"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str, TaskDependency] = {}
        self.adjacency_list: Dict[str, List[str]] = defaultdict(list)  # task_id -> successors
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # task_id -> predecessors
    
    def add_task(self, task: Task) -> None:
        """Register a task in the schedule"""
        if task.task_id in self.tasks:
            logger.warning(f"Task {task.task_id} already exists, overwriting")
        self.tasks[task.task_id] = task
    
    def add_dependency(self, dependency: TaskDependency) -> None:
        """Register a dependency relationship"""
        pred_id = dependency.predecessor_task_id
        succ_id = dependency.successor_task_id
        
        # Validate tasks exist
        if pred_id not in self.tasks:
            logger.error(f"Predecessor task {pred_id} not found")
            return
        if succ_id not in self.tasks:
            logger.error(f"Successor task {succ_id} not found")
            return
        
        # Register dependency
        self.dependencies[dependency.dependency_id] = dependency
        self.adjacency_list[pred_id].append(succ_id)
        self.reverse_adjacency[succ_id].append(pred_id)
        
        logger.debug(f"Added dependency: {pred_id} -> {succ_id} ({dependency.dependency_type})")
    
    def calculate_critical_path(self) -> CriticalPathAnalysis:
        """
        Calculate critical path using forward/backward pass (CPM algorithm).
        
        Returns:
            CriticalPathAnalysis with critical path and slack times
        """
        logger.info("Calculating critical path...")
        
        # Step 1: Forward pass - calculate earliest start/finish times
        earliest_start = {}
        earliest_finish = {}
        
        # Topological sort to process tasks in order
        in_degree = {task_id: len(self.reverse_adjacency[task_id]) 
                    for task_id in self.tasks}
        queue = deque([t for t in self.tasks if in_degree[t] == 0])
        
        while queue:
            task_id = queue.popleft()
            task = self.tasks[task_id]
            
            # Earliest start = max(earliest finish of predecessors + lag)
            if task_id in self.reverse_adjacency and self.reverse_adjacency[task_id]:
                pred_ids = self.reverse_adjacency[task_id]
                max_pred_finish = 0
                for pred_id in pred_ids:
                    if pred_id in earliest_finish:
                        # Find lag for this dependency
                        lag = 0
                        for dep in self.dependencies.values():
                            if dep.predecessor_task_id == pred_id and dep.successor_task_id == task_id:
                                lag = dep.lag_days
                                break
                        max_pred_finish = max(max_pred_finish, earliest_finish[pred_id] + lag)
                earliest_start[task_id] = max_pred_finish
            else:
                earliest_start[task_id] = 0
            
            earliest_finish[task_id] = earliest_start[task_id] + task.duration_days
            
            # Queue successors
            for succ_id in self.adjacency_list[task_id]:
                in_degree[succ_id] -= 1
                if in_degree[succ_id] == 0:
                    queue.append(succ_id)
        
        # Step 2: Backward pass - calculate latest start/finish times
        project_duration = max(earliest_finish.values()) if earliest_finish else 0
        latest_finish = {task_id: project_duration for task_id in self.tasks}
        latest_start = {}
        
        # Process in reverse topological order
        out_degree = {task_id: len(self.adjacency_list[task_id]) for task_id in self.tasks}
        queue = deque([t for t in self.tasks if out_degree[t] == 0])
        
        while queue:
            task_id = queue.popleft()
            
            if task_id in self.adjacency_list and self.adjacency_list[task_id]:
                succ_ids = self.adjacency_list[task_id]
                min_succ_start = float('inf')
                for succ_id in succ_ids:
                    if succ_id in latest_start:
                        # Find lag
                        lag = 0
                        for dep in self.dependencies.values():
                            if dep.predecessor_task_id == task_id and dep.successor_task_id == succ_id:
                                lag = dep.lag_days
                                break
                        min_succ_start = min(min_succ_start, latest_start[succ_id] - lag)
                if min_succ_start != float('inf'):
                    latest_finish[task_id] = min_succ_start
                else:
                    latest_finish[task_id] = earliest_finish.get(task_id, project_duration)
            
            latest_start[task_id] = latest_finish[task_id] - self.tasks[task_id].duration_days
            
            # Queue predecessors
            for pred_id in self.reverse_adjacency[task_id]:
                out_degree[pred_id] -= 1
                if out_degree[pred_id] == 0:
                    queue.append(pred_id)
        
        # Step 3: Identify critical path (slack = 0)
        slack = {}
        critical_tasks = set()
        for task_id in self.tasks:
            slack[task_id] = latest_start.get(task_id, 0) - earliest_start.get(task_id, 0)
            if slack[task_id] == 0:
                critical_tasks.add(task_id)
        
        # Build critical path
        critical_path = self._build_critical_path(critical_tasks)
        
        # Identify bottlenecks (critical tasks with dependent tasks)
        bottlenecks = [t for t in critical_tasks 
                      if len(self.adjacency_list[t]) > 0 and 
                      any(self.tasks[succ].status != TaskStatus.COMPLETED 
                          for succ in self.adjacency_list[t])]
        
        result = CriticalPathAnalysis(
            critical_path=critical_path,
            project_duration_days=int(project_duration),
            slack_by_task=slack,
            critical_tasks=critical_tasks,
            bottleneck_tasks=bottlenecks
        )
        
        logger.info(f"Critical path length: {len(critical_path)} tasks, duration: {project_duration:.0f} days")
        return result
    
    def _build_critical_path(self, critical_tasks: Set[str]) -> List[str]:
        """Reconstruct critical path from critical tasks"""
        if not critical_tasks:
            return []
        
        # Find start node (no predecessors on critical path)
        start = None
        for task_id in critical_tasks:
            preds = self.reverse_adjacency[task_id]
            if not any(p in critical_tasks for p in preds):
                start = task_id
                break
        
        if not start:
            start = list(critical_tasks)[0]
        
        # Follow critical path
        path = [start]
        current = start
        while True:
            # Find next critical task
            successors = self.adjacency_list[current]
            next_task = None
            for succ in successors:
                if succ in critical_tasks:
                    next_task = succ
                    break
            
            if next_task is None:
                break
            path.append(next_task)
            current = next_task
        
        return path
    
    def calculate_risk_factors(self, task_id: str) -> ScheduleRiskFactors:
        """
        Calculate schedule risk factors for a task.
        
        Considers: complexity, weather dependency, resource constraints, dependency risk
        """
        if task_id not in self.tasks:
            logger.error(f"Task {task_id} not found")
            return None
        
        task = self.tasks[task_id]
        
        # Base probabilities
        base_delay = 0.2 + (task.complexity_factor - 1.0) * 0.3  # 0.2-0.5
        weather_risk = 0.3 if task.weather_dependency else 0.05
        resource_risk = 0.25 if task.resource_constrained else 0.1
        
        # Dependency risk: how many successors depend on this?
        num_successors = len(self.adjacency_list[task_id])
        dependency_risk = min(0.5, num_successors * 0.15)  # More dependents = more impact
        
        # Complexity risk
        complexity_risk = min(0.6, task.complexity_factor * 0.4)
        
        # Combine risks (not simple sum, use compound probability)
        combined = 1.0
        for risk in [base_delay, weather_risk, resource_risk, complexity_risk]:
            combined *= (1.0 - risk)
        combined_delay_prob = 1.0 - combined
        
        # Expected delay
        expected_delay = task.duration_days * combined_delay_prob * 0.3  # Assume 30% of duration
        worst_case = int(task.duration_days * 0.5)  # Worst case 50% delay
        
        # Confidence
        conf_pct = min(95, 60 + (task.complexity_factor - 1.0) * 20)
        conf_level = "High" if conf_pct >= 80 else "Medium" if conf_pct >= 60 else "Low"
        
        return ScheduleRiskFactors(
            task_id=task_id,
            base_delay_probability=base_delay,
            weather_risk=weather_risk,
            resource_risk=resource_risk,
            dependency_risk=dependency_risk,
            complexity_risk=complexity_risk,
            combined_delay_probability=combined_delay_prob,
            expected_delay_days=expected_delay,
            worst_case_delay_days=worst_case,
            confidence_level=conf_level
        )
    
    def get_task_impact_scope(self, task_id: str) -> Dict[str, int]:
        """
        BFS to find all tasks affected if this task is delayed.
        Returns dict of {affected_task_id: propagation_distance}
        """
        affected = {}
        visited = set()
        queue = deque([(task_id, 0)])
        
        while queue:
            current, distance = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            
            if current != task_id:
                affected[current] = distance
            
            for successor in self.adjacency_list[current]:
                if successor not in visited:
                    queue.append((successor, distance + 1))
        
        return affected
