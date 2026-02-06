# Feature 11: Resource Allocation - Quick Reference Guide

## 🎯 Essential Commands

### Python API Quick Start
```python
from phase11_resource_integration import create_resource_allocation_integration
from phase11_resource_types import AllocationRequest

# Setup
integration = create_resource_allocation_integration("PRJ001")

# Analyze
request = AllocationRequest(project_id="PRJ001", optimization_goal="minimize_delay")
result = analyze_project_resources(integration, request)

# Get recommendations
recs = generate_allocation_recommendations(integration, "PRJ001")
```

### REST API Quick Reference

| Endpoint | Method | Purpose | Quick Call |
|----------|--------|---------|-----------|
| `/projects/{id}/analyze` | POST | Analyze resources | `curl -X POST .../analyze -d '{...}'` |
| `/projects/{id}/recommendations` | GET | Get recommendations | `curl .../recommendations` |
| `/projects/{id}/resources` | GET | List resources | `curl .../resources` |
| `/projects/{id}/tasks` | GET | List tasks | `curl .../tasks` |
| `/projects/{id}/allocations` | GET | Get allocations | `curl .../allocations` |
| `/projects/{id}/allocations` | POST | Apply allocation | `curl -X POST .../allocations -d '{...}'` |
| `/projects/{id}/conflicts` | GET | Get conflicts | `curl .../conflicts` |
| `/projects/{id}/metrics` | GET | Get metrics | `curl .../metrics` |
| `/health` | GET | Health check | `curl .../health` |

---

## 🔑 Key Classes

### Worker
```python
Worker(
    worker_id="W001",
    name="John Doe",
    skills=[Skill("carpentry", SkillLevel.SENIOR, 10)],
    availability=ResourceAvailability(...),
    hourly_rate=50.0,
    base_reliability_score=0.85
)
```

### Crew
```python
Crew(
    crew_id="C001",
    name="Carpentry Team",
    lead_worker_id="W001",
    member_worker_ids=["W001", "W002"],
    combined_reliability_score=0.85
)
```

### Subcontractor
```python
Subcontractor(
    subcontractor_id="SUB001",
    company_name="ABC Electrical",
    services=["electrical"],
    hourly_rate=75.0,
    performance_score=0.92
)
```

### TaskResourceRequirement
```python
TaskResourceRequirement(
    task_id="TASK-001",
    required_role="carpentry",
    required_skills=[Skill(...)],
    min_skill_level=SkillLevel.SENIOR,
    workers_needed=3,
    duration_days=5,
    start_date=date(2024, 2, 1),
    critical_path=True
)
```

---

## 📊 Optimization Goals

| Goal | Focus | Use Case |
|------|-------|----------|
| `minimize_delay` | Reduce critical path | Time-sensitive projects |
| `minimize_cost` | Reduce project cost | Budget-constrained projects |
| `balance` | Equal weight | General projects |

---

## ⚙️ Common Configuration

```python
# In phase11_config.py
OPTIMIZATION_WEIGHTS = {
    'minimize_delay': {'delay': 0.5, 'cost': 0.3, 'risk': 0.2},
    'minimize_cost': {'delay': 0.2, 'cost': 0.6, 'risk': 0.2},
    'balance': {'delay': 0.33, 'cost': 0.33, 'risk': 0.34}
}

SKILL_LEVELS = ['JUNIOR', 'INTERMEDIATE', 'SENIOR']
MAX_CONCURRENT_TASKS = 5
DEFAULT_RELIABILITY = 0.75
```

---

## 🔍 Constraint Types

| Constraint | Check | Example |
|-----------|-------|---------|
| **Skill Match** | Worker level ≥ Task level | Senior carpentry required |
| **Availability** | Task dates within worker window | Feb 1-31 task, worker available Feb 15-28 |
| **Concurrent Tasks** | Current tasks < max allowed | Worker on 2 tasks, max=3 |
| **On-site** | Task location matches worker preference | Site work needs on-site resource |
| **Travel Time** | Add travel hours to task duration | 1 hour travel + 8 hour task = 9 hours |

---

## 🎁 Recommendation Types

| Type | Example | Impact |
|------|---------|--------|
| **worker_allocation** | Allocate W001 to TASK-001 | Direct assignment |
| **crew_assignment** | Assign crew C001 to phase | Team-based work |
| **subcontractor_use** | Use SUB001 for electrical | External resource |
| **skill_development** | Train W002 in carpentry | Future capability |
| **load_balancing** | Rebalance W001/W002 tasks | Better utilization |
| **timeline_adjustment** | Reschedule TASK-002 to Feb 15 | Resolve conflicts |

---

## ⚡ Performance Tips

1. **Optimize Large Projects**
   - Break into sub-projects
   - Increase optimization timeout
   - Use simplified constraints

2. **Cache Results**
   - Results cached for project
   - Clear when data changes
   - Check `integration.analysis_cache`

3. **Parallel Analysis**
   - Analyze multiple projects simultaneously
   - Use thread pool for API calls
   - Aggregate results

4. **Monday.com Sync**
   - Sync before analysis
   - Verify credentials
   - Check network connection

---

## 🚨 Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `SKILL_MISMATCH` | Worker lacks required skill | Find different worker or train |
| `AVAILABILITY_GAP` | Worker unavailable during task | Reschedule or find alternative |
| `OVERALLOCATION` | Worker at max concurrent tasks | Redistribute or add resource |
| `COST_CONCERN` | Allocation exceeds budget | Use subcontractor or reduce scope |
| `LOCATION_CONFLICT` | Work location mismatch | Find on-site or remote resource |

---

## 📈 Key Metrics

```python
metrics = integration.get_allocation_metrics()

metrics['average_utilization']      # % of time allocated (0-1)
metrics['unallocated_hours']        # Hours without allocation
metrics['compliance_status']         # "on_track", "at_risk", "critical"
metrics['total_workers']             # Count of workers
metrics['critical_skills_gap']      # Missing skills list
metrics['estimated_delay_risk']     # Risk of schedule delay (0-1)
```

---

## 🔗 Integration Points

### Feature 3: Risk Scoring
```python
f3_data = integration.get_feature_3_input()
# Use risk scores in allocation scoring
```

### Feature 4: Task Management
```python
f4_data = integration.get_feature_4_input()
# Tasks with resource requirements
```

### Feature 9: Timeline Analysis
```python
f9_data = integration.get_feature_9_input()
# Critical path and timeline data
```

### Feature 10: Current Allocations
```python
f10_data = integration.get_feature_10_input()
# Existing allocations for conflict detection
```

### Monday.com
```python
monday_data = integration.get_monday_com_data()
# Workers, crews, subcontractors
```

---

## 🛠️ Common Tasks

### Task: Analyze Project Resources
```python
integration = create_resource_allocation_integration("PRJ001")
request = AllocationRequest(project_id="PRJ001", optimization_goal="minimize_delay")
result = analyze_project_resources(integration, request)
print(f"Confidence: {result.confidence_score * 100:.0f}%")
```

### Task: Get Top Recommendations
```python
recs = generate_allocation_recommendations(integration, "PRJ001", max=10)
for rec in recs[:5]:
    print(f"{rec['title']} - Impact: {rec['estimated_impact']}")
```

### Task: Detect Conflicts
```python
conflicts = integration.get_resource_conflicts()
critical = [c for c in conflicts if c['severity'] == 'critical']
print(f"Critical conflicts: {len(critical)}")
```

### Task: Apply Allocation
```python
result = integration.apply_allocation(
    task_id="TASK-001",
    worker_id="W001",
    start_date=date(2024, 2, 1),
    duration_days=5
)
print(f"Allocation: {result['allocation_id']}")
```

### Task: Get Resource Availability
```python
monday_data = integration.get_monday_com_data()
workers = monday_data['workers']
for w in workers:
    print(f"{w['name']}: {w['availability']['hours_per_week']} hrs/week")
```

---

## 🔐 Security Notes

- Validate project_id before operations
- Verify worker_id and task_id exist
- Check monday.com API credentials
- Log all allocation changes
- Audit trail in logs/phase11.log

---

## 📚 Learn More

- **Developer Guide**: `PHASE_23_FEATURE_11_DEVELOPER_GUIDE.py`
- **Completion Report**: `PHASE_23_FEATURE_11_COMPLETION.md`
- **Delivery Summary**: `PHASE_23_FEATURE_11_DELIVERY_SUMMARY.md`
- **Tests**: `backend/app/test_phase11_integration.py`

---

## 🎓 Example Workflows

### Complete Analysis Workflow
```python
# 1. Setup
integration = create_resource_allocation_integration("PRJ001")

# 2. Analyze
request = AllocationRequest("PRJ001", "minimize_delay")
result = analyze_project_resources(integration, request)

# 3. Review
print(f"Confidence: {result.confidence_score * 100:.0f}%")

# 4. Get recommendations
recs = generate_allocation_recommendations(integration, "PRJ001")

# 5. Detect conflicts
conflicts = integration.get_resource_conflicts()

# 6. Apply top recommendation
if recs:
    rec = recs[0]
    success = apply_recommendation(integration, rec)

# 7. Check metrics
metrics = integration.get_allocation_metrics()
print(f"Utilization: {metrics['average_utilization'] * 100:.0f}%")
```

---

**Last Updated**: Phase 23  
**Version**: 1.0  
**Status**: ✅ Production Ready
