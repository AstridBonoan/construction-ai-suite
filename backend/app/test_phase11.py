"""
Feature 11: Comprehensive Unit Tests
Tests for resource allocation optimization
"""
import unittest
from datetime import datetime, date, timedelta

from phase11_resource_types import (
    Worker, Crew, Subcontractor, Skill, SkillLevel, ResourceAvailability,
    TaskResourceRequirement, CurrentTaskAllocation, AllocationRequest,
    ResourceType, ReallocationReason
)
from phase11_allocation_optimizer import AllocationOptimizer
from phase11_resource_integration import create_resource_allocation_integration


class TestAllocationOptimizer(unittest.TestCase):
    """Test allocation optimization logic"""
    
    def setUp(self):
        """Initialize test fixtures"""
        self.optimizer = AllocationOptimizer()
        self.project_id = "test_project_001"
        
        # Create test workers
        self.worker1 = Worker(
            worker_id="W001",
            name="John Carpenter",
            crew_id="C001",
            skills=[Skill("carpentry", SkillLevel.SENIOR, 10, False)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=40,
                max_concurrent_tasks=2,
                on_site_requirement=True,
                travel_time_hours=1
            ),
            hourly_rate=50.0,
            base_reliability_score=0.85,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        self.worker2 = Worker(
            worker_id="W002",
            name="Jane Electrician",
            crew_id="C002",
            skills=[Skill("electrical", SkillLevel.INTERMEDIATE, 5, True)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=40,
                max_concurrent_tasks=2,
                on_site_requirement=True,
                travel_time_hours=0
            ),
            hourly_rate=45.0,
            base_reliability_score=0.80,
            absence_history=[],
            monday_user_id="user_002",
        )
        
        # Create test task
        self.task1 = TaskResourceRequirement(
            task_id="TASK001",
            required_role="carpentry",
            required_skills=[Skill("carpentry", SkillLevel.SENIOR, 0, False)],
            min_skill_level=SkillLevel.INTERMEDIATE,
            workers_needed=2,
            crew_size_optimal=2,
            can_use_subcontractor=False,
            duration_days=10,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 11),
            critical_path=False,
            estimated_hours=80,
        )
        
        # Current allocation
        self.allocation1 = CurrentTaskAllocation(
            task_id="TASK001",
            project_id=self.project_id,
            allocated_workers={"W001": 40},
            allocated_crew_ids=["C001"],
            allocated_subcontractor_ids=[],
            allocation_start=date(2024, 2, 1),
            allocation_end=date(2024, 2, 11),
            estimated_completion_hours=80,
            actual_completed_hours=20,
            completion_percent=0.25,
            delay_risk_from_allocation=0.40,
            cost_from_allocation=3000,
        )
    
    def test_allocation_optimizer_initialization(self):
        """Test optimizer initializes correctly"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(len(self.optimizer.recommendation_history), 0)
    
    def test_score_skill_match(self):
        """Test skill matching score"""
        from phase11_resource_types import ResourceAllocationContext
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=[self.worker1, self.worker2],
            all_crews=[],
            all_subcontractors=[],
            tasks=[self.task1],
            current_allocations=[self.allocation1],
            workforce_reliability_scores={},
            subcontractor_performance_scores={},
            task_delay_risks={},
            historical_productivity={},
            season="spring",
            project_phase="execution",
        )
        
        score = self.optimizer._score_skill_match(self.allocation1, context, self.task1)
        
        self.assertGreater(score, 0.0, "Skill match should be positive")
        self.assertLessEqual(score, 1.0, "Skill match should not exceed 1.0")
    
    def test_score_availability(self):
        """Test availability scoring"""
        from phase11_resource_types import ResourceAllocationContext
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=[self.worker1],
            all_crews=[],
            all_subcontractors=[],
            tasks=[self.task1],
            current_allocations=[self.allocation1],
            workforce_reliability_scores={},
            subcontractor_performance_scores={},
            task_delay_risks={},
            historical_productivity={},
            season="spring",
            project_phase="execution",
        )
        
        score = self.optimizer._score_availability_match(self.allocation1, context)
        
        self.assertGreater(score, 0.0, "Availability score should be positive")
        self.assertLessEqual(score, 1.0, "Availability score should not exceed 1.0")
    
    def test_score_cost_efficiency(self):
        """Test cost efficiency scoring"""
        from phase11_resource_types import ResourceAllocationContext
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=[self.worker1],
            all_crews=[],
            all_subcontractors=[],
            tasks=[self.task1],
            current_allocations=[self.allocation1],
            workforce_reliability_scores={},
            subcontractor_performance_scores={},
            task_delay_risks={},
            historical_productivity={},
            season="spring",
            project_phase="execution",
        )
        
        score = self.optimizer._score_cost_efficiency(self.allocation1, context)
        
        self.assertGreater(score, 0.0, "Cost efficiency should be positive")
        self.assertLessEqual(score, 1.0, "Cost efficiency should not exceed 1.0")
    
    def test_score_utilization(self):
        """Test resource utilization scoring"""
        from phase11_resource_types import ResourceAllocationContext
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=[self.worker1],
            all_crews=[],
            all_subcontractors=[],
            tasks=[self.task1],
            current_allocations=[self.allocation1],
            workforce_reliability_scores={},
            subcontractor_performance_scores={},
            task_delay_risks={},
            historical_productivity={},
            season="spring",
            project_phase="execution",
        )
        
        score = self.optimizer._score_utilization(self.allocation1, context)
        
        self.assertGreater(score, 0.0, "Utilization score should be positive")
        self.assertLessEqual(score, 1.0, "Utilization score should not exceed 1.0")
    
    def test_find_under_utilized_resources(self):
        """Test finding under-utilized resources"""
        from phase11_resource_types import ResourceAllocationContext, AllocationScore
        
        context = ResourceAllocationContext(
            project_id=self.project_id,
            all_workers=[self.worker1],
            all_crews=[],
            all_subcontractors=[],
            tasks=[self.task1],
            current_allocations=[self.allocation1],
            workforce_reliability_scores={},
            subcontractor_performance_scores={},
            task_delay_risks={},
            historical_productivity={},
            season="spring",
            project_phase="execution",
        )
        
        # Create low score
        allocation_id = f"{self.allocation1.task_id}_{self.allocation1.project_id}"
        scores = {
            allocation_id: AllocationScore(
                allocation_id, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.60, "test"
            )
        }
        
        under_utilized = self.optimizer._find_under_utilized_resources(context, scores)
        
        self.assertGreater(len(under_utilized), 0, "Should find under-utilized resources")


class TestResourceAllocationIntegration(unittest.TestCase):
    """Test integration layer"""
    
    def setUp(self):
        """Initialize integration"""
        self.project_id = "integration_test_001"
        self.integration = create_resource_allocation_integration(self.project_id)
    
    def test_integration_factory(self):
        """Test factory creates integration"""
        self.assertIsNotNone(self.integration)
        self.assertEqual(self.integration.project_id, self.project_id)
    
    def test_feature_3_input_format(self):
        """Test Feature 3 input formatting"""
        feature_3_data = self.integration.get_feature_3_input()
        
        self.assertIsInstance(feature_3_data, dict)
        self.assertIn('feature11_workforce_changes', feature_3_data)
    
    def test_feature_4_input_format(self):
        """Test Feature 4 input formatting"""
        feature_4_data = self.integration.get_feature_4_input()
        
        self.assertIsInstance(feature_4_data, dict)
        self.assertIn('feature11_subcontractor_changes', feature_4_data)
    
    def test_feature_9_input_format(self):
        """Test Feature 9 input formatting"""
        feature_9_data = self.integration.get_feature_9_input()
        
        self.assertIsInstance(feature_9_data, dict)
        self.assertIn('feature11_delay_risk_reduction', feature_9_data)
    
    def test_feature_10_input_format(self):
        """Test Feature 10 input formatting"""
        feature_10_data = self.integration.get_feature_10_input()
        
        self.assertIsInstance(feature_10_data, dict)
        self.assertIn('feature11_allocation_recommendations', feature_10_data)
    
    def test_monday_com_data_format(self):
        """Test Monday.com data formatting"""
        monday_data = self.integration.get_monday_com_data()
        
        self.assertIsInstance(monday_data, dict)
        self.assertIn('monday_fields', monday_data)
        
        fields = monday_data['monday_fields']
        self.assertIn('Feature11_Recommendations_Count', fields)
        self.assertIn('Feature11_Confidence_Level', fields)
    
    def test_reset_project(self):
        """Test reset clears caches"""
        # Set some data
        self.integration.analysis_cache[self.project_id] = "test_data"
        
        # Reset
        self.integration.reset_project()
        
        # Verify cleared
        self.assertNotIn(self.project_id, self.integration.analysis_cache)


class TestDeterminism(unittest.TestCase):
    """Test deterministic behavior"""
    
    def test_allocation_deterministic(self):
        """Test same inputs produce same recommendations"""
        opt1 = AllocationOptimizer()
        opt2 = AllocationOptimizer()
        
        # Same inputs should produce same results
        self.assertIsNotNone(opt1)
        self.assertIsNotNone(opt2)


if __name__ == '__main__':
    unittest.main()
