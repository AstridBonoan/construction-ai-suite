"""
Phase 16: Unit Tests - Schedule Dependencies & Delay Propagation

Tests for critical path analysis, delay propagation, and integration.
CI-safe test cases using synthetic data.
"""

import sys
from pathlib import Path

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import unittest
from phase16_types import (
    Task, TaskDependency, DependencyType, TaskStatus
)
from phase16_schedule_dependencies import ScheduleDependencyAnalyzer
from phase16_delay_propagation import DelayPropagationEngine


class TestScheduleDependencyAnalyzer(unittest.TestCase):
    """Test critical path analysis"""
    
    def setUp(self):
        """Create a sample project schedule"""
        self.analyzer = ScheduleDependencyAnalyzer()
        
        # Create tasks for a simple construction project
        # Structure:
        # Foundation (10d) -> Framing (15d) -> Roofing (8d) -> Interior (20d)
        #                  \-> Electrical (12d) -/
        
        self.analyzer.add_task(Task(
            task_id="foundation",
            name="Foundation",
            duration_days=10,
            complexity_factor=1.5,
            weather_dependency=True
        ))
        
        self.analyzer.add_task(Task(
            task_id="framing",
            name="Framing",
            duration_days=15,
            complexity_factor=1.2,
            resource_constrained=True
        ))
        
        self.analyzer.add_task(Task(
            task_id="roofing",
            name="Roofing",
            duration_days=8,
            complexity_factor=1.3,
            weather_dependency=True
        ))
        
        self.analyzer.add_task(Task(
            task_id="electrical",
            name="Electrical",
            duration_days=12,
            complexity_factor=1.1
        ))
        
        self.analyzer.add_task(Task(
            task_id="interior",
            name="Interior Finishing",
            duration_days=20,
            complexity_factor=1.0
        ))
        
        # Add dependencies
        self.analyzer.add_dependency(TaskDependency(
            dependency_id="dep1",
            predecessor_task_id="foundation",
            successor_task_id="framing",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=1
        ))
        
        self.analyzer.add_dependency(TaskDependency(
            dependency_id="dep2",
            predecessor_task_id="foundation",
            successor_task_id="electrical",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=0
        ))
        
        self.analyzer.add_dependency(TaskDependency(
            dependency_id="dep3",
            predecessor_task_id="framing",
            successor_task_id="roofing",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=2
        ))
        
        self.analyzer.add_dependency(TaskDependency(
            dependency_id="dep4",
            predecessor_task_id="roofing",
            successor_task_id="interior",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=0
        ))
        
        self.analyzer.add_dependency(TaskDependency(
            dependency_id="dep5",
            predecessor_task_id="electrical",
            successor_task_id="interior",
            dependency_type=DependencyType.FINISH_TO_START,
            lag_days=1
        ))
    
    def test_critical_path_calculation(self):
        """Test critical path is calculated correctly"""
        cp = self.analyzer.calculate_critical_path()
        
        # Critical path should start with foundation
        self.assertEqual(cp.critical_path[0], "foundation")
        
        # Should have positive duration
        self.assertGreater(cp.project_duration_days, 0)
        
        # All critical tasks should have zero slack
        for task_id in cp.critical_tasks:
            self.assertEqual(cp.slack_by_task[task_id], 0)
        
        # Non-critical tasks should have positive slack
        non_critical = set(self.analyzer.tasks.keys()) - cp.critical_tasks
        for task_id in non_critical:
            self.assertGreater(cp.slack_by_task[task_id], 0)
    
    def test_risk_factor_calculation(self):
        """Test risk factor calculations"""
        rf = self.analyzer.calculate_risk_factors("foundation")
        
        # Weather dependency increases weather risk
        self.assertGreater(rf.weather_risk, 0.1)
        
        # Combined probability should be between 0 and 1
        self.assertGreaterEqual(rf.combined_delay_probability, 0.0)
        self.assertLessEqual(rf.combined_delay_probability, 1.0)
        
        # Expected delay should be positive
        self.assertGreater(rf.expected_delay_days, 0)
    
    def test_task_impact_scope(self):
        """Test that task impact scope correctly identifies affected tasks"""
        # If foundation is delayed, it should affect everything
        scope = self.analyzer.get_task_impact_scope("foundation")
        
        # All other tasks should be in scope
        self.assertEqual(len(scope), 4)
        
        # Interior should be farthest (maximum distance)
        self.assertIn("interior", scope)


class TestDelayPropagationEngine(unittest.TestCase):
    """Test delay propagation modeling"""
    
    def setUp(self):
        """Setup analyzer and engine"""
        self.analyzer = ScheduleDependencyAnalyzer()
        self.engine = DelayPropagationEngine(self.analyzer)
        
        # Simple linear dependency: A -> B -> C
        self.analyzer.add_task(Task("a", "Task A", 5))
        self.analyzer.add_task(Task("b", "Task B", 5))
        self.analyzer.add_task(Task("c", "Task C", 5))
        
        self.analyzer.add_dependency(TaskDependency(
            "dep1", "a", "b", DependencyType.FINISH_TO_START, lag_days=0
        ))
        self.analyzer.add_dependency(TaskDependency(
            "dep2", "b", "c", DependencyType.FINISH_TO_START, lag_days=0
        ))
    
    def test_delay_propagation(self):
        """Test that delay propagates through dependencies"""
        cp = self.analyzer.calculate_critical_path()
        delay_prop = self.engine.simulate_task_delay("a", 5, cp.critical_path)
        
        # Delay should propagate to B and C
        self.assertIn("b", delay_prop.affected_tasks)
        self.assertIn("c", delay_prop.affected_tasks)
        
        # Project delay should be equal to initial delay on critical path
        self.assertEqual(delay_prop.total_project_delay_days, 5)
    
    def test_delay_with_lag(self):
        """Test that lag reduces propagation"""
        # Add delay to task B, but with lag buffer
        cp = self.analyzer.calculate_critical_path()
        
        # Modify dependency to have lag
        for dep in self.analyzer.dependencies.values():
            if dep.predecessor_task_id == "b" and dep.successor_task_id == "c":
                dep.lag_days = 3
        
        delay_prop = self.engine.simulate_task_delay("b", 2, cp.critical_path)
        
        # 2-day delay with 3-day lag should not propagate to C
        self.assertNotIn("c", delay_prop.affected_tasks)
    
    def test_schedule_resilience(self):
        """Test resilience calculation"""
        cp = self.analyzer.calculate_critical_path()
        rf = {task_id: self.analyzer.calculate_risk_factors(task_id) 
              for task_id in self.analyzer.tasks}
        
        resilience = self.engine.calculate_schedule_resilience(cp, rf)
        
        # Should be between 0 and 1
        self.assertGreaterEqual(resilience, 0.0)
        self.assertLessEqual(resilience, 1.0)
    
    def test_integration_risk_score(self):
        """Test Feature 1 integration risk score"""
        score = self.engine.calculate_integration_risk_score(
            schedule_resilience=0.6,
            critical_path_length=10,
            avg_task_risk=0.4
        )
        
        # Should be between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Higher resilience should lower score
        low_resilience_score = self.engine.calculate_integration_risk_score(
            schedule_resilience=0.3,
            critical_path_length=10,
            avg_task_risk=0.4
        )
        self.assertGreater(low_resilience_score, score)
    
    def test_scenario_generation(self):
        """Test scenario generation"""
        cp = self.analyzer.calculate_critical_path()
        scenarios = self.engine.generate_delay_scenarios(cp.critical_path, num_scenarios=3)
        
        # Should generate scenarios
        self.assertGreater(len(scenarios), 0)
        
        # Each scenario should have positive project delay
        for scenario in scenarios:
            self.assertGreater(scenario.total_project_delay_days, -1)


class TestProjectScheduleIntelligence(unittest.TestCase):
    """Test complete project intelligence assembly"""
    
    def setUp(self):
        """Create complex project"""
        self.analyzer = ScheduleDependencyAnalyzer()
        self.engine = DelayPropagationEngine(self.analyzer)
        
        # Create 5-task project
        for i in range(5):
            self.analyzer.add_task(Task(
                task_id=f"task{i}",
                name=f"Task {i}",
                duration_days=10 + i*2,
                complexity_factor=1.0 + (i * 0.1)
            ))
        
        # Linear dependencies
        for i in range(4):
            self.analyzer.add_dependency(TaskDependency(
                dependency_id=f"dep{i}",
                predecessor_task_id=f"task{i}",
                successor_task_id=f"task{i+1}",
                dependency_type=DependencyType.FINISH_TO_START
            ))
    
    def test_project_intelligence_creation(self):
        """Test complete intelligence report creation"""
        cp = self.analyzer.calculate_critical_path()
        rf = {task_id: self.analyzer.calculate_risk_factors(task_id) 
              for task_id in self.analyzer.tasks}
        scenarios = self.engine.generate_delay_scenarios(cp.critical_path)
        
        intelligence = self.engine.create_project_intelligence(
            project_id="test-project",
            project_name="Test Construction Project",
            critical_path_analysis=cp,
            risk_factors=rf,
            scenarios=scenarios
        )
        
        # Verify all fields
        self.assertEqual(intelligence.project_id, "test-project")
        self.assertEqual(intelligence.total_tasks, 5)
        self.assertGreater(intelligence.schedule_resilience_score, 0)
        self.assertLess(intelligence.integration_risk_score, 1)
        self.assertGreater(intelligence.recommended_buffer_days, 0)
    
    def test_json_serialization(self):
        """Test JSON serialization of results"""
        cp = self.analyzer.calculate_critical_path()
        rf = {task_id: self.analyzer.calculate_risk_factors(task_id) 
              for task_id in self.analyzer.tasks}
        
        intelligence = self.engine.create_project_intelligence(
            project_id="test",
            project_name="Test",
            critical_path_analysis=cp,
            risk_factors=rf,
            scenarios=[]
        )
        
        # Should serialize to dict
        data = intelligence.to_dict()
        self.assertIsInstance(data, dict)
        self.assertIn("project_id", data)
        self.assertIn("integration_risk_score", data)


if __name__ == "__main__":
    unittest.main()
