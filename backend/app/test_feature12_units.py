"""
Feature 12: Portfolio Intelligence - Unit Tests
Tests for aggregation, intelligence, and integration components.
"""

import unittest
from datetime import datetime, timedelta
from typing import List

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    RiskDriver,
    ExecutiveSummary,
    PortfolioTrendData,
    DashboardDataContract,
    RiskLevel,
    PortfolioViewType,
    AggregationConfig,
)
from feature12_aggregation_service import PortfolioAggregationService
from feature12_intelligence_engine import (
    ExecutiveIntelligenceEngine,
    TrendDirection,
    RecommendationPriority,
)
from feature12_integrations import (
    Feature9RiskIntegration,
    Feature10RecommendationsIntegration,
    Feature11AllocationIntegration,
    MondayComIntegrator,
    CrossFeatureIntegrator,
)


class TestPortfolioAggregationService(unittest.TestCase):
    """Unit tests for PortfolioAggregationService"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.service = PortfolioAggregationService()
        self.config = AggregationConfig()
    
    def create_test_project(
        self,
        project_id: str,
        client: str = "Test Client",
        region: str = "North",
        budget: float = 100000.0,
        risk_scores: dict = None,
    ) -> ProjectSnapshot:
        """Helper to create test project snapshot"""
        
        if risk_scores is None:
            risk_scores = {
                "delay": 0.3,
                "cost": 0.3,
                "resource": 0.2,
                "safety": 0.1,
                "overall": 0.5,
            }
        
        return ProjectSnapshot(
            project_id=project_id,
            project_name=f"Project {project_id}",
            client=client,
            region=region,
            program="Test Program",
            division="Test Division",
            current_budget=budget,
            original_budget=budget,
            current_cost=budget * 0.4,
            forecasted_final_cost=budget * 0.85,
            original_end_date=datetime.now() + timedelta(days=30),
            current_end_date=datetime.now() + timedelta(days=35),
            delay_risk_score=risk_scores["delay"],
            cost_risk_score=risk_scores["cost"],
            resource_risk_score=risk_scores["resource"],
            safety_risk_score=risk_scores["safety"],
            overall_risk_score=risk_scores["overall"],
            total_tasks=100,
            completed_tasks=40,
            unallocated_tasks=10,
            total_workers=15,
            average_worker_reliability=0.78,
            last_updated=datetime.now(),
            data_confidence=0.85,
        )
    
    def test_aggregate_single_project(self):
        """Test aggregation of single project"""
        
        project = self.create_test_project("P001", "Client A", "North", 100000)
        
        exposure = self.service.aggregate_portfolio(
            portfolio_id="PORT001",
            projects=[project],
            view_type=PortfolioViewType.CLIENT,
        )
        
        self.assertEqual(exposure.portfolio_id, "PORT001")
        self.assertEqual(exposure.total_projects, 1)
        self.assertEqual(exposure.total_budget, 100000)
        self.assertGreater(exposure.portfolio_risk_score, 0)
        self.assertLess(exposure.portfolio_risk_score, 1)
    
    def test_aggregate_multiple_projects_by_client(self):
        """Test aggregation of multiple projects grouped by client"""
        
        projects = [
            self.create_test_project("P001", "Client A", "North", 100000, {"delay": 0.2, "cost": 0.2, "resource": 0.1, "safety": 0.1, "overall": 0.4}),
            self.create_test_project("P002", "Client A", "North", 150000, {"delay": 0.4, "cost": 0.4, "resource": 0.3, "safety": 0.2, "overall": 0.6}),
            self.create_test_project("P003", "Client B", "South", 80000, {"delay": 0.3, "cost": 0.3, "resource": 0.2, "safety": 0.1, "overall": 0.5}),
        ]
        
        exposure = self.service.aggregate_portfolio(
            portfolio_id="PORT001",
            projects=projects,
            view_type=PortfolioViewType.CLIENT,
        )
        
        self.assertEqual(exposure.total_projects, 3)
        self.assertEqual(exposure.total_budget, 330000)
        self.assertGreater(len(exposure.critical_projects) + len(exposure.at_risk_projects) + len(exposure.healthy_projects), 0)
    
    def test_risk_level_determination(self):
        """Test risk level determination based on score"""
        
        # Low risk project
        low_risk = self.create_test_project("P001", risk_scores={"delay": 0.1, "cost": 0.1, "resource": 0.1, "safety": 0.05, "overall": 0.15})
        
        exposure = self.service.aggregate_portfolio(
            portfolio_id="PORT001",
            projects=[low_risk],
        )
        
        self.assertEqual(exposure.risk_level, RiskLevel.LOW)
        self.assertLess(exposure.portfolio_risk_score, self.config.risk_score_threshold_medium)
    
    def test_aggregate_empty_portfolio(self):
        """Test aggregation with no projects"""
        
        exposure = self.service.aggregate_portfolio(
            portfolio_id="PORT001",
            projects=[],
        )
        
        self.assertEqual(exposure.total_projects, 0)
        self.assertEqual(exposure.portfolio_risk_score, 0.0)
        self.assertEqual(exposure.risk_level, RiskLevel.LOW)
    
    def test_identify_risk_drivers(self):
        """Test identification of systemic risk drivers"""
        
        # Create projects with schedule delays
        delayed_projects = [
            self.create_test_project(
                f"P{i:03d}",
                f"Client {chr(65 + i)}",
                budget=100000,
                risk_scores={"delay": 0.7, "cost": 0.5, "resource": 0.3, "safety": 0.1, "overall": 0.6},
            )
            for i in range(3)
        ]
        
        exposure = self.service.aggregate_portfolio("PORT001", delayed_projects)
        drivers = self.service.identify_risk_drivers("PORT001", exposure, delayed_projects)
        
        self.assertGreater(len(drivers), 0)
        # Should identify delay driver
        delay_drivers = [d for d in drivers if "delay" in d.driver_name.lower()]
        self.assertGreater(len(delay_drivers), 0)
    
    def test_confidence_scoring(self):
        """Test confidence score calculation"""
        
        # High confidence project
        high_conf = self.create_test_project("P001")
        high_conf.data_confidence = 0.95
        
        exposure = self.service.aggregate_portfolio("PORT001", [high_conf])
        
        self.assertGreater(exposure.confidence_score, 0.85)


class TestExecutiveIntelligenceEngine(unittest.TestCase):
    """Unit tests for ExecutiveIntelligenceEngine"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.engine = ExecutiveIntelligenceEngine()
    
    def create_test_exposure(
        self,
        portfolio_id: str = "PORT001",
        risk_score: float = 0.5,
        critical_count: int = 0,
        at_risk_count: int = 2,
    ) -> PortfolioRiskExposure:
        """Helper to create test exposure"""
        
        return PortfolioRiskExposure(
            portfolio_id=portfolio_id,
            view_type=PortfolioViewType.CLIENT,
            grouping_key="Test Client",
            portfolio_risk_score=risk_score,
            risk_level=RiskLevel.MEDIUM if risk_score > 0.5 else RiskLevel.LOW,
            delay_risk_score=0.3,
            cost_risk_score=0.3,
            resource_risk_score=0.2,
            safety_risk_score=0.1,
            compliance_risk_score=0.05,
            critical_projects=["P001", "P002"][:critical_count],
            at_risk_projects=[f"P{i:03d}" for i in range(at_risk_count)],
            healthy_projects=[f"P{i+100:03d}" for i in range(5)],
            total_projects=10,
            total_budget=1000000,
            total_cost_to_date=400000,
            forecasted_total_cost=950000,
            total_schedule_variance_days=15,
            total_cost_variance=0.05,
            average_workforce_reliability=0.78,
            total_resource_gaps=5,
            risk_trend="stable",
            risk_trend_magnitude=0.01,
            project_count_in_calc=10,
            confidence_score=0.85,
        )
    
    def test_generate_trends(self):
        """Test trend generation"""
        
        exposure = self.create_test_exposure(risk_score=0.45)
        
        trends = self.engine.generate_trends(
            portfolio_id="PORT001",
            current_exposure=exposure,
            time_period="weekly",
        )
        
        self.assertEqual(trends.portfolio_id, "PORT001")
        self.assertEqual(trends.risk_score, 0.45)
        self.assertIsNotNone(trends.trend_direction)
        self.assertIsNotNone(trends.projected_score)
    
    def test_period_comparison(self):
        """Test period-over-period comparison"""
        
        prev_exposure = self.create_test_exposure(risk_score=0.50)
        curr_exposure = self.create_test_exposure(risk_score=0.45)
        
        comparison = self.engine.generate_period_comparison(
            portfolio_id="PORT001",
            current_exposure=curr_exposure,
            previous_exposure=prev_exposure,
        )
        
        self.assertLess(comparison.risk_score_change, 0)  # Should be improving
        self.assertEqual(comparison.risk_level_change, "improved")
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        
        exposure = self.create_test_exposure(
            risk_score=0.65,
            critical_count=2,
            at_risk_count=3,
        )
        
        drivers = [
            RiskDriver(
                driver_id="DRV001",
                driver_name="Test Risk Driver",
                description="Test driver description",
                risk_category="delay",
                affected_project_count=3,
                total_impact_weight=0.4,
                percentage_of_portfolio_risk=0.4 / 0.65,
                affected_projects=[("P001", 0.7), ("P002", 0.6)],
                examples=["P001 delayed 10 days", "P002 delayed 8 days"],
                trend="degrading",
            ),
        ]
        
        recommendations = self.engine.generate_recommendations(
            portfolio_id="PORT001",
            exposure=exposure,
            drivers=drivers,
            projects=[],
        )
        
        self.assertGreater(len(recommendations), 0)
        # Should have critical recommendation
        critical_recs = [r for r in recommendations if r.get("priority") == RecommendationPriority.CRITICAL.value]
        self.assertGreater(len(critical_recs), 0)
    
    def test_portfolio_insights(self):
        """Test portfolio insights generation"""
        
        exposure = self.create_test_exposure(risk_score=0.55)
        summary = ExecutiveSummary(
            portfolio_id="PORT001",
            report_date=datetime.now(),
            report_period="weekly",
            project_count=10,
            portfolio_health_score=60.0,
            overall_risk_level=RiskLevel.MEDIUM,
            headline="Test portfolio headline",
            key_findings=["Finding 1", "Finding 2"],
            top_risks=["Risk 1", "Risk 2"],
            on_time_projects=5,
            delayed_projects=3,
            over_budget_projects=2,
            critical_risk_projects=0,
            total_portfolio_value=1000000,
            cumulative_at_risk_value=150000,
        )
        
        drivers = []
        
        insights = self.engine.get_portfolio_insights(
            portfolio_id="PORT001",
            exposure=exposure,
            summary=summary,
            drivers=drivers,
        )
        
        self.assertEqual(insights["portfolio_id"], "PORT001")
        self.assertIn("executive_summary", insights)
        self.assertIn("portfolio_metrics", insights)
        self.assertIn("risk_breakdown", insights)


class TestFeatureIntegrations(unittest.TestCase):
    """Unit tests for feature integration components"""
    
    def test_feature9_risk_integration(self):
        """Test Feature 9 risk data integration"""
        
        feature9_data = {
            "project_id": "P001",
            "risk_score": 0.6,
            "delay_risk": 0.4,
            "cost_risk": 0.3,
            "resource_risk": 0.2,
            "safety_risk": 0.1,
            "compliance_risk": 0.05,
            "risk_drivers": ["Schedule pressure", "Resource shortage"],
            "confidence": 0.85,
        }
        
        normalized = Feature9RiskIntegration.ingest_feature9_risk_scores(feature9_data)
        
        self.assertEqual(normalized["project_id"], "P001")
        self.assertEqual(normalized["overall_risk_score"], 0.6)
        self.assertGreater(len(normalized["risk_drivers"]), 0)
        self.assertGreater(normalized["confidence"], 0.8)
    
    def test_feature10_recommendations_integration(self):
        """Test Feature 10 recommendations integration"""
        
        feature10_data = {
            "project_id": "P001",
            "recommendations": [
                {"title": "Increase resources", "urgency": "critical", "impact": "high"},
                {"title": "Adjust schedule", "urgency": "high", "impact": "medium"},
            ],
        }
        
        normalized = Feature10RecommendationsIntegration.ingest_feature10_recommendations(feature10_data)
        
        self.assertEqual(normalized["project_id"], "P001")
        self.assertEqual(normalized["total_recommendations"], 2)
        self.assertEqual(normalized["critical_count"], 1)
        self.assertIsNotNone(normalized["top_recommendation"])
    
    def test_feature11_allocation_integration(self):
        """Test Feature 11 allocation integration"""
        
        feature11_data = {
            "project_id": "P001",
            "allocations": [
                {"task_id": "T001", "capacity_used": 50},
                {"task_id": "T002", "capacity_used": 50},
            ],
            "tasks": [
                {"id": "T001", "allocated": True},
                {"id": "T002", "allocated": True},
                {"id": "T003", "allocated": False},
            ],
            "resources": [
                {"id": "R001", "capacity": 100},
            ],
            "optimization_recommendations": ["Hire temporary staff"],
        }
        
        normalized = Feature11AllocationIntegration.ingest_feature11_allocations(feature11_data)
        
        self.assertEqual(normalized["project_id"], "P001")
        self.assertEqual(normalized["total_tasks"], 3)
        self.assertEqual(normalized["allocated_tasks"], 2)
        self.assertEqual(normalized["unallocated_tasks"], 1)
    
    def test_monday_format_conversion(self):
        """Test Monday.com format conversion"""
        
        contract = DashboardDataContract(
            portfolio_id="PORT001",
            portfolio_name="Test Portfolio",
            summary_metrics={
                "health_score": 75.0,
                "risk_score": 0.45,
                "total_projects": 10,
            },
        )
        
        monday_data = MondayComIntegrator.convert_to_monday_format(contract)
        
        self.assertIsNotNone(monday_data)
        self.assertIn("portfolio_id", monday_data)
        self.assertEqual(monday_data["portfolio_id"], "PORT001")
    
    def test_dashboard_structure_creation(self):
        """Test Monday.com dashboard structure creation"""
        
        structure = MondayComIntegrator.create_portfolio_dashboard_structure(
            portfolio_id="PORT001",
            portfolio_name="North Region",
            is_summary=False,
        )
        
        self.assertEqual(structure["board_name"], "Portfolio: North Region")
        self.assertGreater(len(structure["widgets"]), 0)
        self.assertTrue(structure["no_api_required"])


class TestConfidenceAndQuality(unittest.TestCase):
    """Unit tests for confidence and quality metrics"""
    
    def test_confidence_propagation(self):
        """Test that confidence scores propagate correctly"""
        
        service = PortfolioAggregationService()
        
        high_conf_project = TestPortfolioAggregationService().create_test_project("P001")
        high_conf_project.data_confidence = 0.95
        
        exposure = service.aggregate_portfolio("PORT001", [high_conf_project])
        
        self.assertGreater(exposure.confidence_score, 0.85)
    
    def test_stale_data_handling(self):
        """Test handling of stale project data"""
        
        service = PortfolioAggregationService()
        
        stale_project = TestPortfolioAggregationService().create_test_project("P001")
        stale_project.last_updated = datetime.now() - timedelta(days=10)
        stale_project.data_confidence = 0.85
        
        exposure = service.aggregate_portfolio("PORT001", [stale_project])
        
        # Confidence should be reduced due to staleness
        self.assertLess(exposure.confidence_score, stale_project.data_confidence)


if __name__ == "__main__":
    unittest.main()
