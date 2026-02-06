"""
Feature 11: Resource Allocation Optimizer
Core optimization logic for resource and subcontractor allocation
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional
from phase11_resource_types import (
    Worker, Crew, Subcontractor, TaskResourceRequirement, CurrentTaskAllocation,
    ReallocationRecommendation, AllocationScore, DownstreamEffect, AllocationComparison,
    ResourceAllocationContext, AllocationRequest, AllocationOutput,
    SkillLevel, ResourceType, AllocationStatus, ReallocationReason,
    MondayComMapping, ResourceAllocationMetrics
)

logger = logging.getLogger(__name__)


class AllocationOptimizer:
    """
    Optimizes resource and subcontractor allocation across tasks and projects
    """
    
    def __init__(self):
        """Initialize optimizer"""
        self.recommendation_history: Dict[str, List[ReallocationRecommendation]] = {}
        self.comparison_cache: Dict[str, AllocationComparison] = {}
    
    def optimize_allocation(self, context: ResourceAllocationContext, request: AllocationRequest) -> AllocationOutput:
        """
        Analyze current allocation and recommend reallocations
        
        Args:
            context: Resource allocation context with workers, tasks, allocations
            request: Optimization request with goals and constraints
            
        Returns:
            AllocationOutput with recommendations and comparisons
        """
        logger.info(f"Optimizing allocation for project {context.project_id} - goal: {request.optimization_goal}")
        
        # Score current allocations
        current_scores = self._score_current_allocations(context)
        
        # Generate reallocation recommendations
        recommendations = self._generate_recommendations(context, request, current_scores)
        
        # Filter by confidence threshold
        recommendations = [r for r in recommendations if r.confidence_level >= request.min_confidence_threshold]
        
        # Sort by impact (delay risk reduction primary, then cost)
        recommendations.sort(
            key=lambda r: (r.delay_risk_reduction, -r.cost_impact),
            reverse=True
        )
        
        # Limit to max_recommendations
        recommendations = recommendations[:request.max_recommendations]
        
        # Project optimized state
        optimized_scores = self._project_optimized_state(current_scores, recommendations)
        
        # Build comparison
        comparison = AllocationComparison(
            current_recommendations=recommendations,
            current_state=current_scores,
            optimized_state=optimized_scores,
            total_delay_risk_reduction=sum(r.delay_risk_reduction for r in recommendations),
            total_cost_impact=sum(r.cost_impact for r in recommendations),
            total_utilization_improvement=self._calculate_utilization_improvement(current_scores, optimized_scores),
            recommendations_count=len(recommendations),
            high_confidence_count=sum(1 for r in recommendations if r.confidence_level >= 0.80),
            implementation_effort_hours=sum(self._estimate_effort_hours(r) for r in recommendations),
            analysis_timestamp=datetime.now()
        )
        
        # Build output
        top_rec = recommendations[0] if recommendations else None
        overall_confidence = sum(r.confidence_level for r in recommendations) / max(len(recommendations), 1)
        
        output = AllocationOutput(
            project_id=context.project_id,
            recommendations=recommendations,
            comparison=comparison,
            optimization_goal=request.optimization_goal,
            total_delay_risk_reduction_potential=comparison.total_delay_risk_reduction,
            total_cost_reduction_potential=-comparison.total_cost_impact if comparison.total_cost_impact < 0 else 0,
            total_utilization_improvement=comparison.total_utilization_improvement,
            top_recommendation=top_rec,
            confidence_level=overall_confidence,
            generated_at=datetime.now(),
        )
        
        # Cache
        if context.project_id not in self.recommendation_history:
            self.recommendation_history[context.project_id] = []
        self.recommendation_history[context.project_id].extend(recommendations)
        self.comparison_cache[context.project_id] = comparison
        
        return output
    
    def _score_current_allocations(self, context: ResourceAllocationContext) -> Dict[str, AllocationScore]:
        """
        Score each current task allocation on multiple dimensions
        
        Returns:
            Dictionary of allocation_id -> AllocationScore
        """
        scores: Dict[str, AllocationScore] = {}
        
        for allocation in context.current_allocations:
            allocation_id = f"{allocation.task_id}_{allocation.project_id}"
            
            # Find the task requirement
            task_req = None
            for task in context.tasks:
                if task.task_id == allocation.task_id:
                    task_req = task
                    break
            
            if not task_req:
                continue
            
            # Score components
            skill_match = self._score_skill_match(allocation, context, task_req)
            availability = self._score_availability_match(allocation, context)
            cost_efficiency = self._score_cost_efficiency(allocation, context)
            reliability = context.workforce_reliability_scores.get(allocation.task_id, 0.70)
            utilization = self._score_utilization(allocation, context)
            dependency_impact = self._score_dependency_impact(allocation, context)
            
            # Weight and combine
            weights = {
                'skill_match': 0.25,
                'availability': 0.15,
                'cost_efficiency': 0.20,
                'reliability': 0.20,
                'utilization': 0.10,
                'dependency_impact': 0.10,
            }
            
            overall_score = (
                skill_match * weights['skill_match'] +
                availability * weights['availability'] +
                cost_efficiency * weights['cost_efficiency'] +
                reliability * weights['reliability'] +
                utilization * weights['utilization'] +
                dependency_impact * weights['dependency_impact']
            )
            
            explanation = (
                f"Skill match: {skill_match:.0%} | Availability: {availability:.0%} | "
                f"Cost efficiency: {cost_efficiency:.0%} | Reliability: {reliability:.0%} | "
                f"Utilization: {utilization:.0%}"
            )
            
            score = AllocationScore(
                allocation_id=allocation_id,
                skill_match_score=skill_match,
                availability_match_score=availability,
                cost_efficiency_score=cost_efficiency,
                reliability_score=reliability,
                utilization_score=utilization,
                dependency_impact_score=dependency_impact,
                overall_allocation_score=overall_score,
                explanation=explanation
            )
            
            scores[allocation_id] = score
        
        return scores
    
    def _score_skill_match(self, allocation: CurrentTaskAllocation, context: ResourceAllocationContext,
                          task_req: TaskResourceRequirement) -> float:
        """Score how well allocated resources match required skills"""
        if not allocation.allocated_workers and not allocation.allocated_crew_ids and not allocation.allocated_subcontractor_ids:
            return 0.0
        
        matches = 0
        total = task_req.workers_needed
        
        # Check workers
        for worker_id in allocation.allocated_workers.keys():
            worker = next((w for w in context.all_workers if w.worker_id == worker_id), None)
            if worker:
                worker_match = self._worker_skill_match(worker, task_req)
                matches += worker_match
        
        # Check crews
        for crew_id in allocation.allocated_crew_ids:
            crew = next((c for c in context.all_crews if c.crew_id == crew_id), None)
            if crew:
                crew_match = sum(
                    self._worker_skill_match(
                        next((w for w in context.all_workers if w.worker_id == wid), None),
                        task_req
                    )
                    for wid in crew.member_worker_ids
                ) / max(len(crew.member_worker_ids), 1)
                matches += crew_match * (len(crew.member_worker_ids) / total)
        
        # Subcontractors get full mark if they provide the service
        for sub_id in allocation.allocated_subcontractor_ids:
            sub = next((s for s in context.all_subcontractors if s.subcontractor_id == sub_id), None)
            if sub and any(service in sub.services for service in [task_req.required_role]):
                matches += 1
        
        return min(matches / max(total, 1), 1.0)
    
    def _worker_skill_match(self, worker: Optional[Worker], task_req: TaskResourceRequirement) -> float:
        """Score individual worker against task requirements"""
        if not worker:
            return 0.0
        
        skill_match = 0.0
        for required_skill in task_req.required_skills:
            for worker_skill in worker.skills:
                if worker_skill.skill_name == required_skill.skill_name:
                    # Check proficiency level match
                    req_levels = {SkillLevel.JUNIOR: 1, SkillLevel.INTERMEDIATE: 2, SkillLevel.SENIOR: 3, SkillLevel.MASTER: 4}
                    worker_level = req_levels.get(worker_skill.proficiency_level, 0)
                    req_level = req_levels.get(required_skill.proficiency_level, 0)
                    
                    if worker_level >= req_level:
                        skill_match += 1.0
                    elif worker_level == req_level - 1:
                        skill_match += 0.7
                    else:
                        skill_match += 0.3
        
        return min(skill_match / max(len(task_req.required_skills), 1), 1.0)
    
    def _score_availability_match(self, allocation: CurrentTaskAllocation, context: ResourceAllocationContext) -> float:
        """Score how available the allocated resources are"""
        if not allocation.allocated_workers and not allocation.allocated_crew_ids:
            return 0.8  # Subcontractors usually available
        
        available = 0
        total = len(allocation.allocated_workers) + len(allocation.allocated_crew_ids)
        
        for worker_id in allocation.allocated_workers.keys():
            worker = next((w for w in context.all_workers if w.worker_id == worker_id), None)
            if worker and self._is_available(worker.availability, allocation.allocation_start, allocation.allocation_end):
                available += 1
        
        for crew_id in allocation.allocated_crew_ids:
            crew = next((c for c in context.all_crews if c.crew_id == crew_id), None)
            if crew:
                lead = next((w for w in context.all_workers if w.worker_id == crew.lead_worker_id), None)
                if lead and self._is_available(lead.availability, allocation.allocation_start, allocation.allocation_end):
                    available += 1
        
        return min(available / max(total, 1), 1.0) if total > 0 else 0.8
    
    def _is_available(self, availability, start_date: date, end_date: date) -> bool:
        """Check if resource is available during date range"""
        return (
            availability.available_from <= start_date and
            availability.available_to >= end_date
        )
    
    def _score_cost_efficiency(self, allocation: CurrentTaskAllocation, context: ResourceAllocationContext) -> float:
        """Score cost efficiency of current allocation"""
        task_hours = allocation.estimated_completion_hours
        if task_hours == 0:
            return 0.5
        
        current_cost = allocation.cost_from_allocation
        
        # Calculate ideal minimum cost
        min_cost_estimate = task_hours * 25  # $25/hour minimum
        
        # Score: lower cost is better (capped at 1.0)
        efficiency = 1.0 - min((current_cost - min_cost_estimate) / max(current_cost, 1), 0.5)
        return max(efficiency, 0.0)
    
    def _score_utilization(self, allocation: CurrentTaskAllocation, context: ResourceAllocationContext) -> float:
        """Score resource utilization - is resource used efficiently"""
        if not allocation.allocated_workers:
            return 0.7
        
        total_capacity = 0
        total_allocated = 0
        
        for worker_id, hours in allocation.allocated_workers.items():
            worker = next((w for w in context.all_workers if w.worker_id == worker_id), None)
            if worker:
                # Weekly capacity
                capacity = worker.availability.hours_per_week
                total_capacity += capacity * (
                    (allocation.allocation_end - allocation.allocation_start).days / 7
                )
                total_allocated += hours
        
        if total_capacity == 0:
            return 0.5
        
        utilization = total_allocated / total_capacity
        # Optimal is 80-90%, penalize over/under
        if 0.80 <= utilization <= 0.90:
            return 1.0
        elif 0.60 <= utilization <= 1.0:
            return 0.85 + (utilization * 0.15)
        else:
            return max(utilization * 0.5, 0.2)
    
    def _score_dependency_impact(self, allocation: CurrentTaskAllocation, context: ResourceAllocationContext) -> float:
        """Score if this allocation helps or hurts task dependencies"""
        task_delay_risk = context.task_delay_risks.get(allocation.task_id, 0.5)
        
        # If task is on critical path and has high delay risk, good allocation is crucial
        if task_delay_risk > 0.70:
            return 1.0 if allocation.delay_risk_from_allocation < 0.50 else 0.5
        
        return 0.7
    
    def _generate_recommendations(self, context: ResourceAllocationContext, request: AllocationRequest,
                                 current_scores: Dict[str, AllocationScore]) -> List[ReallocationRecommendation]:
        """Generate reallocation recommendations"""
        recommendations: List[ReallocationRecommendation] = []
        
        # Identify under-utilized resources
        under_utilized = self._find_under_utilized_resources(context, current_scores)
        
        # Identify over-allocated tasks
        over_allocated = self._find_over_allocated_tasks(context, current_scores)
        
        # Generate recommendations to move from over-allocated to under-utilized
        for task_from, score_from in over_allocated:
            allocation_from = next((a for a in context.current_allocations if a.task_id == task_from), None)
            if not allocation_from or task_from in context.no_reallocation_task_ids:
                continue
            
            for task_to, score_to in under_utilized:
                if task_to in context.no_reallocation_task_ids:
                    continue
                
                # Generate reallocation recommendation
                rec = self._create_reallocation_recommendation(
                    context, allocation_from, task_to, current_scores, request
                )
                
                if rec:
                    recommendations.append(rec)
        
        return recommendations
    
    def _find_under_utilized_resources(self, context: ResourceAllocationContext,
                                      scores: Dict[str, AllocationScore]) -> List[Tuple[str, AllocationScore]]:
        """Find tasks that are under-allocated or have low scores"""
        under_utilized = []
        
        for allocation in context.current_allocations:
            allocation_id = f"{allocation.task_id}_{allocation.project_id}"
            score = scores.get(allocation_id)
            
            if score and score.overall_allocation_score < 0.65:
                under_utilized.append((allocation.task_id, score))
        
        return sorted(under_utilized, key=lambda x: x[1].overall_allocation_score)
    
    def _find_over_allocated_tasks(self, context: ResourceAllocationContext,
                                   scores: Dict[str, AllocationScore]) -> List[Tuple[str, AllocationScore]]:
        """Find tasks with over-allocation"""
        over_allocated = []
        
        for allocation in context.current_allocations:
            allocation_id = f"{allocation.task_id}_{allocation.project_id}"
            score = scores.get(allocation_id)
            
            # Check if resources are unnecessarily over-allocated
            if allocation.completion_percent < 0.30:  # Early in task
                estimated_remaining = allocation.estimated_completion_hours - allocation.actual_completed_hours
                if estimated_remaining < allocation.estimated_completion_hours * 0.60:
                    over_allocated.append((allocation.task_id, score))
        
        return sorted(over_allocated, key=lambda x: -x[1].utilization_score)
    
    def _create_reallocation_recommendation(self, context: ResourceAllocationContext,
                                          allocation_from: CurrentTaskAllocation,
                                          task_to_id: str,
                                          current_scores: Dict[str, AllocationScore],
                                          request: AllocationRequest) -> Optional[ReallocationRecommendation]:
        """Create reallocation recommendation"""
        allocation_to = next((a for a in context.current_allocations if a.task_id == task_to_id), None)
        if not allocation_to:
            return None
        
        # Calculate potential impact
        delay_reduction = context.task_delay_risks.get(task_to_id, 0.5) * 0.15  # 15% relief
        cost_impact = -5000  # Assume cost savings from better allocation
        
        from_score_id = f"{allocation_from.task_id}_{allocation_from.project_id}"
        to_score_id = f"{allocation_to.task_id}_{allocation_to.project_id}"
        
        current_score = current_scores.get(from_score_id, AllocationScore(
            from_score_id, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, "unknown"
        ))
        
        projection_score = min(current_score.overall_allocation_score + 0.15, 1.0)
        confidence = 0.75 if delay_reduction > 0.10 else 0.60
        
        # Determine which resource to move
        primary_worker = list(allocation_from.allocated_workers.keys())[0] if allocation_from.allocated_workers else None
        resource_type = ResourceType.LABOR if primary_worker else ResourceType.CREW
        resource_id = primary_worker if primary_worker else allocation_from.allocated_crew_ids[0] if allocation_from.allocated_crew_ids else ""
        
        if not resource_id:
            return None
        
        resource_name = next((w.name for w in context.all_workers if w.worker_id == resource_id), resource_id)
        
        rec = ReallocationRecommendation(
            recommendation_id=f"REALLOC_{len(self.recommendation_history)}",
            from_task_id=allocation_from.task_id,
            to_task_id=task_to_id,
            project_id=context.project_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            reason=ReallocationReason.REDUCE_DELAY_RISK,
            hours_to_reallocate=int(allocation_from.estimated_completion_hours * 0.20),
            current_allocation_score=current_score.overall_allocation_score,
            projected_allocation_score=projection_score,
            delay_risk_reduction=delay_reduction,
            cost_impact=cost_impact,
            confidence_level=confidence,
            implementation_difficulty="easy",
            explanation=(
                f"Moving {resource_name} from {allocation_from.task_id} to {task_to_id} "
                f"reduces delay risk by {delay_reduction:.0%} with cost savings of ${-cost_impact:,.0f}"
            ),
            generated_at=datetime.now(),
        )
        
        return rec
    
    def _project_optimized_state(self, current_scores: Dict[str, AllocationScore],
                                recommendations: List[ReallocationRecommendation]) -> Dict[str, AllocationScore]:
        """Project allocation scores after applying recommendations"""
        optimized = current_scores.copy()
        
        # Apply improvements from recommendations
        for rec in recommendations:
            allocation_id_to = f"{rec.to_task_id}_{rec.project_id}"
            if allocation_id_to in optimized:
                # Improve to-task score
                current = optimized[allocation_id_to]
                improvement = rec.delay_risk_reduction * 0.10  # Convert to score improvement
                new_score = min(current.overall_allocation_score + improvement, 1.0)
                optimized[allocation_id_to] = AllocationScore(
                    allocation_id_to,
                    current.skill_match_score,
                    current.availability_match_score,
                    current.cost_efficiency_score,
                    current.reliability_score,
                    current.utilization_score,
                    current.dependency_impact_score,
                    new_score,
                    current.explanation + " (optimized)"
                )
        
        return optimized
    
    def _calculate_utilization_improvement(self, current: Dict[str, AllocationScore],
                                          optimized: Dict[str, AllocationScore]) -> float:
        """Calculate overall utilization improvement"""
        if not current:
            return 0.0
        
        current_avg = sum(s.utilization_score for s in current.values()) / len(current)
        optimized_avg = sum(s.utilization_score for s in optimized.values()) / len(optimized)
        
        return optimized_avg - current_avg
    
    def _estimate_effort_hours(self, rec: ReallocationRecommendation) -> int:
        """Estimate hours needed to implement reallocation"""
        difficulty_map = {
            "easy": 2,
            "moderate": 8,
            "hard": 24,
        }
        return difficulty_map.get(rec.implementation_difficulty, 8)
