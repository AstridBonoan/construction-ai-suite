# Phase 16: Smart Schedule Dependencies & Delay Propagation

**Feature 2** of the Construction AI Suite - Advanced schedule intelligence with cascading delay modeling.

## Overview

Phase 16 adds intelligent analysis of task dependencies and critical path calculation to the Construction AI Suite. It models how delays cascade through project schedules and integrates delay risk into Feature 1's overall project risk scoring engine.

### Key Capabilities

- **Critical Path Analysis** - Uses CPM (Critical Path Method) algorithm to identify critical tasks and project duration
- **Delay Propagation** - Simulates cascading delays through dependent tasks with realistic lag buffers
- **Risk Quantification** - Calculates probability of delays for each task based on complexity, weather, resources
- **Schedule Resilience** - Measures how resistant the schedule is to delays (0-1 score)
- **Feature 1 Integration** - Provides schedule delay risk to feed into overall project risk scoring
- **Explainable Reasoning** - Human-readable explanations of delay scenarios and recommendations

## Architecture

### Core Modules

1. **phase16_types.py** - Data structures
   - `Task` - Represents a work package/task
   - `TaskDependency` - Represents predecessor/successor relationships (PMBOK-standard types)
   - `CriticalPathAnalysis` - Results of CPM algorithm
   - `DelayPropagation` - Cascade model output
   - `ScheduleRiskFactors` - Risk quantification per task
   - `ProjectScheduleIntelligence` - Complete intelligence report

2. **phase16_schedule_dependencies.py** - Core analysis
   - `ScheduleDependencyAnalyzer` class
   - Critical path calculation using forward/backward pass
   - Risk factor calculation per task
   - Task impact scope analysis

3. **phase16_delay_propagation.py** - Cascading delays
   - `DelayPropagationEngine` class
   - Task delay simulation with BFS traversal
   - Schedule resilience calculation
   - Feature 1 integration risk scoring
   - Scenario generation for "what-if" analysis

4. **phase16_api.py** - REST endpoints
   - `POST /api/schedule/analyze` - Analyze a schedule
   - `GET /api/schedule/critical-path/<project_id>` - Get critical path (placeholder)
   - `GET /api/schedule/integration-risk/<project_id>` - Get Feature 1 integration risk

5. **tests/test_phase16.py** - Unit tests
   - CI-safe test cases using synthetic data
   - Tests for CPM calculation, delay propagation, risk scoring

## Data Model

### Task Definition

```python
Task(
    task_id="foundation",
    name="Foundation Work",
    duration_days=10,
    complexity_factor=1.5,  # 0.5-2.0
    weather_dependency=True,
    resource_constrained=False
)
```

### Dependency Definition (PMBOK Standard)

```python
TaskDependency(
    dependency_id="dep1",
    predecessor_task_id="foundation",
    successor_task_id="framing",
    dependency_type=DependencyType.FINISH_TO_START,  # or SS, FF, SF
    lag_days=1  # Buffer between tasks
)
```

### Schedule Intelligence Output

```json
{
  "project_id": "PROJ_001",
  "project_name": "Downtown Plaza",
  "critical_path": ["foundation", "framing", "roofing", "interior"],
  "project_duration_days": 120,
  "schedule_resilience_score": 0.65,
  "integration_risk_score": 0.35,
  "recommended_buffer_days": 15,
  "high_risk_task_count": 3,
  "task_risk_factors": {
    "foundation": {
      "task_id": "foundation",
      "combined_delay_probability": 0.45,
      "expected_delay_days": 3.2,
      "worst_case_delay_days": 5,
      "confidence_level": "High"
    }
  }
}
```

## Integration with Feature 1 (Risk Scoring)

The schedule delay risk integrates with Feature 1's AI risk engine through:

1. **Integration Risk Score** (0-1)
   - Calculated from schedule resilience, critical path length, and task risks
   - Added to Feature 1's project risk components
   - Contributes to overall project risk estimate

2. **Delay Contribution**
   - Schedule intelligence provides expected delay days to Feature 1
   - Feeds into delay probability predictions
   - Improves accuracy of risk-based recommendations

## API Usage

### Example 1: Analyze a Schedule

```bash
curl -X POST http://localhost:5000/api/schedule/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "PROJ_001",
    "project_name": "Downtown Plaza Construction",
    "tasks": [
      {
        "task_id": "foundation",
        "name": "Foundation",
        "duration_days": 10,
        "complexity_factor": 1.5,
        "weather_dependency": true
      },
      {
        "task_id": "framing",
        "name": "Framing",
        "duration_days": 15,
        "complexity_factor": 1.2,
        "resource_constrained": true
      }
    ],
    "dependencies": [
      {
        "dependency_id": "dep1",
        "predecessor_task_id": "foundation",
        "successor_task_id": "framing",
        "dependency_type": "finish_to_start",
        "lag_days": 1
      }
    ]
  }'
```

### Example 2: Use Results in Feature 1

```python
# Get schedule intelligence
schedule_intel = engine.create_project_intelligence(...)

# Feed to Feature 1 risk engine
overall_risk_score = (
    feature1_risk * 0.7 +  # 70% from Feature 1
    schedule_intel.integration_risk_score * 0.3  # 30% from schedule
)
```

## Testing

Run unit tests with:

```bash
python -m pytest backend/tests/test_phase16.py -v
```

Tests cover:
- Critical path calculation correctness
- Delay propagation through dependencies
- Risk factor quantification
- Schedule resilience scoring
- JSON serialization

All tests use CI-safe synthetic data (no external dependencies).

## Monday.com Integration (Phase 8)

Placeholder hooks for future Monday.com integration:

- `GET /api/schedule/critical-path/<project_id>` - Will fetch from Monday.com board
- `GET /api/schedule/integration-risk/<project_id>` - Will update task risk status columns
- Planned: Bi-directional sync of task status and dependency updates

## Future Enhancements

1. **Live Data Integration**
   - Fetch schedules from Monday.com task board
   - Update risk assessments in real-time as tasks progress

2. **Advanced Scenarios**
   - Monte Carlo simulation for probabilistic project completion
   - Resource leveling impact analysis
   - Multi-project portfolio scheduling

3. **Recommendations Engine**
   - Suggest scope reductions for critical path
   - Recommend resource reallocation to high-risk tasks
   - Calculate time/cost tradeoff options

4. **Database Persistence**
   - Store analysis results for historical comparison
   - Track actual delays vs. predictions
   - Improve risk models with feedback data

## Code Patterns & Conventions

### Logging

```python
logger.info("Critical path length: 45 days")
logger.error(f"Task {task_id} not found")
```

### Type Hints

All functions include type hints for clarity and IDE support:

```python
def simulate_task_delay(
    self,
    task_id: str,
    delay_days: int,
    critical_path: List[str]
) -> DelayPropagation:
```

### Error Handling

Graceful error handling with informative messages:

```python
if task_id not in self.analyzer.tasks:
    logger.error(f"Task {task_id} not found")
    return jsonify({"error": "Task not found"}), 404
```

### Testing

Unit tests are CI-safe and use deterministic synthetic data:

```python
def setUp(self):
    """Create synthetic schedule"""
    self.analyzer = ScheduleDependencyAnalyzer()
    self.analyzer.add_task(Task("task1", "Task 1", 10))
```

## File Structure

```
backend/app/
├── phase16_types.py              # Data structures
├── phase16_schedule_dependencies.py  # Core CPM algorithm
├── phase16_delay_propagation.py     # Delay cascading engine
├── phase16_api.py                   # REST endpoints
└── main.py                          # Register blueprint

backend/tests/
└── test_phase16.py                # Unit tests
```

## Notes for Developers

1. **Determinism**: All calculations use deterministic algorithms (CPM, BFS, simple probability) for reproducible results
2. **Testability**: Synthetic test data means no external dependencies required
3. **Modularity**: Each class has single responsibility (Analyzer, Engine, API)
4. **Documentation**: Extensive docstrings explain algorithm rationale
5. **Integration**: Designed to feed into Feature 1, not replace it

---

**Branch**: `feature/smart-schedule-dependencies`
**Status**: Initial implementation ready for extension with live data
