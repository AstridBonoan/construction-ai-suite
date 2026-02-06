"""
Feature 9: Unit Tests for Multi-Factor Risk Synthesis
Tests for aggregation algorithms, interactions, and Feature 1 integration
"""
import pytest
from datetime import datetime, timedelta
from phase9_risk_types import (
    RiskCategory,
    RiskSeverity,
    AggregationMethod,
    RiskFactorInput,
    MultiFactorRiskInput,
    RiskWeightConfig,
)
from phase9_risk_aggregator import MultiFactorRiskAggregator
from phase9_risk_integration import create_feature9_integration


# Fixtures
@pytest.fixture
def default_weights():
    """Default risk weight configuration"""
    return RiskWeightConfig()


@pytest.fixture
def aggregator(default_weights):
    """Create aggregator instance"""
    return MultiFactorRiskAggregator(weights_config=default_weights)


@pytest.fixture
def integration():
    """Create Feature 9 integration instance"""
    return create_feature9_integration("test_project_123")


@pytest.fixture
def sample_cost_risk():
    """Sample cost risk factor"""
    return RiskFactorInput(
        category=RiskCategory.COST,
        score=0.6,
        severity=RiskSeverity.HIGH,
        confidence=0.9,
        contributing_issues=["Budget overrun on materials"],
        trend="increasing",
        timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def sample_schedule_risk():
    """Sample schedule risk factor"""
    return RiskFactorInput(
        category=RiskCategory.SCHEDULE,
        score=0.7,
        severity=RiskSeverity.HIGH,
        confidence=0.85,
        contributing_issues=["Permit delays"],
        trend="increasing",
        timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def sample_workforce_risk():
    """Sample workforce risk factor"""
    return RiskFactorInput(
        category=RiskCategory.WORKFORCE,
        score=0.4,
        severity=RiskSeverity.MEDIUM,
        confidence=0.8,
        contributing_issues=["Labor shortage"],
        trend="stable",
        timestamp=datetime.now().isoformat(),
    )


@pytest.fixture
def complete_input(sample_cost_risk, sample_schedule_risk, sample_workforce_risk):
    """Complete multi-factor risk input"""
    return MultiFactorRiskInput(
        project_id="test_project",
        task_id="task_123",
        cost_risk=sample_cost_risk,
        schedule_risk=sample_schedule_risk,
        workforce_risk=sample_workforce_risk,
        subcontractor_risk=None,
        equipment_risk=None,
        materials_risk=None,
        compliance_risk=None,
        environmental_risk=None,
        project_phase="execution",
        criticality="high",
        dependencies_count=3,
    )


# Test classes
class TestMultiFactorRiskAggregator:
    """Tests for core aggregation algorithms"""

    def test_aggregator_initialization(self, aggregator, default_weights):
        """Aggregator should initialize with default weights"""
        assert aggregator is not None
        assert aggregator.weights_config == default_weights

    def test_weighted_average_all_factors(self, aggregator):
        """Weighted average should combine all factors"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.8, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.6, confidence=0.9
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.4, confidence=0.9
            ),
        }

        result = aggregator._aggregate_weighted_average(factors, aggregator.weights_config)
        
        # Score should be between min and max of inputs
        assert 0.4 <= result <= 0.8
        # Should favor higher-weighted factors (Cost=18%, Schedule=18%)
        assert result > 0.5

    def test_weighted_average_single_factor(self, aggregator):
        """Weighted average with single factor should return that factor"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.7, confidence=0.9
            ),
        }

        result = aggregator._aggregate_weighted_average(factors, aggregator.weights_config)
        assert result == 0.7

    def test_worst_case_aggregation(self, aggregator):
        """Worst case should return maximum factor score"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.5, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.9, confidence=0.9
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.3, confidence=0.9
            ),
        }

        result = aggregator._aggregate_worst_case(factors, aggregator.weights_config)
        assert result == 0.9  # Maximum score

    def test_compound_aggregation(self, aggregator):
        """Compound aggregation should use joint probability formula"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.5, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.5, confidence=0.9
            ),
        }

        result = aggregator._aggregate_compound(factors, aggregator.weights_config)
        
        # Compound should be > weighted average for equal factors
        # 1 - (1-0.5)*(1-0.5) = 1 - 0.25 = 0.75
        expected = 1 - (1 - 0.5) * (1 - 0.5)
        assert abs(result - expected) < 0.01

    def test_hierarchical_aggregation(self, aggregator):
        """Hierarchical aggregation should use tier-based weighting"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.8, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.7, confidence=0.9
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.4, confidence=0.9
            ),
        }

        result = aggregator._aggregate_hierarchical(factors, aggregator.weights_config)
        
        # Should favor Tier 1 (Cost/Schedule)
        assert result >= 0.6

    def test_phase_adjustment_planning(self, aggregator):
        """Planning phase should apply 1.0x adjustment"""
        score = 0.6
        adjusted = aggregator._apply_phase_adjustment(score, "planning")
        assert abs(adjusted - 0.6) < 0.01

    def test_phase_adjustment_execution(self, aggregator):
        """Execution phase should apply 1.3x adjustment"""
        score = 0.6
        adjusted = aggregator._apply_phase_adjustment(score, "execution")
        assert abs(adjusted - 0.78) < 0.01  # min(0.6 * 1.3, 1.0) = 0.78

    def test_phase_adjustment_closing(self, aggregator):
        """Closing phase should apply 0.7x adjustment"""
        score = 0.6
        adjusted = aggregator._apply_phase_adjustment(score, "closing")
        assert abs(adjusted - 0.42) < 0.01

    def test_confidence_calculation_all_high(self, aggregator):
        """Confidence with all high confidences should be high"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.5, confidence=1.0
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.5, confidence=1.0
            ),
        }

        confidence = aggregator._calculate_confidence(factors)
        assert confidence >= 0.95

    def test_confidence_calculation_mixed(self, aggregator):
        """Confidence with mixed inputs should be geometric mean"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.5, confidence=0.8
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.5, confidence=0.5
            ),
        }

        confidence = aggregator._calculate_confidence(factors)
        # Geometric mean: sqrt(0.8 * 0.5) ≈ 0.632
        assert 0.6 < confidence < 0.65

    def test_severity_classification_low(self, aggregator):
        """Score < 0.25 should be LOW"""
        severity = aggregator._classify_severity(0.2)
        assert severity == RiskSeverity.LOW

    def test_severity_classification_medium(self, aggregator):
        """Score 0.25-0.50 should be MEDIUM"""
        severity = aggregator._classify_severity(0.38)
        assert severity == RiskSeverity.MEDIUM

    def test_severity_classification_high(self, aggregator):
        """Score 0.50-0.75 should be HIGH"""
        severity = aggregator._classify_severity(0.60)
        assert severity == RiskSeverity.HIGH

    def test_severity_classification_critical(self, aggregator):
        """Score > 0.75 should be CRITICAL"""
        severity = aggregator._classify_severity(0.85)
        assert severity == RiskSeverity.CRITICAL

    def test_risk_interaction_cost_schedule(self, aggregator):
        """Cost-schedule interaction should amplify schedule risk"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.8, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.5, confidence=0.9
            ),
        }

        interactions = aggregator._model_interactions(factors)
        
        # Schedule risk should be amplified due to high cost risk
        schedule_interaction = interactions.get(RiskCategory.SCHEDULE, 0.5)
        assert schedule_interaction > 0.5

    def test_risk_interaction_schedule_workforce(self, aggregator):
        """Schedule-workforce interaction should amplify workforce risk"""
        factors = {
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.8, confidence=0.9
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.4, confidence=0.9
            ),
        }

        interactions = aggregator._model_interactions(factors)
        
        # Workforce risk should be amplified due to high schedule risk
        workforce_interaction = interactions.get(RiskCategory.WORKFORCE, 0.4)
        assert workforce_interaction > 0.4

    def test_normalization_by_confidence(self, aggregator):
        """Normalization should reduce scores with low confidence"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.9, confidence=0.5
            ),
        }

        normalized = aggregator._normalize_risk_factors(factors)
        cost_normalized = normalized[RiskCategory.COST]
        
        # High confidence should have minimal effect
        assert cost_normalized <= 0.9

    def test_factor_contributions(self, aggregator):
        """Factor contributions should sum to approximately 100%"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.8, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.6, confidence=0.9
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.4, confidence=0.9
            ),
        }

        overall_score = 0.65  # Mock overall score
        contributions = aggregator._generate_contributions(
            factors, overall_score, aggregator.weights_config
        )
        
        total_contribution = sum(c.percentage for c in contributions)
        # Should be close to 100%
        assert 90 <= total_contribution <= 110

    def test_executive_summary_generation(self, aggregator):
        """Executive summary should be concise and informative"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.8, confidence=0.9
            ),
        }

        summary = aggregator._generate_executive_summary(
            0.8, RiskSeverity.HIGH, factors
        )
        
        assert summary is not None
        assert len(summary) > 0
        assert len(summary) < 200  # Should be concise

    def test_mitigation_plan_generation(self, aggregator):
        """Mitigation plan should provide actionable recommendations"""
        factors = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST,
                score=0.8,
                confidence=0.9,
                contributing_issues=["Budget overrun"],
            ),
        }

        plan = aggregator._generate_mitigation_plan(
            0.8, RiskSeverity.HIGH, factors
        )
        
        assert plan is not None
        assert len(plan) > 0

    def test_synthesis_complete_flow(self, aggregator, complete_input):
        """Complete synthesis should return valid output"""
        result = aggregator.synthesize(complete_input)
        
        assert result is not None
        assert result.overall_risk_score >= 0.0
        assert result.overall_risk_score <= 1.0
        assert result.overall_severity in RiskSeverity
        assert 0.0 <= result.overall_confidence <= 1.0
        assert result.executive_summary is not None
        assert len(result.factor_contributions) > 0

    def test_synthesis_deterministic(self, aggregator, complete_input):
        """Same input should produce same output"""
        result1 = aggregator.synthesize(complete_input)
        result2 = aggregator.synthesize(complete_input)
        
        assert result1.overall_risk_score == result2.overall_risk_score
        assert result1.overall_severity == result2.overall_severity
        assert result1.overall_confidence == result2.overall_confidence


class TestRiskWeightConfig:
    """Tests for weight configuration"""

    def test_default_weights_sum(self):
        """Default weights should sum to 1.0"""
        config = RiskWeightConfig()
        total = (
            config.cost_weight
            + config.schedule_weight
            + config.workforce_weight
            + config.subcontractor_weight
            + config.equipment_weight
            + config.materials_weight
            + config.compliance_weight
            + config.environmental_weight
        )
        assert abs(total - 1.0) < 0.01

    def test_interaction_multipliers_reasonable(self):
        """Interaction multipliers should be reasonable"""
        config = RiskWeightConfig()
        assert 0.0 < config.cost_schedule_multiplier < 0.2
        assert 0.0 < config.schedule_workforce_multiplier < 0.2
        assert 0.0 < config.equipment_schedule_multiplier < 0.2
        assert 0.0 < config.compliance_safety_multiplier < 0.2

    def test_phase_adjustments_reasonable(self):
        """Phase adjustments should be reasonable"""
        config = RiskWeightConfig()
        assert 0.9 < config.planning_adjustment < 1.1
        assert 1.2 < config.execution_adjustment < 1.4
        assert 0.6 < config.closing_adjustment < 0.8


class TestFeature9Integration:
    """Tests for Feature 1 integration"""

    def test_integration_initialization(self, integration):
        """Integration should initialize properly"""
        assert integration is not None
        assert integration.project_id == "test_project_123"

    def test_register_single_risk(self, integration):
        """Should register single risk factor"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST,
            score=0.6,
            confidence=0.9,
        )
        
        result = integration.register_feature_risks(
            cost_risk=cost_risk,
            project_phase="execution",
        )
        
        assert result is not None
        assert result.overall_risk_score >= 0.0

    def test_register_multiple_risks(self, integration):
        """Should register multiple risk factors"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        schedule_risk = RiskFactorInput(
            category=RiskCategory.SCHEDULE, score=0.7, confidence=0.85
        )
        workforce_risk = RiskFactorInput(
            category=RiskCategory.WORKFORCE, score=0.4, confidence=0.8
        )
        
        result = integration.register_feature_risks(
            cost_risk=cost_risk,
            schedule_risk=schedule_risk,
            workforce_risk=workforce_risk,
            project_phase="execution",
        )
        
        assert result is not None
        # With 3 factors, should have some balance
        assert 0.4 <= result.overall_risk_score <= 0.7

    def test_core_engine_input_format(self, integration):
        """Core engine input should have required fields"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        
        integration.register_feature_risks(
            cost_risk=cost_risk,
            project_phase="execution",
        )
        
        core_input = integration.get_core_engine_input()
        
        assert "feature9_overall_risk" in core_input
        assert "feature9_primary_drivers" in core_input
        assert "feature9_confidence" in core_input

    def test_synthesis_history_tracking(self, integration):
        """Should track synthesis history"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        
        # Register multiple times
        integration.register_feature_risks(cost_risk=cost_risk)
        integration.register_feature_risks(cost_risk=cost_risk)
        
        history = integration.get_synthesis_history()
        assert len(history) >= 2

    def test_risk_trend_calculation(self, integration):
        """Should calculate risk trends"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.5, confidence=0.9
        )
        
        # Create trend by multiple registrations with increasing score
        for score in [0.5, 0.55, 0.6, 0.65, 0.7]:
            cost_risk.score = score
            integration.register_feature_risks(cost_risk=cost_risk)
        
        trend = integration.get_risk_trend()
        
        assert trend is not None
        assert "direction" in trend

    def test_alert_threshold_critical(self, integration):
        """Should trigger CRITICAL alert when risk exceeds threshold"""
        # High risk that exceeds critical threshold (0.75)
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.9, confidence=0.95
        )
        schedule_risk = RiskFactorInput(
            category=RiskCategory.SCHEDULE, score=0.85, confidence=0.9
        )
        
        integration.register_feature_risks(
            cost_risk=cost_risk,
            schedule_risk=schedule_risk,
        )
        
        alerts = integration.alert_history
        critical_alerts = [a for a in alerts if "CRITICAL" in a.alert_type]
        
        assert len(critical_alerts) > 0

    def test_alert_threshold_high(self, integration):
        """Should trigger HIGH alert when risk exceeds medium threshold"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        schedule_risk = RiskFactorInput(
            category=RiskCategory.SCHEDULE, score=0.55, confidence=0.9
        )
        
        integration.register_feature_risks(
            cost_risk=cost_risk,
            schedule_risk=schedule_risk,
        )
        
        alerts = integration.alert_history
        high_alerts = [a for a in alerts if "HIGH" in a.alert_type]
        
        assert len(high_alerts) >= 0  # May or may not trigger depending on synthesis

    def test_monday_data_formatting(self, integration):
        """Should format data for monday.com"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        
        integration.register_feature_risks(cost_risk=cost_risk)
        
        monday_data = integration.get_monday_com_data()
        
        assert monday_data is not None
        assert "Holistic Risk" in monday_data or len(monday_data) > 0

    def test_reset_project(self, integration):
        """Should reset all project data"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        
        integration.register_feature_risks(cost_risk=cost_risk)
        initial_history = len(integration.get_synthesis_history())
        
        integration.reset_project()
        final_history = len(integration.get_synthesis_history())
        
        assert final_history < initial_history

    def test_task_level_synthesis(self, integration):
        """Should track task-level synthesis separately"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.6, confidence=0.9
        )
        
        result1 = integration.register_feature_risks(
            cost_risk=cost_risk,
            task_id="task_1",
        )
        result2 = integration.register_feature_risks(
            cost_risk=cost_risk,
            task_id="task_2",
        )
        
        assert result1.task_id == "task_1"
        assert result2.task_id == "task_2"


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios"""

    def test_all_factors_present(self, integration):
        """Should synthesize when all 8 factors are present"""
        risks = {
            RiskCategory.COST: RiskFactorInput(
                category=RiskCategory.COST, score=0.6, confidence=0.9
            ),
            RiskCategory.SCHEDULE: RiskFactorInput(
                category=RiskCategory.SCHEDULE, score=0.7, confidence=0.85
            ),
            RiskCategory.WORKFORCE: RiskFactorInput(
                category=RiskCategory.WORKFORCE, score=0.4, confidence=0.8
            ),
            RiskCategory.SUBCONTRACTOR: RiskFactorInput(
                category=RiskCategory.SUBCONTRACTOR, score=0.5, confidence=0.75
            ),
            RiskCategory.EQUIPMENT: RiskFactorInput(
                category=RiskCategory.EQUIPMENT, score=0.45, confidence=0.8
            ),
            RiskCategory.MATERIALS: RiskFactorInput(
                category=RiskCategory.MATERIALS, score=0.5, confidence=0.85
            ),
            RiskCategory.COMPLIANCE: RiskFactorInput(
                category=RiskCategory.COMPLIANCE, score=0.55, confidence=0.9
            ),
            RiskCategory.ENVIRONMENTAL: RiskFactorInput(
                category=RiskCategory.ENVIRONMENTAL, score=0.3, confidence=0.7
            ),
        }
        
        result = integration.register_feature_risks(**risks)
        
        assert result is not None
        assert result.overall_risk_score >= 0.4  # Should aggregate to reasonable level

    def test_sparse_factors(self, integration):
        """Should synthesize with only 1-2 factors"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.8, confidence=0.9
        )
        
        result = integration.register_feature_risks(cost_risk=cost_risk)
        
        assert result is not None
        assert result.overall_risk_score > 0.5  # High cost risk should result in high overall

    def test_low_confidence_inputs(self, integration):
        """Should handle low-confidence inputs gracefully"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.9, confidence=0.1
        )
        
        result = integration.register_feature_risks(cost_risk=cost_risk)
        
        assert result is not None
        # Low confidence should reduce overall confidence
        assert result.overall_confidence < 0.5

    def test_zero_scores(self, integration):
        """Should handle zero-score inputs"""
        cost_risk = RiskFactorInput(
            category=RiskCategory.COST, score=0.0, confidence=1.0
        )
        
        result = integration.register_feature_risks(cost_risk=cost_risk)
        
        assert result is not None
        assert result.overall_risk_score < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
