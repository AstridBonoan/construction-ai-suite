"""
Feature 10: Integration Layer
Integration with Features 1-9 for recommendations and scenario analysis
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from phase10_recommendation_types import (
    RecommendationContext,
    RecommendationRequest,
    ScenarioRequest,
    RecommendationOutput,
    Recommendation,
    Scenario,
)
from phase10_recommendation_engine import RecommendationEngine
from phase10_scenario_simulator import ScenarioSimulator

logger = logging.getLogger(__name__)


def create_feature10_integration(project_id: str) -> 'Feature10Integration':
    """Factory function to create Feature 10 integration"""
    return Feature10Integration(project_id)


class Feature10Integration:
    """Integration wrapper for Feature 10"""
    
    def __init__(self, project_id: str):
        """Initialize Feature 10 integration"""
        self.project_id = project_id
        self.recommendation_engine = RecommendationEngine()
        self.scenario_simulator = ScenarioSimulator()
        
        # Caches
        self.analysis_cache: Dict[str, RecommendationOutput] = {}
        self.context_history: List[RecommendationContext] = []
    
    def analyze_project(
        self,
        context: RecommendationContext,
        recommendation_request: Optional[RecommendationRequest] = None,
        scenario_request: Optional[ScenarioRequest] = None,
    ) -> RecommendationOutput:
        """
        Analyze project and generate recommendations + scenarios
        
        Args:
            context: Current project state from Features 1-9
            recommendation_request: Settings for recommendation generation
            scenario_request: Settings for scenario simulation
            
        Returns:
            Combined output with recommendations and scenarios
        """
        
        # Store context history
        self.context_history.append(context)
        
        # Set defaults
        if recommendation_request is None:
            recommendation_request = RecommendationRequest(project_id=self.project_id)
        
        if scenario_request is None:
            scenario_request = ScenarioRequest(project_id=self.project_id)
        
        # Generate recommendations
        recommendations = self.recommendation_engine.generate_recommendations(
            context, recommendation_request
        )
        
        # Simulate scenarios
        comparison = self.scenario_simulator.simulate_scenarios(
            context, scenario_request
        )
        
        # Build output
        output = RecommendationOutput(
            project_id=self.project_id,
            task_id=context.task_id,
            recommendations=recommendations,
            scenarios=comparison.scenarios,
            comparison=comparison,
            total_cost_reduction_potential=sum(
                max(0, -r.impact.cost_impact.total_cost_delta)
                for r in recommendations
            ),
            total_risk_reduction_potential=sum(
                max(0, -r.impact.risk_impact.overall_risk_delta)
                for r in recommendations
            ) / max(1, len(recommendations)),
            total_schedule_improvement=sum(
                max(0, -r.impact.schedule_impact.duration_delta_days)
                for r in recommendations
            ),
            top_recommendation=recommendations[0] if recommendations else None,
            recommended_scenario=next(
                (s for s in comparison.scenarios if s.recommended),
                comparison.scenarios[comparison.scenario_rankings[comparison.best_overall][0] - 1]
                if comparison.scenario_rankings else None
            ),
            analysis_basis=f"Analysis of {len(recommendations)} recommendations and {len(comparison.scenarios)} scenarios",
            confidence_level=min(
                sum(r.confidence_level for r in recommendations) / max(1, len(recommendations)),
                0.9  # Cap at 90%
            ),
            monday_com_mappings=self._build_monday_mappings(recommendations),
        )
        
        # Cache
        cache_key = f"{self.project_id}_{context.task_id}"
        self.analysis_cache[cache_key] = output
        
        return output
    
    def get_recommendation_for_task(
        self,
        task_id: str,
        limit: int = 5
    ) -> List[Recommendation]:
        """Get recommendations for specific task"""
        return self.recommendation_engine.get_top_recommendations(
            self.project_id, limit
        )
    
    def get_feature1_input(self) -> Dict[str, any]:
        """
        Prepare Feature 10 output for Feature 1 (Core Risk Engine) consumption
        
        Returns Feature 1-compatible format with risk adjustments
        """
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis:
            return {}
        
        # Build Feature 1 input
        feature1_input = {
            'feature10_all_recommendations': [
                {
                    'title': r.title,
                    'type': r.recommendation_type.value,
                    'severity': r.severity.value,
                    'risk_delta': r.impact.risk_impact.overall_risk_delta,
                    'cost_delta': r.impact.cost_impact.total_cost_delta,
                    'schedule_delta': r.impact.schedule_impact.duration_delta_days,
                    'confidence': r.confidence_level,
                }
                for r in latest_analysis.recommendations
            ],
            'feature10_top_recommendation': (
                {
                    'title': latest_analysis.top_recommendation.title,
                    'type': latest_analysis.top_recommendation.recommendation_type.value,
                    'impact': latest_analysis.top_recommendation.impact.risk_impact.overall_risk_delta,
                }
                if latest_analysis.top_recommendation else None
            ),
            'feature10_recommended_scenario': (
                {
                    'name': latest_analysis.recommended_scenario.name,
                    'risk_projection': latest_analysis.recommended_scenario.estimated_risk_score,
                    'cost_projection': latest_analysis.recommended_scenario.estimated_total_cost,
                    'schedule_projection': latest_analysis.recommended_scenario.estimated_completion_days,
                }
                if latest_analysis.recommended_scenario else None
            ),
            'feature10_total_risk_reduction_potential': latest_analysis.total_risk_reduction_potential,
            'feature10_total_cost_reduction_potential': latest_analysis.total_cost_reduction_potential,
            'feature10_total_schedule_improvement': latest_analysis.total_schedule_improvement,
            'feature10_analysis_timestamp': latest_analysis.generated_at,
        }
        
        return feature1_input
    
    def get_monday_com_data(self) -> Dict[str, any]:
        """
        Prepare Feature 10 output for monday.com integration
        
        Returns monday.com-compatible column mappings
        """
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis:
            return {}
        
        return {
            'monday_fields': {
                'Recommendations': f"{len(latest_analysis.recommendations)} recommendations" if latest_analysis.recommendations else "No recommendations",
                'Top Action': latest_analysis.top_recommendation.title if latest_analysis.top_recommendation else "N/A",
                'Impact (Risk)': f"Risk {latest_analysis.top_recommendation.impact.risk_impact.overall_risk_delta*100:+.0f}%" if latest_analysis.top_recommendation else "N/A",
                'Impact (Cost)': f"Cost ${latest_analysis.top_recommendation.impact.cost_impact.total_cost_delta:+,.0f}" if latest_analysis.top_recommendation else "N/A",
                'Effort': latest_analysis.top_recommendation.impact.implementation_difficulty if latest_analysis.top_recommendation else "N/A",
                'Recommended Scenario': latest_analysis.recommended_scenario.name if latest_analysis.recommended_scenario else "No scenario",
                'Scenario Risk Projection': f"{latest_analysis.recommended_scenario.estimated_risk_score*100:.0f}%" if latest_analysis.recommended_scenario else "N/A",
                'Scenario Cost': f"${latest_analysis.recommended_scenario.estimated_total_cost:,.0f}" if latest_analysis.recommended_scenario else "N/A",
                'Scenario Schedule': f"{latest_analysis.recommended_scenario.estimated_completion_days} days" if latest_analysis.recommended_scenario else "N/A",
            }
        }
    
    def compare_scenarios(self, scenario_ids: List[str]):
        """Compare specific scenarios"""
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis or not latest_analysis.comparison:
            return {}
        
        filtered_scenarios = [
            s for s in latest_analysis.comparison.scenarios
            if s.scenario_id in scenario_ids
        ]
        
        return {
            'scenarios': filtered_scenarios,
            'comparison': {
                'ranked': latest_analysis.comparison.scenario_rankings
            }
        }
    
    def apply_recommendation(
        self,
        recommendation_id: str
    ) -> Dict[str, any]:
        """
        Apply a recommendation (update project context)
        
        This would typically trigger Feature 1-9 updates
        """
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis:
            return {'status': 'error', 'message': 'No analysis available'}
        
        # Find recommendation
        rec = next(
            (r for r in latest_analysis.recommendations if r.recommendation_id == recommendation_id),
            None
        )
        
        if not rec:
            return {'status': 'error', 'message': 'Recommendation not found'}
        
        return {
            'status': 'applied',
            'recommendation_id': recommendation_id,
            'title': rec.title,
            'estimated_impacts': {
                'risk_change': rec.impact.risk_impact.overall_risk_delta,
                'cost_change': rec.impact.cost_impact.total_cost_delta,
                'schedule_change': rec.impact.schedule_impact.duration_delta_days,
            },
            'next_steps': rec.description,
            'timestamp': datetime.now().isoformat(),
        }
    
    def apply_scenario(self, scenario_id: str) -> Dict[str, any]:
        """
        Apply a scenario (potentially update project baseline)
        """
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis or not latest_analysis.comparison:
            return {'status': 'error', 'message': 'No scenario analysis available'}
        
        # Find scenario
        scenario = next(
            (s for s in latest_analysis.comparison.scenarios if s.scenario_id == scenario_id),
            None
        )
        
        if not scenario:
            return {'status': 'error', 'message': 'Scenario not found'}
        
        return {
            'status': 'applied',
            'scenario_id': scenario_id,
            'name': scenario.name,
            'projections': {
                'risk_score': scenario.estimated_risk_score,
                'total_cost': scenario.estimated_total_cost,
                'completion_days': scenario.estimated_completion_days,
            },
            'adjustments': [
                {
                    'workforce_delta': adj.workforce_count_delta,
                    'cost_multiplier': adj.cost_multiplier,
                    'schedule_override': adj.duration_override_days,
                }
                for adj in scenario.adjustments
            ],
            'timestamp': datetime.now().isoformat(),
        }
    
    def get_context_history(self, limit: int = 10) -> List[RecommendationContext]:
        """Get historical contexts for trend analysis"""
        return self.context_history[-limit:]
    
    def reset_project(self):
        """Clear all analysis for project"""
        self.analysis_cache.clear()
        self.context_history.clear()
        self.recommendation_engine.recommendation_history.pop(self.project_id, None)
        self.scenario_simulator.scenarios_history.pop(self.project_id, None)
    
    def _get_latest_analysis(self) -> Optional[RecommendationOutput]:
        """Get most recent analysis for this project"""
        # Get latest from any task
        latest = None
        for key, analysis in self.analysis_cache.items():
            if analysis.project_id == self.project_id:
                if latest is None or analysis.generated_at > latest.generated_at:
                    latest = analysis
        
        return latest
    
    def _build_monday_mappings(self, recommendations: List[Recommendation]) -> List[Dict[str, str]]:
        """Build monday.com mappings from recommendations"""
        return [r.monday_com_column_map for r in recommendations[:5]]  # Top 5
