"""
Feature 11: Resource Allocation Integration
Integration with Features 3, 4, 9, and 10
"""
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
from phase11_resource_types import (
    ResourceAllocationContext, AllocationRequest, AllocationOutput,
    AllocationOptimizer, Worker, Crew, Subcontractor, TaskResourceRequirement,
    CurrentTaskAllocation, ResourceType, SkillLevel, Skill, ResourceAvailability
)
from phase11_allocation_optimizer import AllocationOptimizer

logger = logging.getLogger(__name__)


class ResourceAllocationIntegration:
    """
    Integration wrapper for Feature 11 optimization
    Bridges with Features 3, 4, 9, and 10
    """
    
    def __init__(self, project_id: str):
        """Initialize integration"""
        self.project_id = project_id
        self.optimizer = AllocationOptimizer()
        self.analysis_cache: Dict[str, AllocationOutput] = {}
        self.context_history: List[ResourceAllocationContext] = []
    
    def analyze_allocation(self, 
                          workers: List[Worker],
                          crews: List[Crew],
                          subcontractors: List[Subcontractor],
                          tasks: List[TaskResourceRequirement],
                          current_allocations: List[CurrentTaskAllocation],
                          request: AllocationRequest,
                          feature_3_data: Optional[Dict] = None,
                          feature_4_data: Optional[Dict] = None) -> AllocationOutput:
        """
        Analyze resource allocation and generate recommendations
        
        Args:
            workers: All available workers
            crews: All crews
            subcontractors: All subcontractors
            tasks: All tasks needing resources
            current_allocations: Current allocations
            request: Optimization request
            feature_3_data: Workforce reliability from Feature 3
            feature_4_data: Subcontractor performance from Feature 4
            
        Returns:
            AllocationOutput with recommendations
        """
        logger.info(f"Analyzing allocation for project {self.project_id}")
        
        # Build context
        context = self._build_context(
            workers, crews, subcontractors, tasks, current_allocations,
            feature_3_data, feature_4_data
        )
        
        # Run optimization
        output = self.optimizer.optimize_allocation(context, request)
        
        # Enrich with Feature 9/10 integration
        output = self._enrich_with_features_9_10(output, context)
        
        # Cache and history
        self.analysis_cache[self.project_id] = output
        self.context_history.append(context)
        
        return output
    
    def _build_context(self,
                      workers: List[Worker],
                      crews: List[Crew],
                      subcontractors: List[Subcontractor],
                      tasks: List[TaskResourceRequirement],
                      current_allocations: List[CurrentTaskAllocation],
                      feature_3_data: Optional[Dict],
                      feature_4_data: Optional[Dict]) -> ResourceAllocationContext:
        """Build allocation context with Feature data"""
        
        # Feature 3: Extract workforce reliability scores
        workforce_reliability_scores: Dict[str, float] = {}
        if feature_3_data:
            for task_id, reliability in feature_3_data.items():
                workforce_reliability_scores[task_id] = reliability
        
        # Feature 4: Extract subcontractor performance scores
        subcontractor_performance_scores: Dict[str, float] = {}
        if feature_4_data:
            for sub_id, score in feature_4_data.items():
                subcontractor_performance_scores[sub_id] = score
        
        # Task delay risks (from Feature 1 via Feature 9)
        task_delay_risks: Dict[str, float] = {}
        for task in tasks:
            task_delay_risks[task.task_id] = 0.5  # Default, override with actual
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=workers,
            all_crews=crews,
            all_subcontractors=subcontractors,
            tasks=tasks,
            current_allocations=current_allocations,
            workforce_reliability_scores=workforce_reliability_scores,
            subcontractor_performance_scores=subcontractor_performance_scores,
            task_delay_risks=task_delay_risks,
            historical_productivity={},
            season="summer",
            project_phase="execution",
        )
        
        return context
    
    def _enrich_with_features_9_10(self, output: AllocationOutput, context: ResourceAllocationContext) -> AllocationOutput:
        """Enrich output with Feature 9 and 10 integration"""
        
        # Feature 9 Integration: Risk synthesis impact
        output.feature_9_inputs = {
            'resource_allocation_risk_reduction': output.total_delay_risk_reduction_potential,
            'workforce_reliability_improvement': self._calculate_workforce_improvement(output),
            'subcontractor_risk_mitigation': self._calculate_subcontractor_improvement(output),
            'critical_path_exposure_reduction': self._calculate_critical_path_reduction(output, context),
        }
        
        # Feature 10 Integration: What-if scenarios
        output.feature_10_if_statements = [
            f"If we reallocate {rec.resource_name} to {rec.to_task_id}, "
            f"delay risk reduces by {rec.delay_risk_reduction:.0%} "
            f"with cost impact of ${rec.cost_impact:,.0f}"
            for rec in output.recommendations[:5]
        ]
        
        return output
    
    def _calculate_workforce_improvement(self, output: AllocationOutput) -> float:
        """Calculate workforce reliability improvement from allocation"""
        avg_confidence = sum(r.confidence_level for r in output.recommendations) / max(len(output.recommendations), 1)
        # Confidence translates to reliability improvement
        return avg_confidence * 0.15  # Max 15% improvement
    
    def _calculate_subcontractor_improvement(self, output: AllocationOutput) -> float:
        """Calculate subcontractor performance improvement from better allocation"""
        subcontractor_recs = [r for r in output.recommendations if r.resource_type == ResourceType.SUBCONTRACTOR]
        if not subcontractor_recs:
            return 0.0
        
        avg_cost_impact = sum(r.cost_impact for r in subcontractor_recs) / len(subcontractor_recs)
        # Cost savings suggests better subcontractor utilization
        return max(min(-avg_cost_impact / 100000, 0.10), 0.0)
    
    def _calculate_critical_path_reduction(self, output: AllocationOutput, context: ResourceAllocationContext) -> float:
        """Calculate critical path exposure reduction"""
        critical_recs = [r for r in output.recommendations if r.delay_risk_reduction > 0.10]
        reduction = sum(r.delay_risk_reduction for r in critical_recs) / max(len(context.tasks), 1)
        return min(reduction, 0.25)
    
    def get_feature_3_input(self) -> Dict[str, Any]:
        """
        Format output for Feature 3 (Workforce Reliability)
        Return recommendations for workforce management
        """
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'feature11_workforce_changes': [
                {
                    'worker_id': rec.resource_id if rec.resource_type == ResourceType.LABOR else None,
                    'current_utilization': rec.current_allocation_score,
                    'recommended_utilization': rec.projected_allocation_score,
                    'hours_to_reallocate': rec.hours_to_reallocate,
                    'reason': rec.reason.value,
                }
                for rec in output.recommendations if rec.resource_type == ResourceType.LABOR
            ],
            'feature11_total_workforce_improvement': output.total_utilization_improvement,
        }
    
    def get_feature_4_input(self) -> Dict[str, Any]:
        """
        Format output for Feature 4 (Subcontractor Performance)
        Return recommendations for subcontractor management
        """
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'feature11_subcontractor_changes': [
                {
                    'subcontractor_id': rec.resource_id,
                    'subcontractor_name': rec.resource_name,
                    'from_task': rec.from_task_id,
                    'to_task': rec.to_task_id,
                    'expected_cost_impact': rec.cost_impact,
                    'confidence': rec.confidence_level,
                }
                for rec in output.recommendations if rec.resource_type == ResourceType.SUBCONTRACTOR
            ],
            'feature11_subcontractor_optimization_potential': output.total_cost_reduction_potential,
        }
    
    def get_feature_9_input(self) -> Dict[str, Any]:
        """
        Format output for Feature 9 (Multi-Factor Risk Synthesis)
        """
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'feature11_delay_risk_reduction': output.total_delay_risk_reduction_potential,
            'feature11_cost_optimization': output.total_cost_reduction_potential,
            'feature11_resource_allocation_confidence': output.confidence_level,
            'feature11_critical_recommendations': len(output.recommendations),
            'feature11_analysis_timestamp': output.generated_at.isoformat(),
        }
    
    def get_feature_10_input(self) -> Dict[str, Any]:
        """
        Format output for Feature 10 (AI Recommendations & What-If)
        Provide allocation scenarios for what-if analysis
        """
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'feature11_allocation_recommendations': [
                {
                    'title': f"Reallocate {rec.resource_name}",
                    'description': rec.explanation,
                    'type': 'workforce_optimization' if rec.resource_type == ResourceType.LABOR else 'subcontractor_optimization',
                    'impact_delay_risk': rec.delay_risk_reduction,
                    'impact_cost': rec.cost_impact,
                    'confidence': rec.confidence_level,
                }
                for rec in output.recommendations
            ],
            'feature11_allocation_scenarios': self._build_allocation_scenarios(output),
        }
    
    def _build_allocation_scenarios(self, output: AllocationOutput) -> List[Dict[str, Any]]:
        """Build allocation scenarios for Feature 10 what-if analysis"""
        scenarios = [
            {
                'name': 'Current Allocation',
                'description': 'Status quo - no changes',
                'delay_risk_projection': 0.0,
                'cost_projection': 0.0,
            },
            {
                'name': 'Conservative Reallocation',
                'description': 'Apply only high-confidence recommendations',
                'delay_risk_projection': output.comparison.total_delay_risk_reduction * 0.6,
                'cost_projection': output.comparison.total_cost_impact * 0.6,
            },
            {
                'name': 'Aggressive Reallocation',
                'description': 'Apply all recommendations',
                'delay_risk_projection': output.comparison.total_delay_risk_reduction,
                'cost_projection': output.comparison.total_cost_impact,
            },
        ]
        return scenarios
    
    def get_monday_com_data(self) -> Dict[str, Any]:
        """Format output for monday.com integration"""
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'monday_fields': {
                'Feature11_Recommendations_Count': len(output.recommendations),
                'Feature11_Top_Action': output.top_recommendation.explanation if output.top_recommendation else "No recommendations",
                'Feature11_Delay_Risk_Reduction': f"{output.total_delay_risk_reduction_potential:.0%}",
                'Feature11_Cost_Optimization': f"${output.total_cost_reduction_potential:,.0f}",
                'Feature11_Confidence_Level': f"{output.confidence_level:.0%}",
                'Feature11_Implementation_Hours': output.comparison.implementation_effort_hours,
                'Feature11_High_Confidence_Count': output.comparison.high_confidence_count,
            },
            'timestamp': datetime.now().isoformat(),
        }
    
    def apply_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Apply a specific recommendation"""
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {'status': 'error', 'message': 'No analysis available'}
        
        rec = next((r for r in output.recommendations if r.recommendation_id == recommendation_id), None)
        if not rec:
            return {'status': 'error', 'message': 'Recommendation not found'}
        
        return {
            'status': 'applied',
            'recommendation_id': recommendation_id,
            'from_task': rec.from_task_id,
            'to_task': rec.to_task_id,
            'resource': rec.resource_name,
            'expected_delay_reduction': rec.delay_risk_reduction,
            'expected_cost_impact': rec.cost_impact,
            'confidence': rec.confidence_level,
            'applied_at': datetime.now().isoformat(),
        }
    
    def compare_allocation_scenarios(self) -> Dict[str, Any]:
        """Compare different allocation scenarios"""
        output = self.analysis_cache.get(self.project_id)
        if not output:
            return {}
        
        return {
            'current_state': {
                'avg_utilization': sum(s.utilization_score for s in output.comparison.current_state.values()) / max(len(output.comparison.current_state), 1),
                'avg_score': sum(s.overall_allocation_score for s in output.comparison.current_state.values()) / max(len(output.comparison.current_state), 1),
            },
            'optimized_state': {
                'avg_utilization': sum(s.utilization_score for s in output.comparison.optimized_state.values()) / max(len(output.comparison.optimized_state), 1),
                'avg_score': sum(s.overall_allocation_score for s in output.comparison.optimized_state.values()) / max(len(output.comparison.optimized_state), 1),
            },
            'potential_improvement': {
                'delay_risk_reduction': output.comparison.total_delay_risk_reduction,
                'cost_savings': -output.comparison.total_cost_impact if output.comparison.total_cost_impact < 0 else 0,
                'utilization_improvement': output.comparison.total_utilization_improvement,
            },
        }
    
    def reset_project(self):
        """Clear caches for testing"""
        if self.project_id in self.analysis_cache:
            del self.analysis_cache[self.project_id]
        self.context_history.clear()


def create_resource_allocation_integration(project_id: str) -> ResourceAllocationIntegration:
    """Factory function to create integration"""
    return ResourceAllocationIntegration(project_id)
