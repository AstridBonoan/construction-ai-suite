"""
Feature 12: Portfolio Intelligence - Integration Tests
End-to-end tests with multiple projects and cross-feature scenarios.
"""

import unittest
from datetime import datetime, timedelta
from typing import List

from feature12_portfolio_models import (
    ProjectSnapshot,
    PortfolioRiskExposure,
    RiskLevel,
    PortfolioViewType,
    AggregationConfig,
)
from feature12_aggregation_service import PortfolioAggregationService
from feature12_intelligence_engine import ExecutiveIntelligenceEngine
from feature12_integrations import (
    Feature9RiskIntegration,
    Feature10RecommendationsIntegration,
    Feature11AllocationIntegration,
    CrossFeatureIntegrator,
)


class TestPortfolioIntegrationScenarios(unittest.TestCase):
    """Integration tests with realistic portfolio scenarios"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.aggregation_service = PortfolioAggregationService()
        self.intelligence_engine = ExecutiveIntelligenceEngine()
        self.config = AggregationConfig()
    
    def create_multi_project_portfolio(
        self,
        client_name: str,
        num_projects: int = 5,
        risk_profile: str = "balanced",
    ) -> List[ProjectSnapshot]:
        """Create a portfolio of projects with specified risk profile"""
        
        projects = []
        base_date = datetime.now()
        
        risk_profiles = {
            "balanced": [
                {"delay": 0.3, "cost": 0.3, "resource": 0.2, "safety": 0.1, "overall": 0.50},
                {"delay": 0.2, "cost": 0.2, "resource": 0.1, "safety": 0.05, "overall": 0.35},
                {"delay": 0.4, "cost": 0.4, "resource": 0.3, "safety": 0.15, "overall": 0.65},
                {"delay": 0.25, "cost": 0.25, "resource": 0.15, "safety": 0.1, "overall": 0.45},
                {"delay": 0.35, "cost": 0.35, "resource": 0.25, "safety": 0.12, "overall": 0.55},
            ],
            "high_risk": [
                {"delay": 0.7, "cost": 0.6, "resource": 0.5, "safety": 0.3, "overall": 0.80},
                {"delay": 0.75, "cost": 0.65, "resource": 0.55, "safety": 0.35, "overall": 0.85},
                {"delay": 0.65, "cost": 0.6, "resource": 0.45, "safety": 0.25, "overall": 0.75},
                {"delay": 0.7, "cost": 0.65, "resource": 0.5, "safety": 0.3, "overall": 0.80},
                {"delay": 0.68, "cost": 0.62, "resource": 0.48, "safety": 0.28, "overall": 0.78},
            ],
            "mixed": [
                {"delay": 0.15, "cost": 0.15, "resource": 0.1, "safety": 0.05, "overall": 0.25},  # Healthy
                {"delay": 0.45, "cost": 0.4, "resource": 0.3, "safety": 0.15, "overall": 0.6},  # At risk
                {"delay": 0.75, "cost": 0.7, "resource": 0.6, "safety": 0.4, "overall": 0.85},  # Critical
                {"delay": 0.2, "cost": 0.2, "resource": 0.15, "safety": 0.1, "overall": 0.4},  # Healthy
                {"delay": 0.5, "cost": 0.45, "resource": 0.35, "safety": 0.2, "overall": 0.65},  # At risk
            ],
        }
        
        profile = risk_profiles.get(risk_profile, risk_profiles["balanced"])
        
        for i in range(min(num_projects, len(profile))):
            budget = 100000 + (i * 50000)
            scores = profile[i]
            
            project = ProjectSnapshot(
                project_id=f"{client_name}_P{i+1:03d}",
                project_name=f"{client_name} Project {i+1}",
                client=client_name,
                region=["North", "South", "East", "West"][i % 4],
                program=f"Program {(i // 2) + 1}",
                division=f"Division {(i // 3) + 1}",
                current_budget=budget,
                original_budget=budget,
                current_cost=budget * (0.3 + i * 0.05),
                forecasted_final_cost=budget * (0.8 + i * 0.05),
                original_end_date=base_date + timedelta(days=60),
                current_end_date=base_date + timedelta(days=60 + i * 5),
                delay_risk_score=scores["delay"],
                cost_risk_score=scores["cost"],
                resource_risk_score=scores["resource"],
                safety_risk_score=scores["safety"],
                overall_risk_score=scores["overall"],
                total_tasks=100 + i * 20,
                completed_tasks=30 + i * 10,
                unallocated_tasks=int((50 + i * 5) * (scores["resource"] / 0.5)),
                total_workers=10 + i,
                average_worker_reliability=0.75 + (0.1 * (1 - scores["resource"])),
                last_updated=datetime.now(),
                data_confidence=0.8 + (0.1 * (1 - scores["overall"])),
            )
            projects.append(project)
        
        return projects
    
    def test_scenario_single_client_portfolio(self):
        """Test portfolio aggregation for single client with multiple projects"""
        
        projects = self.create_multi_project_portfolio("Client A", num_projects=5, risk_profile="balanced")
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_CLIENT_A",
            projects=projects,
            view_type=PortfolioViewType.CLIENT,
        )
        
        # Assertions
        self.assertEqual(exposure.total_projects, 5)
        self.assertGreater(exposure.total_budget, 0)
        self.assertGreater(len(exposure.critical_projects) + len(exposure.at_risk_projects), 0)
        self.assertLessEqual(exposure.portfolio_risk_score, 1.0)
        self.assertGreaterEqual(exposure.portfolio_risk_score, 0.0)
    
    def test_scenario_multi_client_aggregation(self):
        """Test aggregation across multiple clients"""
        
        # Create portfolios for 3 clients
        clients_data = {
            "Client A": self.create_multi_project_portfolio("Client A", 3, "balanced"),
            "Client B": self.create_multi_project_portfolio("Client B", 3, "high_risk"),
            "Client C": self.create_multi_project_portfolio("Client C", 3, "mixed"),
        }
        
        # Aggregate each client
        client_exposures = {}
        for client, projects in clients_data.items():
            exposure = self.aggregation_service.aggregate_portfolio(
                portfolio_id=f"PORT_{client.replace(' ', '_')}",
                projects=projects,
                view_type=PortfolioViewType.CLIENT,
            )
            client_exposures[client] = exposure
        
        # Verify expected risk levels
        self.assertLess(client_exposures["Client A"].portfolio_risk_score, 0.6)
        self.assertGreater(client_exposures["Client B"].portfolio_risk_score, 0.7)
        
        # High-risk client B should have more critical projects
        self.assertGreater(len(client_exposures["Client B"].critical_projects), 
                          len(client_exposures["Client A"].critical_projects))
    
    def test_scenario_regional_aggregation(self):
        """Test aggregation by region"""
        
        projects = self.create_multi_project_portfolio("Multi-Region", num_projects=5)
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_REGIONS",
            projects=projects,
            view_type=PortfolioViewType.REGION,
        )
        
        self.assertEqual(exposure.total_projects, 5)
        # Regional view should still aggregate all projects
        self.assertGreater(exposure.total_budget, 0)
    
    def test_scenario_risk_driver_detection(self):
        """Test systemic risk driver detection in portfolio"""
        
        # Create portfolio with systemic delay issues
        projects = self.create_multi_project_portfolio("Delayed Client", num_projects=4, risk_profile="high_risk")
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_DELAYED",
            projects=projects,
        )
        
        drivers = self.aggregation_service.identify_risk_drivers(
            portfolio_id="PORT_DELAYED",
            exposure=exposure,
            projects=projects,
        )
        
        # Should detect multiple drivers
        self.assertGreater(len(drivers), 0)
        
        # Should identify delay risk as primary driver (high_risk profile)
        delay_drivers = [d for d in drivers if "delay" in d.driver_name.lower() or "schedule" in d.driver_name.lower()]
        self.assertGreater(len(delay_drivers), 0)
    
    def test_scenario_critical_vs_healthy_projects(self):
        """Test classification of projects by health"""
        
        projects = self.create_multi_project_portfolio("Mixed Health", num_projects=5, risk_profile="mixed")
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_MIXED",
            projects=projects,
        )
        
        # Mixed portfolio should have all three categories
        self.assertGreater(len(exposure.critical_projects), 0)
        self.assertGreater(len(exposure.at_risk_projects), 0)
        self.assertGreater(len(exposure.healthy_projects), 0)
        
        # Total should equal project count
        total_classified = len(exposure.critical_projects) + len(exposure.at_risk_projects) + len(exposure.healthy_projects)
        self.assertEqual(total_classified, exposure.total_projects)
    
    def test_scenario_executive_summary_generation(self):
        """Test end-to-end executive summary generation"""
        
        projects = self.create_multi_project_portfolio("Client X", num_projects=5, risk_profile="mixed")
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_CLIENT_X",
            projects=projects,
        )
        
        drivers = self.aggregation_service.identify_risk_drivers(
            portfolio_id="PORT_CLIENT_X",
            exposure=exposure,
            projects=projects,
        )
        
        summary = self.aggregation_service.generate_executive_summary(
            portfolio_id="PORT_CLIENT_X",
            exposure=exposure,
            drivers=drivers,
            projects=projects,
        )
        
        # Verify summary structure
        self.assertIsNotNone(summary.headline)
        self.assertGreater(len(summary.key_findings), 0)
        self.assertGreater(len(summary.top_risks), 0)
        self.assertGreaterEqual(summary.portfolio_health_score, 0)
        self.assertLessEqual(summary.portfolio_health_score, 100)
    
    def test_scenario_trend_analysis(self):
        """Test trend analysis over time"""
        
        projects = self.create_multi_project_portfolio("Trending", num_projects=3)
        
        # First exposure
        exposure1 = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_TREND",
            projects=projects,
        )
        
        # Simulate project deterioration
        for project in projects:
            project.overall_risk_score = min(1.0, project.overall_risk_score + 0.1)
            project.delay_risk_score = min(1.0, project.delay_risk_score + 0.1)
        
        # Second exposure
        exposure2 = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_TREND",
            projects=projects,
        )
        
        # Generate trend
        trends = self.intelligence_engine.generate_trends(
            portfolio_id="PORT_TREND",
            current_exposure=exposure2,
            time_period="weekly",
            comparison_exposures=[exposure1, exposure2],
        )
        
        # Risk should be increasing
        self.assertGreater(exposure2.portfolio_risk_score, exposure1.portfolio_risk_score)
        self.assertEqual(trends.portfolio_id, "PORT_TREND")
    
    def test_scenario_period_comparison(self):
        """Test period-over-period comparison"""
        
        projects_prev = self.create_multi_project_portfolio("Period Test", num_projects=4, risk_profile="balanced")
        projects_curr = self.create_multi_project_portfolio("Period Test", num_projects=4, risk_profile="mixed")
        
        exposure_prev = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_PERIOD",
            projects=projects_prev,
        )
        
        exposure_curr = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_PERIOD",
            projects=projects_curr,
        )
        
        comparison = self.intelligence_engine.generate_period_comparison(
            portfolio_id="PORT_PERIOD",
            current_exposure=exposure_curr,
            previous_exposure=exposure_prev,
        )
        
        # Verify comparison data
        self.assertEqual(comparison.portfolio_id, "PORT_PERIOD")
        self.assertIsNotNone(comparison.risk_level_change)
        self.assertGreater(len(comparison.key_changes), 0)
    
    def test_scenario_recommendations_generation(self):
        """Test comprehensive recommendation generation"""
        
        projects = self.create_multi_project_portfolio("Recommendations", num_projects=5, risk_profile="high_risk")
        
        exposure = self.aggregation_service.aggregate_portfolio(
            portfolio_id="PORT_RECS",
            projects=projects,
        )
        
        drivers = self.aggregation_service.identify_risk_drivers(
            portfolio_id="PORT_RECS",
            exposure=exposure,
            projects=projects,
        )
        
        recommendations = self.intelligence_engine.generate_recommendations(
            portfolio_id="PORT_RECS",
            exposure=exposure,
            drivers=drivers,
            projects=projects,
        )
        
        # Should generate actionable recommendations
        self.assertGreater(len(recommendations), 0)
        
        # Should have critical recommendations for high-risk portfolio
        critical_recs = [r for r in recommendations if r.get("priority") == "critical"]
        self.assertGreater(len(critical_recs), 0)
        
        # Each recommendation should have structure
        for rec in recommendations:
            self.assertIn("id", rec)
            self.assertIn("title", rec)
            self.assertIn("priority", rec)
            self.assertIn("recommended_actions", rec)


class TestCrossFeatureIntegrationFlow(unittest.TestCase):
    """Integration tests for cross-feature data flows"""
    
    def test_feature9_to_portfolio_flow(self):
        """Test data flow from Feature 9 to portfolio aggregation"""
        
        # Simulate Feature 9 output
        feature9_outputs = [
            {"project_id": "P001", "risk_score": 0.6, "delay_risk": 0.4, "confidence": 0.85},
            {"project_id": "P002", "risk_score": 0.5, "delay_risk": 0.3, "confidence": 0.80},
        ]
        
        # Ingest Feature 9 data
        ingested_risks = [
            Feature9RiskIntegration.ingest_feature9_risk_scores(f9)
            for f9 in feature9_outputs
        ]
        
        # Verify ingestion
        self.assertEqual(len(ingested_risks), 2)
        for risk in ingested_risks:
            self.assertIn("project_id", risk)
            self.assertGreater(risk["confidence"], 0)
    
    def test_feature10_to_portfolio_flow(self):
        """Test data flow from Feature 10 to portfolio aggregation"""
        
        # Simulate Feature 10 output
        feature10_outputs = [
            {
                "project_id": "P001",
                "recommendations": [
                    {"title": "Increase resources", "urgency": "critical"},
                    {"title": "Review schedule", "urgency": "high"},
                ]
            },
            {
                "project_id": "P002",
                "recommendations": [
                    {"title": "Risk mitigation", "urgency": "high"},
                ]
            },
        ]
        
        # Ingest Feature 10 data
        ingested_recs = [
            Feature10RecommendationsIntegration.ingest_feature10_recommendations(f10)
            for f10 in feature10_outputs
        ]
        
        # Synthesize portfolio recommendations
        portfolio_recs = Feature10RecommendationsIntegration.synthesize_portfolio_recommendations(ingested_recs)
        
        self.assertGreater(len(portfolio_recs), 0)
    
    def test_feature11_to_portfolio_flow(self):
        """Test data flow from Feature 11 to portfolio aggregation"""
        
        # Simulate Feature 11 output
        feature11_outputs = [
            {
                "project_id": "P001",
                "allocations": [{"task_id": "T001", "capacity_used": 50}],
                "tasks": [
                    {"id": "T001", "allocated": True},
                    {"id": "T002", "allocated": False},
                ],
                "resources": [{"id": "R001", "capacity": 100}],
            },
            {
                "project_id": "P002",
                "allocations": [{"task_id": "T003", "capacity_used": 60}],
                "tasks": [
                    {"id": "T003", "allocated": True},
                    {"id": "T004", "allocated": True},
                ],
                "resources": [{"id": "R002", "capacity": 100}],
            },
        ]
        
        # Ingest Feature 11 data
        ingested_allocs = [
            Feature11AllocationIntegration.ingest_feature11_allocations(f11)
            for f11 in feature11_outputs
        ]
        
        # Synthesize portfolio resource status
        portfolio_status = Feature11AllocationIntegration.synthesize_portfolio_resource_status(ingested_allocs)
        
        self.assertGreater(portfolio_status["allocation_rate"], 0)
        self.assertEqual(portfolio_status["unallocated_tasks"], 1)
    
    def test_integrated_context_building(self):
        """Test building integrated context from multiple features"""
        
        projects = [
            ProjectSnapshot(
                project_id="P001",
                project_name="Project 1",
                client="Client A",
                region="North",
                current_budget=100000,
                original_budget=100000,
                current_cost=40000,
                forecasted_final_cost=95000,
                original_end_date=datetime.now() + timedelta(days=30),
                current_end_date=datetime.now() + timedelta(days=35),
                delay_risk_score=0.3,
                cost_risk_score=0.3,
                resource_risk_score=0.2,
                safety_risk_score=0.1,
                overall_risk_score=0.5,
                total_tasks=100,
                completed_tasks=40,
                unallocated_tasks=10,
                total_workers=15,
                average_worker_reliability=0.78,
                last_updated=datetime.now(),
                data_confidence=0.85,
            ),
        ]
        
        feature9_data = [
            {"project_id": "P001", "risk_score": 0.5, "risk_drivers": ["Schedule risk"]},
        ]
        
        feature10_data = [
            {"project_id": "P001", "recommendations": [{"title": "Increase resources", "urgency": "high"}]},
        ]
        
        feature11_data = [
            {"project_id": "P001", "total_tasks": 100, "allocated_tasks": 90, "allocation_percentage": 90},
        ]
        
        # Build integrated context
        context = CrossFeatureIntegrator.build_integrated_context(
            project_snapshots=projects,
            feature9_risks=[f9 for f9 in feature9_data],
            feature10_recommendations=[f10 for f10 in feature10_data],
            feature11_allocations=[f11 for f11 in feature11_data],
        )
        
        self.assertEqual(context["project_count"], 1)
        self.assertGreater(len(context["feature_integrations"]), 0)
        self.assertIn("feature9_risk", context["feature_integrations"])
        self.assertIn("feature10_recommendations", context["feature_integrations"])
        self.assertIn("feature11_allocations", context["feature_integrations"])


if __name__ == "__main__":
    unittest.main()
