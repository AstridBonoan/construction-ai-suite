# Feature 10: QUICK START GUIDE

## What is Feature 10?

Feature 10 is an AI-powered recommendation engine that:
- 🎯 Generates **10 specific, actionable recommendations** for construction projects
- 📊 Simulates **5 scenario types** with what-if analysis
- 🔄 Compares scenarios across **risk, cost, and schedule** dimensions
- 🔗 Integrates seamlessly with **Feature 1** (Core Risk Engine)
- 📱 Exports to **Monday.com** without API keys

## 5-Minute Setup

### 1. Import and Initialize
```python
from phase10_recommendation_integration import create_feature10_integration
from phase10_recommendation_types import RecommendationContext

# Create integration instance
integration = create_feature10_integration(project_id="PROJECT_001")
```

### 2. Prepare Project Context
```python
context = RecommendationContext(
    project_id="PROJECT_001",
    current_overall_risk=0.6,           # 0.0-1.0
    current_total_cost=1500000,         # in dollars
    current_duration_days=240,          # project duration
    cost_risk=0.7,                      # cost overrun risk
    schedule_risk=0.8,                  # schedule slip risk
    workforce_risk=0.55,                # labor availability
    equipment_risk=0.4,                 # equipment risk
    project_phase='execution',          # planning|execution|closing
    days_into_project=80,               # days elapsed
    days_remaining=160,                 # days left
    percent_complete=0.33,              # 0-1
    budget_headroom_available=150000,   # contingency
    schedule_headroom_available_days=21,# schedule buffer
    # ... other optional fields
)
```

### 3. Analyze Project
```python
output = integration.analyze_project(context, None, None)

# Access results
print(f"Recommendations: {len(output.recommendations)}")
print(f"Top Action: {output.top_recommendation.title}")
print(f"Recommended Scenario: {output.recommended_scenario.name}")
print(f"Risk Reduction Potential: {output.total_risk_reduction_potential:.1%}")
```

## Common Use Cases

### Use Case 1: Get Top Recommendation
```python
output = integration.analyze_project(context, None, None)
top_rec = output.top_recommendation

print(f"Action: {top_rec.title}")
print(f"Severity: {top_rec.severity.value}")
print(f"Impact:")
print(f"  Risk: {top_rec.impact.risk_impact.overall_risk_delta:.1%}")
print(f"  Cost: ${top_rec.impact.cost_impact.total_cost_delta:,.0f}")
print(f"  Schedule: {top_rec.impact.schedule_impact.duration_delta_days} days")
print(f"Confidence: {top_rec.confidence_level:.1%}")
```

### Use Case 2: Compare Scenarios
```python
from phase10_recommendation_types import ScenarioRequest, ScenarioType

scenario_request = ScenarioRequest(
    scenario_types=[
        ScenarioType.BASELINE,
        ScenarioType.CONSERVATIVE,
        ScenarioType.RISK_OPTIMIZED,
    ]
)

comparison = integration.scenario_simulator.simulate_scenarios(context, scenario_request)

# See best for each dimension
print(f"Best for Risk: {comparison.best_for_risk['name']}")
print(f"Best for Cost: {comparison.best_for_cost['name']}")
print(f"Best for Schedule: {comparison.best_for_schedule['name']}")

# View all scenarios
for scenario in comparison.scenarios:
    print(f"\n{scenario.name}:")
    print(f"  Risk: {scenario.estimated_risk_score:.2f}")
    print(f"  Cost: ${scenario.estimated_total_cost:,.0f}")
    print(f"  Schedule: {scenario.estimated_completion_days} days")
```

### Use Case 3: Export to Feature 1 (Core Risk Engine)
```python
# Get Feature 1 format
feature1_data = integration.get_feature1_input()

# Use in Feature 1
core_risk_engine.update_from_feature10(feature1_data)
```

### Use Case 4: Export to Monday.com
```python
# Get Monday.com formatted data
monday_data = integration.get_monday_com_data()

# Sync to Monday.com (manual or API)
for column, value in monday_data['monday_fields'].items():
    task_board.update_column(column, value)
```

## REST API Quick Reference

### Start Analysis
```bash
curl -X POST http://localhost:5000/api/feature10/analyze/PROJECT_001 \
  -H "Content-Type: application/json" \
  -d '{
    "current_overall_risk": 0.6,
    "current_total_cost": 1500000,
    "current_duration_days": 240,
    "cost_risk": 0.7,
    "schedule_risk": 0.8
  }'
```

### Get Recommendations
```bash
curl http://localhost:5000/api/feature10/recommendations/PROJECT_001?limit=5
```

### Get Scenarios
```bash
curl http://localhost:5000/api/feature10/scenarios/PROJECT_001
```

### Compare Scenarios
```bash
curl http://localhost:5000/api/feature10/scenario-comparison/PROJECT_001
```

### Get Monday.com Data
```bash
curl http://localhost:5000/api/feature10/monday-data/PROJECT_001
```

## 10 Recommendation Types You'll See

| Type | Triggered When | Impact | Effort |
|------|---|---|---|
| Cost Controls | cost_risk > 0.6 | Risk -15%, Cost +$5K, Schedule +2d | Easy |
| Schedule Buffer | schedule_risk > 0.6 | Risk -12%, Cost $0, Schedule +buffer/4 | Easy |
| Workforce Augmentation | workforce_risk > 0.55 | Risk -18%, Cost +$150K, Schedule -5d | Moderate |
| Equipment Maintenance | equipment_risk > 0.5 | Risk -10%, Cost +$25K | Easy |
| Compliance Enhancement | compliance_risk > 0.55 | Risk -12%, Cost +$8K | Easy |
| Environmental Safeguards | environmental_risk > 0.5 | Risk -8%, Cost +$12K, Schedule +1d | Moderate |
| Material Substitution | cost_variance > 0.1 | Risk +2%, Cost -$50K | Moderate |
| Productivity Optimization | execution phase | Risk -5%, Cost -$75K, Schedule -3d | Moderate |
| Fast-Track Critical Path | schedule_risk > 0.65 | Risk +15%, Cost +$200K, Schedule -10d | Hard |
| Schedule Recovery | behind > 1 week | Risk +10%, Cost +$300K, Schedule recovery | Hard |

## 5 Scenarios Available

| Name | Risk | Cost | Schedule | Viability | Best For |
|------|------|------|----------|-----------|----------|
| Baseline | Current | Current | Current | 100% | Reference |
| Optimistic | -25% | -8% | -15% | 60% | Best case |
| Conservative | -15% | +12% | +20% | 95% | **RECOMMENDED** |
| Cost-Optimized | +12% | -15% | +5% | 70% | Lowest cost |
| Time-Optimized | +18% | +35% | -25% | 65% | Fastest |
| Risk-Optimized | -30% | +18% | +10% | 85% | **RECOMMENDED** |

## Testing Feature 10

```bash
# Run all tests
pytest backend/app/test_phase10.py -v

# Run specific test class
pytest backend/app/test_phase10.py::TestRecommendationEngine -v

# Run with coverage
pytest backend/app/test_phase10.py --cov=backend.app.phase10
```

## Next Steps

1. **Review PHASE_10_README.md** for complete documentation
2. **Run tests**: `pytest backend/app/test_phase10.py -v`
3. **Try an example**: Use code above with real project data
4. **Integrate with Feature 1**: Use `get_feature1_input()`
5. **Sync to Monday.com**: Use `get_monday_com_data()`

## Key Principles

✅ **Deterministic** - Same input always produces same output  
✅ **Actionable** - 10 specific, measurable recommendations  
✅ **Integrated** - Works seamlessly with Features 1-9  
✅ **Explainable** - Every recommendation includes reasoning  
✅ **Testable** - 80+ comprehensive tests  
✅ **Production-Ready** - No external dependencies  

## File Reference

| File | Purpose |
|------|---------|
| phase10_recommendation_types.py | Data types (450 lines) |
| phase10_recommendation_engine.py | Recommendations (550 lines) |
| phase10_scenario_simulator.py | Scenarios (700 lines) |
| phase10_recommendation_integration.py | Integration (400 lines) |
| phase10_recommendation_api.py | REST API (400 lines) |
| test_phase10.py | Unit tests (50+) |
| test_phase10_api.py | API tests (30+) |
| PHASE_10_README.md | Full documentation (800+ lines) |

## Troubleshooting

**Q: No recommendations generated**  
A: Check that risk/cost/schedule values exceed trigger thresholds (e.g., cost_risk > 0.6)

**Q: Viability too low**  
A: Increase budget_headroom_available or schedule_headroom_available_days

**Q: How do I customize recommendations?**  
A: Edit thresholds in phase10_recommendation_engine.py

**Q: How do I add custom scenarios?**  
A: Use ScenarioRequest with custom ScenarioAdjustment

## Support

- Full documentation in PHASE_10_README.md
- Working examples in test files
- API reference at /api/feature10/health
- Browse code in backend/app/phase10_*.py

---

**Ready to generate AI-powered recommendations?** Start with 5-minute setup above!
