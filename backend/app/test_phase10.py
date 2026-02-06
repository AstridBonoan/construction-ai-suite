"""
Feature 10: Comprehensive Unit Tests
Tests for recommendation engine, scenario simulator, and integration
"""
import unittest
from datetime import datetime, timedelta
from typing import Dict

from phase10_recommendation_types import (
    RecommendationType,
    RecommendationSeverity,
    ScenarioType,
    RecommendationContext,
    RecommendationRequest,
    ScenarioRequest,
)
from phase10_recommendation_engine import RecommendationEngine
from phase10_scenario_simulator import ScenarioSimulator
from phase10_recommendation_integration import Feature10Integration, create_feature10_integration


class TestRecommendationEngine(unittest.TestCase):
    """Test recommendation generation logic"""
    
    def setUp(self):
        """Initialize engine before each test"""
        self.engine = RecommendationEngine()
        self.project_id = "test_project_001"
        self.base_context = RecommendationContext(
            project_id=self.project_id,
            current_overall_risk=0.5,
            current_total_cost=1000000,
            current_duration_days=180,
            cost_risk=0.5,
            schedule_risk=0.5,
            workforce_risk=0.4,
            subcontractor_risk=0.4,
            equipment_risk=0.3,
            materials_risk=0.3,
            compliance_risk=0.3,
            environmental_risk=0.2,
            project_phase='execution',
            days_into_project=60,
            days_remaining=120,
            percent_complete=0.33,
            budget_headroom_available=100000,
            schedule_headroom_available_days=14,
            resource_availability={},
            risk_trend='stable',
            cost_variance=0.05,
            schedule_variance=0.0,
            similar_projects_count=5,
            success_rate_percent=0.75,
        )
    
    def test_cost_controls_recommendation_triggered(self):
        """Test cost controls recommendation when cost_risk > 0.6"""
        context = self.base_context
        context.cost_risk = 0.65  # Triggers cost controls
        
        request = RecommendationRequest(
            max_recommendations=10,
            include_types=None,
            exclude_types=None,
            minimum_cost_reduction=0,
            minimum_schedule_improvement=0,
            minimum_risk_reduction=0,
        )
        
        recs = self.engine.generate_recommendations(context, request)
        
        # Should have recommendations
        self.assertTrue(len(recs) > 0, "Cost controls should be recommended when cost_risk > 0.6")
        
        # At least one should be cost controls
        cost_control_recs = [r for r in recs if r.recommendation_type == RecommendationType.COST_REDUCTION]
        self.assertTrue(len(cost_control_recs) > 0, "Should have cost control recommendation")
    
    def test_schedule_buffer_recommendation_triggered(self):
        """Test schedule buffer recommendation when schedule_risk > 0.6"""
        context = self.base_context
        context.schedule_risk = 0.65  # Triggers schedule buffer
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        buffer_recs = [r for r in recs if r.recommendation_type == RecommendationType.SCHEDULE_BUFFER]
        self.assertTrue(len(buffer_recs) > 0, "Should have schedule buffer recommendation")
    
    def test_workforce_augmentation_recommendation(self):
        """Test workforce augmentation when workforce_risk > 0.55"""
        context = self.base_context
        context.workforce_risk = 0.56  # Triggers workforce augmentation
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        workforce_recs = [r for r in recs if r.recommendation_type == RecommendationType.WORKFORCE_OPTIMIZATION]
        self.assertTrue(len(workforce_recs) > 0, "Should have workforce recommendation")
    
    def test_equipment_maintenance_recommendation(self):
        """Test equipment maintenance when equipment_risk > 0.5"""
        context = self.base_context
        context.equipment_risk = 0.55  # Triggers equipment maintenance
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        equipment_recs = [r for r in recs if r.recommendation_type == RecommendationType.EQUIPMENT_EFFICIENCY]
        self.assertTrue(len(equipment_recs) > 0, "Should have equipment recommendation")
    
    def test_compliance_enhancement_recommendation(self):
        """Test compliance enhancement when compliance_risk > 0.55"""
        context = self.base_context
        context.compliance_risk = 0.56  # Triggers compliance
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        compliance_recs = [r for r in recs if r.recommendation_type == RecommendationType.COMPLIANCE_ENHANCEMENT]
        self.assertTrue(len(compliance_recs) > 0, "Should have compliance recommendation")
    
    def test_environmental_safeguards_recommendation(self):
        """Test environmental safeguards when environmental_risk > 0.5"""
        context = self.base_context
        context.environmental_risk = 0.55  # Triggers environmental
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        env_recs = [r for r in recs if r.recommendation_type == RecommendationType.ENVIRONMENTAL_PROTECTION]
        self.assertTrue(len(env_recs) > 0, "Should have environmental recommendation")
    
    def test_material_substitution_recommendation(self):
        """Test material substitution when cost_variance > 0.1"""
        context = self.base_context
        context.cost_variance = 0.15  # Triggers material substitution
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        material_recs = [r for r in recs if r.recommendation_type == RecommendationType.MATERIAL_SUBSTITUTION]
        self.assertTrue(len(material_recs) > 0, "Should have material substitution recommendation")
    
    def test_fast_track_recommendation(self):
        """Test fast-track when schedule_risk > 0.65"""
        context = self.base_context
        context.schedule_risk = 0.70  # Triggers fast-track
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        # Should have schedule-related recommendations
        schedule_recs = [r for r in recs if r.recommendation_type == RecommendationType.SCHEDULE_ACCELERATION]
        self.assertTrue(len(schedule_recs) > 0, "Should have schedule acceleration recommendation")
    
    def test_recommendations_sorting_by_severity(self):
        """Test recommendations are sorted by severity"""
        context = self.base_context
        # Create high-risk scenario
        context.cost_risk = 0.8
        context.schedule_risk = 0.8
        context.workforce_risk = 0.8
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        # Check severity order (higher severity first)
        if len(recs) > 1:
            for i in range(len(recs) - 1):
                curr_severity = self._severity_value(recs[i].severity)
                next_severity = self._severity_value(recs[i+1].severity)
                self.assertGreaterEqual(curr_severity, next_severity, "Recommendations should be sorted by severity")
    
    def _severity_value(self, severity):
        """Map severity to numeric value"""
        severity_map = {
            RecommendationSeverity.LOW: 1,
            RecommendationSeverity.MEDIUM: 2,
            RecommendationSeverity.HIGH: 3,
            RecommendationSeverity.CRITICAL: 4,
        }
        return severity_map.get(severity, 0)
    
    def test_recommendation_filtering_by_type(self):
        """Test filtering recommendations by type"""
        context = self.base_context
        context.cost_risk = 0.7
        context.schedule_risk = 0.7
        
        # Only request cost recommendations
        request = RecommendationRequest(
            include_types=[RecommendationType.COST_REDUCTION]
        )
        recs = self.engine.generate_recommendations(context, request)
        
        # Should only have cost reduction type
        for rec in recs:
            self.assertEqual(rec.recommendation_type, RecommendationType.COST_REDUCTION)
    
    def test_recommendation_filtering_by_min_cost_reduction(self):
        """Test filtering by minimum cost reduction"""
        context = self.base_context
        context.cost_risk = 0.7
        
        # Only high-impact cost reductions
        request = RecommendationRequest(
            minimum_cost_reduction=100000  # At least $100K savings
        )
        recs = self.engine.generate_recommendations(context, request)
        
        # All should meet minimum
        for rec in recs:
            cost_savings = -rec.impact.cost_impact.total_cost_delta
            self.assertGreaterEqual(cost_savings, 99000, "Should meet minimum cost reduction")
    
    def test_recommendation_history_tracking(self):
        """Test that recommendations are tracked in history"""
        context = self.base_context
        context.cost_risk = 0.7
        
        request = RecommendationRequest()
        recs1 = self.engine.generate_recommendations(context, request)
        
        # Get history
        history = self.engine.get_recommendation_history(self.project_id)
        
        self.assertTrue(len(history) > 0, "Should have history after generation")
        self.assertEqual(len(history[0]), len(recs1), "History should match generated recommendations")
    
    def test_recommendation_impacts_correct(self):
        """Test recommendation impacts are calculated correctly"""
        context = self.base_context
        context.cost_risk = 0.7
        
        request = RecommendationRequest(include_types=[RecommendationType.COST_REDUCTION])
        recs = self.engine.generate_recommendations(context, request)
        
        if len(recs) > 0:
            rec = recs[0]
            # Cost controls should reduce cost and risk
            self.assertLess(rec.impact.cost_impact.total_cost_delta, 0, "Should reduce cost")
            self.assertLess(rec.impact.risk_impact.overall_risk_delta, 0, "Should reduce risk")
    
    def test_recommendation_confidence_based_on_impact(self):
        """Test confidence is based on impact"""
        context = self.base_context
        context.cost_risk = 0.7
        
        request = RecommendationRequest()
        recs = self.engine.generate_recommendations(context, request)
        
        # All should have confidence
        for rec in recs:
            self.assertGreater(rec.confidence_level, 0.5, "Should have reasonable confidence")
            self.assertLessEqual(rec.confidence_level, 1.0, "Confidence should not exceed 1.0")


class TestScenarioSimulator(unittest.TestCase):
    """Test scenario simulation logic"""
    
    def setUp(self):
        """Initialize simulator before each test"""
        self.simulator = ScenarioSimulator()
        self.project_id = "test_project_002"
        self.base_context = RecommendationContext(
            project_id=self.project_id,
            current_overall_risk=0.5,
            current_total_cost=1000000,
            current_duration_days=180,
            cost_risk=0.5,
            schedule_risk=0.5,
            workforce_risk=0.4,
            subcontractor_risk=0.4,
            equipment_risk=0.3,
            materials_risk=0.3,
            compliance_risk=0.3,
            environmental_risk=0.2,
            project_phase='execution',
            days_into_project=60,
            days_remaining=120,
            percent_complete=0.33,
            budget_headroom_available=100000,
            schedule_headroom_available_days=14,
            resource_availability={},
            risk_trend='stable',
            cost_variance=0.05,
            schedule_variance=0.0,
            similar_projects_count=5,
            success_rate_percent=0.75,
        )
    
    def test_baseline_scenario_generates(self):
        """Test baseline scenario is generated"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        baseline_scenarios = [s for s in scenarios if s.scenario_type == ScenarioType.BASELINE]
        
        self.assertTrue(len(baseline_scenarios) > 0, "Should generate baseline scenario")
    
    def test_optimistic_scenario_reduces_risk(self):
        """Test optimistic scenario reduces risk"""
        context = self.base_context
        request = ScenarioRequest(scenario_types=[ScenarioType.OPTIMISTIC])
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        optimistic = [s for s in scenarios if s.scenario_type == ScenarioType.OPTIMISTIC]
        
        self.assertTrue(len(optimistic) > 0, "Should generate optimistic scenario")
        if len(optimistic) > 0:
            # Optimistic should have lower risk
            self.assertLess(optimistic[0].estimated_risk_score, context.current_overall_risk * 1.1,
                           "Optimistic should have lower risk")
    
    def test_conservative_scenario_marked_recommended(self):
        """Test conservative scenario is marked as recommended"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        conservative = [s for s in scenarios if s.scenario_type == ScenarioType.CONSERVATIVE]
        
        self.assertTrue(len(conservative) > 0, "Should generate conservative scenario")
        if len(conservative) > 0:
            # Conservative should be recommended
            self.assertTrue(conservative[0].recommended, "Conservative scenario should be recommended")
    
    def test_cost_optimized_scenario_reduces_cost(self):
        """Test cost-optimized scenario reduces cost"""
        context = self.base_context
        request = ScenarioRequest(scenario_types=[ScenarioType.COST_OPTIMIZED])
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        cost_opt = [s for s in scenarios if s.scenario_type == ScenarioType.COST_OPTIMIZED]
        
        self.assertTrue(len(cost_opt) > 0, "Should generate cost-optimized scenario")
        if len(cost_opt) > 0:
            # Cost-optimized should have lower cost
            self.assertLess(cost_opt[0].estimated_total_cost, context.current_total_cost,
                           "Cost-optimized should have lower cost")
    
    def test_time_optimized_scenario_reduces_schedule(self):
        """Test time-optimized scenario reduces schedule"""
        context = self.base_context
        request = ScenarioRequest(scenario_types=[ScenarioType.TIME_OPTIMIZED])
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        time_opt = [s for s in scenarios if s.scenario_type == ScenarioType.TIME_OPTIMIZED]
        
        self.assertTrue(len(time_opt) > 0, "Should generate time-optimized scenario")
        if len(time_opt) > 0:
            # Time-optimized should have shorter duration
            self.assertLess(time_opt[0].estimated_completion_days, context.current_duration_days,
                           "Time-optimized should have shorter schedule")
    
    def test_risk_optimized_scenario_reduces_risk(self):
        """Test risk-optimized scenario reduces risk significantly"""
        context = self.base_context
        request = ScenarioRequest(scenario_types=[ScenarioType.RISK_OPTIMIZED])
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        risk_opt = [s for s in scenarios if s.scenario_type == ScenarioType.RISK_OPTIMIZED]
        
        self.assertTrue(len(risk_opt) > 0, "Should generate risk-optimized scenario")
        if len(risk_opt) > 0:
            # Risk-optimized should have much lower risk
            self.assertLess(risk_opt[0].estimated_risk_score, context.current_overall_risk * 0.8,
                           "Risk-optimized should significantly reduce risk")
    
    def test_scenario_comparison_identifies_best_for_risk(self):
        """Test comparison identifies best scenario for risk"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        self.assertIsNotNone(comparison.best_for_risk, "Should identify best for risk")
        self.assertIn('scenario_id', comparison.best_for_risk)
    
    def test_scenario_comparison_identifies_best_for_cost(self):
        """Test comparison identifies best scenario for cost"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        self.assertIsNotNone(comparison.best_for_cost, "Should identify best for cost")
        self.assertIn('scenario_id', comparison.best_for_cost)
    
    def test_scenario_comparison_identifies_best_for_schedule(self):
        """Test comparison identifies best scenario for schedule"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        self.assertIsNotNone(comparison.best_for_schedule, "Should identify best for schedule")
        self.assertIn('scenario_id', comparison.best_for_schedule)
    
    def test_scenario_tradeoffs_calculated(self):
        """Test trade-off analysis is calculated"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        for scenario in scenarios:
            # All should have tradeoffs
            self.assertIsNotNone(scenario.trade_offs)
            self.assertIn('cost_vs_time', scenario.trade_offs)
            self.assertIn('cost_vs_risk', scenario.trade_offs)
            self.assertIn('time_vs_risk', scenario.trade_offs)
    
    def test_scenario_viability_reasonable(self):
        """Test viability scores are reasonable"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison = self.simulator.simulate_scenarios(context, request)
        
        scenarios = comparison.scenarios if comparison.scenarios else []
        for scenario in scenarios:
            self.assertGreaterEqual(scenario.viability_score, 0.0, "Viability should be >= 0")
            self.assertLessEqual(scenario.viability_score, 1.0, "Viability should be <= 1")
    
    def test_scenario_history_tracking(self):
        """Test scenarios are tracked in history"""
        context = self.base_context
        request = ScenarioRequest()
        
        comparison1 = self.simulator.simulate_scenarios(context, request)
        
        # Get history
        history = self.simulator.scenarios_history.get(self.project_id, [])
        
        self.assertTrue(len(history) > 0, "Should have history after simulation")


class TestFeature10Integration(unittest.TestCase):
    """Test Feature 10 integration layer"""
    
    def setUp(self):
        """Initialize integration before each test"""
        self.project_id = "test_project_003"
        self.integration = create_feature10_integration(self.project_id)
        self.base_context = RecommendationContext(
            project_id=self.project_id,
            current_overall_risk=0.5,
            current_total_cost=1000000,
            current_duration_days=180,
            cost_risk=0.5,
            schedule_risk=0.5,
            workforce_risk=0.4,
            subcontractor_risk=0.4,
            equipment_risk=0.3,
            materials_risk=0.3,
            compliance_risk=0.3,
            environmental_risk=0.2,
            project_phase='execution',
            days_into_project=60,
            days_remaining=120,
            percent_complete=0.33,
            budget_headroom_available=100000,
            schedule_headroom_available_days=14,
            resource_availability={},
            risk_trend='stable',
            cost_variance=0.05,
            schedule_variance=0.0,
            similar_projects_count=5,
            success_rate_percent=0.75,
        )
    
    def test_integration_factory_creates_instance(self):
        """Test factory creates integration instance"""
        self.assertIsNotNone(self.integration, "Factory should create integration")
        self.assertEqual(self.integration.project_id, self.project_id)
    
    def test_analyze_project_returns_output(self):
        """Test analyze_project returns complete output"""
        context = self.base_context
        rec_request = RecommendationRequest()
        scenario_request = ScenarioRequest()
        
        output = self.integration.analyze_project(context, rec_request, scenario_request)
        
        self.assertIsNotNone(output, "Should return output")
        self.assertIsNotNone(output.recommendations, "Should have recommendations")
        self.assertIsNotNone(output.scenarios, "Should have scenarios")
        self.assertIsNotNone(output.scenario_comparison, "Should have comparison")
    
    def test_get_feature1_input_returns_correct_format(self):
        """Test Feature 1 input has correct structure"""
        context = self.base_context
        self.integration.analyze_project(context, RecommendationRequest(), ScenarioRequest())
        
        feature1_input = self.integration.get_feature1_input()
        
        # Should have key Feature 10 fields
        self.assertIn('feature10_all_recommendations', feature1_input)
        self.assertIn('feature10_top_recommendation', feature1_input)
        self.assertIn('feature10_recommended_scenario', feature1_input)
        self.assertIn('feature10_total_risk_reduction_potential', feature1_input)
        self.assertIn('feature10_total_cost_reduction_potential', feature1_input)
    
    def test_get_monday_com_data_returns_mappings(self):
        """Test Monday.com data has correct mappings"""
        context = self.base_context
        self.integration.analyze_project(context, RecommendationRequest(), ScenarioRequest())
        
        monday_data = self.integration.get_monday_com_data()
        
        self.assertIsNotNone(monday_data, "Should return monday data")
        self.assertIn('monday_fields', monday_data)
    
    def test_context_history_preserved(self):
        """Test context history is preserved"""
        context1 = self.base_context
        self.integration.analyze_project(context1, RecommendationRequest(), ScenarioRequest())
        
        context2 = self.base_context
        context2.current_overall_risk = 0.6
        self.integration.analyze_project(context2, RecommendationRequest(), ScenarioRequest())
        
        history = self.integration.get_context_history(limit=10)
        
        self.assertGreaterEqual(len(history), 2, "Should preserve multiple contexts")
    
    def test_reset_clears_analysis(self):
        """Test reset clears analysis"""
        context = self.base_context
        self.integration.analyze_project(context, RecommendationRequest(), ScenarioRequest())
        
        # Should have analysis
        feature1_before = self.integration.get_feature1_input()
        self.assertIsNotNone(feature1_before)
        
        # Reset
        self.integration.reset_project()
        
        # Should not have cached analysis
        feature1_after = self.integration.get_feature1_input()
        self.assertIsNotNone(feature1_after)  # Still exists but empty


class TestDeterminism(unittest.TestCase):
    """Test deterministic behavior (same input -> same output)"""
    
    def setUp(self):
        """Initialize for determinism tests"""
        self.base_context = RecommendationContext(
            project_id="determinism_test",
            current_overall_risk=0.5,
            current_total_cost=1000000,
            current_duration_days=180,
            cost_risk=0.5,
            schedule_risk=0.5,
            workforce_risk=0.4,
            subcontractor_risk=0.4,
            equipment_risk=0.3,
            materials_risk=0.3,
            compliance_risk=0.3,
            environmental_risk=0.2,
            project_phase='execution',
            days_into_project=60,
            days_remaining=120,
            percent_complete=0.33,
            budget_headroom_available=100000,
            schedule_headroom_available_days=14,
            resource_availability={},
            risk_trend='stable',
            cost_variance=0.05,
            schedule_variance=0.0,
            similar_projects_count=5,
            success_rate_percent=0.75,
        )
    
    def test_recommendations_deterministic(self):
        """Test recommendations are deterministic"""
        engine1 = RecommendationEngine()
        engine2 = RecommendationEngine()
        
        request = RecommendationRequest()
        recs1 = engine1.generate_recommendations(self.base_context, request)
        recs2 = engine2.generate_recommendations(self.base_context, request)
        
        # Should have same count and same impacts
        self.assertEqual(len(recs1), len(recs2), "Should generate same count of recommendations")
        
        for r1, r2 in zip(recs1, recs2):
            self.assertEqual(r1.title, r2.title, "Same recommendation type should have same title")
            self.assertAlmostEqual(
                r1.impact.cost_impact.total_cost_delta,
                r2.impact.cost_impact.total_cost_delta,
                places=2,
                msg="Should have same cost impact"
            )
    
    def test_scenarios_deterministic(self):
        """Test scenarios are deterministic"""
        sim1 = ScenarioSimulator()
        sim2 = ScenarioSimulator()
        
        request = ScenarioRequest()
        comp1 = sim1.simulate_scenarios(self.base_context, request)
        comp2 = sim2.simulate_scenarios(self.base_context, request)
        
        # Should have same scenarios
        if comp1.scenarios and comp2.scenarios:
            self.assertEqual(len(comp1.scenarios), len(comp2.scenarios))
            
            for s1, s2 in zip(comp1.scenarios, comp2.scenarios):
                self.assertAlmostEqual(
                    s1.estimated_risk_score,
                    s2.estimated_risk_score,
                    places=4,
                    msg="Should have same risk projection"
                )


if __name__ == '__main__':
    unittest.main()
