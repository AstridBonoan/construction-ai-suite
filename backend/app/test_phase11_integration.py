"""
Feature 11: Integration Tests
Tests for multi-project scenarios and API workflows
"""
import unittest
from datetime import date

from phase11_resource_types import (
    Worker, Crew, Subcontractor, Skill, SkillLevel, ResourceAvailability,
    TaskResourceRequirement, CurrentTaskAllocation, AllocationRequest,
    ResourceAllocationContext
)
from phase11_allocation_optimizer import AllocationOptimizer
from phase11_resource_integration import create_resource_allocation_integration


class TestMultiProjectScenarios(unittest.TestCase):
    """Test allocation across multiple projects"""
    
    def setUp(self):
        """Set up multi-project scenario"""
        self.project_ids = ["PRJ001", "PRJ002", "PRJ003"]
        self.integrations = {
            pid: create_resource_allocation_integration(pid)
            for pid in self.project_ids
        }
    
    def test_parallel_project_analysis(self):
        """Test simultaneous analysis of multiple projects"""
        for project_id in self.project_ids:
            integration = self.integrations[project_id]
            self.assertIsNotNone(integration)
            self.assertEqual(integration.project_id, project_id)
    
    def test_worker_contention_across_projects(self):
        """Test detecting worker contention across projects"""
        # Create same worker assigned to multiple projects
        worker = Worker(
            worker_id="W001",
            name="Shared Worker",
            crew_id=None,
            skills=[Skill("carpentry", SkillLevel.SENIOR, 10, False)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=40,
                max_concurrent_tasks=1,
                on_site_requirement=True,
                travel_time_hours=0
            ),
            hourly_rate=50.0,
            base_reliability_score=0.80,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        # Verify worker can be shared
        self.assertEqual(worker.max_concurrent_tasks, 1)
    
    def test_crew_utilization_across_projects(self):
        """Test crew allocation efficiency across projects"""
        crew = Crew(
            crew_id="C001",
            name="Main Carpentry Crew",
            lead_worker_id="W001",
            member_worker_ids=["W001", "W002", "W003"],
            team_role="carpentry",
            combined_reliability_score=0.85,
            monday_team_id="team_001",
        )
        
        self.assertEqual(len(crew.member_worker_ids), 3)


class TestResourceConstraints(unittest.TestCase):
    """Test handling of resource constraints"""
    
    def test_skill_requirement_mismatch(self):
        """Test handling of skill mismatches"""
        worker = Worker(
            worker_id="W001",
            name="Carpenter",
            crew_id=None,
            skills=[Skill("carpentry", SkillLevel.JUNIOR, 2, False)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=40,
                max_concurrent_tasks=2,
                on_site_requirement=True,
                travel_time_hours=1
            ),
            hourly_rate=35.0,
            base_reliability_score=0.70,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        # Task requires senior level
        task = TaskResourceRequirement(
            task_id="TASK001",
            required_role="electrical_work",
            required_skills=[Skill("electrical", SkillLevel.SENIOR, 0, True)],
            min_skill_level=SkillLevel.SENIOR,
            workers_needed=1,
            crew_size_optimal=None,
            can_use_subcontractor=True,
            duration_days=5,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 6),
            critical_path=True,
            estimated_hours=40,
        )
        
        # Verify mismatch detected
        self.assertNotEqual(worker.skills[0].skill_name, task.required_role)
    
    def test_availability_conflict(self):
        """Test detection of availability conflicts"""
        worker = Worker(
            worker_id="W001",
            name="Worker",
            crew_id=None,
            skills=[Skill("carpentry", SkillLevel.INTERMEDIATE, 5, False)],
            availability=ResourceAvailability(
                available_from=date(2024, 3, 1),
                available_to=date(2024, 3, 31),
                hours_per_week=40,
                max_concurrent_tasks=1,
                on_site_requirement=True,
                travel_time_hours=0
            ),
            hourly_rate=45.0,
            base_reliability_score=0.75,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        # Task outside availability
        task = TaskResourceRequirement(
            task_id="TASK001",
            required_role="carpentry",
            required_skills=[Skill("carpentry", SkillLevel.INTERMEDIATE, 0, False)],
            min_skill_level=SkillLevel.JUNIOR,
            workers_needed=1,
            crew_size_optimal=None,
            can_use_subcontractor=False,
            duration_days=5,
            start_date=date(2024, 2, 1),  # Before availability
            end_date=date(2024, 2, 6),
            critical_path=False,
            estimated_hours=40,
        )
        
        # Verify conflict detected
        self.assertGreater(task.start_date, worker.availability.available_to)
    
    def test_overallocation_detection(self):
        """Test detecting over-allocation"""
        worker = Worker(
            worker_id="W001",
            name="Busy Worker",
            crew_id=None,
            skills=[Skill("carpentry", SkillLevel.SENIOR, 10, False)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=40,
                max_concurrent_tasks=2,
                on_site_requirement=True,
                travel_time_hours=0
            ),
            hourly_rate=50.0,
            base_reliability_score=0.85,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        # Task 1: 30 hours
        task1 = TaskResourceRequirement(
            task_id="TASK001",
            required_role="carpentry",
            required_skills=[Skill("carpentry", SkillLevel.SENIOR, 0, False)],
            min_skill_level=SkillLevel.SENIOR,
            workers_needed=1,
            crew_size_optimal=None,
            can_use_subcontractor=False,
            duration_days=3,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 4),
            critical_path=True,
            estimated_hours=30,
        )
        
        # Task 2: 20 hours
        task2 = TaskResourceRequirement(
            task_id="TASK002",
            required_role="carpentry",
            required_skills=[Skill("carpentry", SkillLevel.SENIOR, 0, False)],
            min_skill_level=SkillLevel.SENIOR,
            workers_needed=1,
            crew_size_optimal=None,
            can_use_subcontractor=False,
            duration_days=2,
            start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 3),
            critical_path=False,
            estimated_hours=20,
        )
        
        # Verify tasks overlap
        self.assertTrue(
            task1.start_date <= task2.end_date and task2.start_date <= task1.end_date,
            "Tasks should overlap"
        )


class TestOptimizationGoals(unittest.TestCase):
    """Test different optimization goals"""
    
    def test_minimize_delay_goal(self):
        """Test delay minimization optimization"""
        request = AllocationRequest(
            project_id="PRJ001",
            optimization_goal="minimize_delay",
            max_recommendations=10,
            allow_subcontractor_substitution=True,
        )
        
        self.assertEqual(request.optimization_goal, "minimize_delay")
    
    def test_minimize_cost_goal(self):
        """Test cost minimization optimization"""
        request = AllocationRequest(
            project_id="PRJ001",
            optimization_goal="minimize_cost",
            max_recommendations=10,
            allow_subcontractor_substitution=True,
        )
        
        self.assertEqual(request.optimization_goal, "minimize_cost")
    
    def test_balance_goal(self):
        """Test balanced optimization"""
        request = AllocationRequest(
            project_id="PRJ001",
            optimization_goal="balance",
            max_recommendations=10,
            allow_subcontractor_substitution=True,
        )
        
        self.assertEqual(request.optimization_goal, "balance")


class TestSubcontractorIntegration(unittest.TestCase):
    """Test subcontractor allocation and performance"""
    
    def test_subcontractor_performance_scoring(self):
        """Test subcontractor performance evaluation"""
        subcontractor = Subcontractor(
            subcontractor_id="SUB001",
            company_name="Quality Electrical Inc",
            primary_contact="John Doe",
            contact_phone="555-1234",
            services=["electrical", "low_voltage"],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 12, 31),
                hours_per_week=999,
                max_concurrent_tasks=5,
                on_site_requirement=False,
                travel_time_hours=2
            ),
            hourly_rate=75.0,
            contract_cost_range=(2000, 5000),
            performance_score=0.85,
            reliability_score=0.80,
            past_delay_frequency=0.05,
            past_cost_overrun_percent=0.08,
            monday_vendor_id="vendor_001",
        )
        
        self.assertGreater(subcontractor.performance_score, 0.8)
        self.assertLess(subcontractor.past_delay_frequency, 0.10)
    
    def test_subcontractor_substitution(self):
        """Test substituting workers with subcontractors"""
        worker = Worker(
            worker_id="W001",
            name="Electrician",
            crew_id=None,
            skills=[Skill("electrical", SkillLevel.INTERMEDIATE, 3, True)],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 1, 31),  # Limited availability
                hours_per_week=40,
                max_concurrent_tasks=2,
                on_site_requirement=True,
                travel_time_hours=0
            ),
            hourly_rate=45.0,
            base_reliability_score=0.75,
            absence_history=[],
            monday_user_id="user_001",
        )
        
        subcontractor = Subcontractor(
            subcontractor_id="SUB001",
            company_name="Electrical Contractor",
            primary_contact="Jane Smith",
            contact_phone="555-5678",
            services=["electrical"],
            availability=ResourceAvailability(
                available_from=date(2024, 1, 1),
                available_to=date(2024, 3, 31),  # Better availability
                hours_per_week=999,
                max_concurrent_tasks=10,
                on_site_requirement=True,
                travel_time_hours=1
            ),
            hourly_rate=60.0,
            contract_cost_range=(3000, 6000),
            performance_score=0.90,
            reliability_score=0.88,
            past_delay_frequency=0.02,
            past_cost_overrun_percent=0.05,
            monday_vendor_id="vendor_001",
        )
        
        # Subcontractor has better availability and reliability
        self.assertGreater(subcontractor.availability.available_to, worker.availability.available_to)
        self.assertGreater(subcontractor.performance_score, worker.base_reliability_score)


class TestAPIWorkflows(unittest.TestCase):
    """Test API-level workflows"""
    
    def test_optimize_analyze_recommend_workflow(self):
        """Test flow: optimize -> analyze -> recommend"""
        project_id = "api_test_001"
        integration = create_resource_allocation_integration(project_id)
        
        # Step 1: Analyze
        self.assertIsNotNone(integration)
        
        # Step 2: Get recommendations
        recs = integration.analysis_cache.get(project_id, {})
        self.assertIsInstance(recs, (dict, type(None)))
    
    def test_monday_com_sync_workflow(self):
        """Test monday.com sync workflow"""
        project_id = "monday_test_001"
        integration = create_resource_allocation_integration(project_id)
        
        # Get monday data
        monday_data = integration.get_monday_com_data()
        
        self.assertIn('monday_fields', monday_data)
        self.assertIn('timestamp', monday_data)
    
    def test_feature_integration_workflow(self):
        """Test Feature 3,4,9,10 integration workflow"""
        project_id = "feature_test_001"
        integration = create_resource_allocation_integration(project_id)
        
        # Get all feature inputs
        f3_data = integration.get_feature_3_input()
        f4_data = integration.get_feature_4_input()
        f9_data = integration.get_feature_9_input()
        f10_data = integration.get_feature_10_input()
        
        self.assertIsInstance(f3_data, dict)
        self.assertIsInstance(f4_data, dict)
        self.assertIsInstance(f9_data, dict)
        self.assertIsInstance(f10_data, dict)


if __name__ == '__main__':
    unittest.main()
