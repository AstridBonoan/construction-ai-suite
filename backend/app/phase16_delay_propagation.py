"""
Phase 16: Delay Propagation Engine - Cascading Delay Modeling

Models how delays cascade through task dependencies and integrates with Feature 1 risk scoring.
"""

import logging
from typing import Dict, List, Optional, Set
from phase16_types import (
    DelayPropagation, ProjectScheduleIntelligence, Task, TaskDependency,
    CriticalPathAnalysis, ScheduleRiskFactors, DependencyType
)

logger = logging.getLogger(__name__)


class DelayPropagationEngine:
    """Models and simulates cascading delays through project schedule"""
    
    def __init__(self, analyzer):
        """
        Args:
            analyzer: ScheduleDependencyAnalyzer instance
        """
        self.analyzer = analyzer
    
    def simulate_task_delay(
        self,
        task_id: str,
        delay_days: int,
        critical_path: List[str]
    ) -> DelayPropagation:
        """
        Simulate impact of delaying a task and track propagation.
        
        Args:
            task_id: Task to delay
            delay_days: Number of days to delay
            critical_path: List of critical path task IDs
        
        Returns:
            DelayPropagation object with simulation results
        """
        if task_id not in self.analyzer.tasks:
            logger.error(f"Task {task_id} not found")
            return None
        
        logger.info(f"Simulating {delay_days}-day delay on task {task_id}")
        
        affected_tasks = {}
        propagation_path = [task_id]
        
        # BFS to track delay propagation
        visited = set()
        queue = [(task_id, delay_days)]
        
        while queue:
            current_task, current_delay = queue.pop(0)
            
            if current_task in visited:
                continue
            visited.add(current_task)
            
            if current_task != task_id:
                affected_tasks[current_task] = current_delay
            
            # Propagate to successors
            successors = self.analyzer.adjacency_list[current_task]
            for succ_id in successors:
                if succ_id not in visited:
                    # Find the dependency relationship
                    lag = 0
                    for dep in self.analyzer.dependencies.values():
                        if dep.predecessor_task_id == current_task and dep.successor_task_id == succ_id:
                            lag = dep.lag_days
                            break
                    
                    # Delay propagates if lag < current_delay
                    propagated_delay = max(0, current_delay - lag)
                    
                    if propagated_delay > 0:
                        queue.append((succ_id, propagated_delay))
                        propagation_path.append(succ_id)
        
        # Calculate total project delay
        # This is the maximum propagation to any task on critical path
        total_project_delay = 0
        for cp_task in critical_path:
            if cp_task in affected_tasks:
                total_project_delay = max(total_project_delay, affected_tasks[cp_task])
        
        # Confidence: higher if on critical path
        confidence = 0.95 if task_id in critical_path else 0.75
        
        # Explanation
        explanation = f"Task {self.analyzer.tasks[task_id].name} delayed by {delay_days} days. "
        if total_project_delay > 0:
            explanation += f"This cascades to {len(affected_tasks)} dependent tasks, "
            explanation += f"delaying project completion by {total_project_delay} days."
        else:
            explanation += "This task has slack, so no impact on project completion."
        
        return DelayPropagation(
            initial_task_id=task_id,
            initial_delay_days=delay_days,
            affected_tasks=affected_tasks,
            propagation_path=propagation_path,
            total_project_delay_days=total_project_delay,
            confidence_score=confidence,
            explanation=explanation
        )
    
    def generate_delay_scenarios(
        self,
        critical_path: List[str],
        num_scenarios: int = 3
    ) -> List[DelayPropagation]:
        """
        Generate plausible delay scenarios for risk planning.
        
        Args:
            critical_path: Critical path task IDs
            num_scenarios: Number of scenarios to generate
        
        Returns:
            List of DelayPropagation scenarios
        """
        scenarios = []
        
        # Scenario 1: Minor delay on critical path task
        if len(critical_path) > 0:
            task = critical_path[0]
            scenario = self.simulate_task_delay(task, 5, critical_path)
            scenarios.append(scenario)
            logger.info(f"Scenario 1: 5-day delay on {task}")
        
        # Scenario 2: Major delay on bottleneck task
        if len(critical_path) > len(critical_path) // 2:
            task = critical_path[len(critical_path) // 2]
            scenario = self.simulate_task_delay(task, 15, critical_path)
            scenarios.append(scenario)
            logger.info(f"Scenario 2: 15-day delay on {task}")
        
        # Scenario 3: Weather/resource impact
        if len(critical_path) > 0:
            for task_id in critical_path:
                if self.analyzer.tasks[task_id].weather_dependency:
                    scenario = self.simulate_task_delay(task_id, 10, critical_path)
                    scenarios.append(scenario)
                    logger.info(f"Scenario 3: 10-day weather delay on {task_id}")
                    break
        
        return scenarios
    
    def calculate_schedule_resilience(
        self,
        critical_path_analysis: CriticalPathAnalysis,
        risk_factors: Dict[str, ScheduleRiskFactors]
    ) -> float:
        """
        Calculate how resilient the schedule is to delays (0-1).
        
        Higher resilience = more slack, lower risk factors
        """
        if not critical_path_analysis.critical_path:
            return 0.5
        
        # Factor 1: Slack distribution (more slack = more resilient)
        total_slack = sum(critical_path_analysis.slack_by_task.values())
        avg_slack = total_slack / len(critical_path_analysis.slack_by_task) if critical_path_analysis.slack_by_task else 0
        slack_factor = min(1.0, avg_slack / critical_path_analysis.project_duration_days)
        
        # Factor 2: Risk in critical path tasks
        critical_task_risks = []
        for task_id in critical_path_analysis.critical_tasks:
            if task_id in risk_factors:
                critical_task_risks.append(risk_factors[task_id].combined_delay_probability)
        
        avg_critical_risk = sum(critical_task_risks) / len(critical_task_risks) if critical_task_risks else 0.3
        risk_factor = 1.0 - avg_critical_risk
        
        # Factor 3: Number of bottlenecks
        bottleneck_factor = 1.0 - min(0.5, len(critical_path_analysis.bottleneck_tasks) * 0.1)
        
        # Combine factors
        resilience = (slack_factor * 0.4 + risk_factor * 0.4 + bottleneck_factor * 0.2)
        
        return max(0.0, min(1.0, resilience))
    
    def calculate_integration_risk_score(
        self,
        schedule_resilience: float,
        critical_path_length: int,
        avg_task_risk: float
    ) -> float:
        """
        Calculate how schedule delays impact Feature 1 project risk scoring.
        
        Returns score 0-1 to be integrated with Feature 1's AI engine.
        """
        # Poor schedule resilience increases overall project risk
        resilience_penalty = (1.0 - schedule_resilience) * 0.4
        
        # Longer critical paths = more delay risk
        # Normalize to projects with 50 tasks as baseline
        path_penalty = min(0.3, (critical_path_length / 50.0) * 0.3)
        
        # Average task risk
        risk_penalty = avg_task_risk * 0.3
        
        # Combine
        integration_score = resilience_penalty + path_penalty + risk_penalty
        
        return max(0.0, min(1.0, integration_score))
    
    def create_project_intelligence(
        self,
        project_id: str,
        project_name: str,
        critical_path_analysis: CriticalPathAnalysis,
        risk_factors: Dict[str, ScheduleRiskFactors],
        scenarios: List[DelayPropagation]
    ) -> ProjectScheduleIntelligence:
        """
        Assemble complete schedule intelligence report.
        
        Returns:
            ProjectScheduleIntelligence ready for Feature 1 integration
        """
        # Identify high-risk dependencies
        high_risk_deps = []
        for dep in self.analyzer.dependencies.values():
            # Risk = if predecessor is delayed, successor is heavily impacted
            if dep.successor_task_id in self.analyzer.adjacency_list:
                # More successors = higher risk
                num_affected = len(self.analyzer.adjacency_list[dep.successor_task_id])
                if num_affected > 0 and dep.lag_days == 0:  # No buffer = high risk
                    dep.criticality_score = min(1.0, num_affected * 0.2)
                    high_risk_deps.append(dep)
        
        high_risk_deps.sort(key=lambda d: d.criticality_score, reverse=True)
        
        # Calculate metrics
        resilience = self.calculate_schedule_resilience(
            critical_path_analysis,
            risk_factors
        )
        
        avg_task_risk = sum(rf.combined_delay_probability for rf in risk_factors.values()) / len(risk_factors) if risk_factors else 0.3
        
        integration_risk = self.calculate_integration_risk_score(
            resilience,
            len(critical_path_analysis.critical_path),
            avg_task_risk
        )
        
        # Recommended buffer
        max_expected_delay = max(
            (rf.expected_delay_days for rf in risk_factors.values()),
            default=5
        )
        recommended_buffer = int(max_expected_delay * 1.5)
        
        intelligence = ProjectScheduleIntelligence(
            project_id=project_id,
            project_name=project_name,
            total_tasks=len(self.analyzer.tasks),
            critical_path_analysis=critical_path_analysis,
            task_risk_factors=risk_factors,
            delay_scenarios=scenarios,
            schedule_resilience_score=resilience,
            high_risk_dependencies=high_risk_deps[:5],  # Top 5
            recommended_buffer_days=recommended_buffer,
            integration_risk_score=integration_risk
        )
        
        logger.info(f"Project {project_name}: resilience={resilience:.2f}, "
                   f"integration_risk={integration_risk:.2f}")
        
        return intelligence
