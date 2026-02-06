# Feature 10: Automated AI Recommendations & What-If Scenarios

## Overview

Feature 10 implements an intelligent recommendation engine and scenario simulator that provides actionable AI-driven insights for construction project management. It enables decision-makers to understand impacts of different strategies before implementation, with full integration into the existing Feature 1-9 ecosystem.

**Key Capabilities:**
- 🎯 **AI Recommendations**: 10 specific recommendation types (Cost Reduction, Schedule Acceleration, Risk Mitigation, etc.)
- 📊 **What-If Analysis**: 5 predefined + custom scenarios with trade-off analysis
- 🔄 **Scenario Comparison**: Rank scenarios across risk, cost, and schedule dimensions
- 🔗 **Feature Integration**: Seamless integration with Feature 1 (Core Risk Engine) and monday.com
- ✅ **Deterministic Output**: Same input always produces same output (testable, reproducible)

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Feature 10 Integration                        │
│  (feature10_recommendation_integration.py)                       │
│  - Orchestrates engines                                          │
│  - Feature 1 input formatting                                    │
│  - Monday.com data formatting                                    │
└────────┬────────────────────────────┬────────────────────────────┘
         │                            │
    ┌────▼─────────────┐    ┌────────▼──────────────┐
    │ Recommendation    │    │  Scenario Simulator   │
    │ Engine            │    │  (ScenarioSimulator)  │
    │ (RecommendationEn │    │  - 5 scenario types   │
    │ gine)             │    │  - Trade-off analysis │
    │ - 8+ rec types    │    │  - Comparison logic   │
    │ - Risk/Cost/Sch   │    │  - History tracking   │
    │ - Filtering       │    └───────────────────────┘
    └───────────────────┘
         │
         └─ feature10_recommendation_types.py
            - 12 @dataclass structures
            - 10 Enums (types, severity)
            - Complete type system
```

### Data Types (phase10_recommendation_types.py)

**Enums:**
- `RecommendationType` (10 values): COST_REDUCTION, SCHEDULE_ACCELERATION, SCHEDULE_BUFFER, RISK_MITIGATION, QUALITY_IMPROVEMENT, WORKFORCE_OPTIMIZATION, EQUIPMENT_EFFICIENCY, MATERIAL_SUBSTITUTION, COMPLIANCE_ENHANCEMENT, ENVIRONMENTAL_PROTECTION

- `RecommendationSeverity` (4 values): LOW, MEDIUM, HIGH, CRITICAL

- `ScenarioType` (7 values): BASELINE, OPTIMISTIC, CONSERVATIVE, COST_OPTIMIZED, TIME_OPTIMIZED, RISK_OPTIMIZED, CUSTOM

- `ImpactMetric` (8 values): RISK, COST, SCHEDULE, QUALITY, SAFETY, COMPLIANCE, WORKFORCE_MORALE, RESOURCE_UTILIZATION

**Core Data Structures:**

```python
@dataclass
class Recommendation:
    recommendation_id: str                      # Unique identifier
    project_id: str                             # Project reference
    task_id: Optional[str]                      # Optional task reference
    recommendation_type: RecommendationType     # Type of recommendation
    severity: RecommendationSeverity            # Severity level
    title: str                                  # Short title
    description: str                            # Full description
    impact: RecommendationImpact                # Impact details
    reasoning: str                              # Why recommended
    benefits: List[str]                         # Benefits list
    drawbacks: List[str]                        # Drawbacks list
    prerequisites: List[str]                    # Prerequisites
    constraints: List[str]                      # Constraints
    baseline_metrics: Dict                      # Before metrics
    projected_metrics: Dict                     # After metrics
    confidence_level: float                     # Confidence (0-1)
    generated_at: datetime                      # Generation time
    valid_until: Optional[datetime]             # Validity period
    monday_com_column_map: Dict                 # Monday.com mappings

@dataclass
class RecommendationImpact:
    risk_impact: RiskImpact                      # Risk changes
    cost_impact: CostImpact                      # Cost changes
    schedule_impact: ScheduleImpact              # Schedule changes
    implementation_effort_hours: int             # Hours needed
    implementation_difficulty: str               # easy|moderate|hard
    implementation_duration_days: int            # Days to implement
    risk_of_implementation: float                # Implementation risk

@dataclass
class Scenario:
    scenario_id: str                             # Unique identifier
    scenario_type: ScenarioType                  # Type
    name: str                                    # Scenario name
    description: str                             # Description
    adjustments: Dict                            # Parameter adjustments
    estimated_risk_score: float                  # Projected risk (0-1)
    estimated_total_cost: float                  # Projected cost
    estimated_completion_days: int               # Projected duration
    risk_breakdown: Dict                         # Risk by type
    cost_breakdown: Dict                         # Cost by type
    schedule_breakdown: Dict                     # Schedule details
    viability_score: float                       # Viability (0-1)
    risk_of_scenario: float                      # Inherent risk (0-1)
    confidence_level: float                      # Confidence (0-1)
    trade_offs: Dict                             # Trade-off analysis
    recommended: bool                            # Is recommended
    created_at: datetime                         # Creation time
    last_updated: datetime                       # Last update
    valid_until: Optional[datetime]              # Validity period
    monday_com_column_map: Dict                  # Monday.com mappings
```

## Recommendation Engine

### How It Works

The recommendation engine analyzes project context and generates specific, actionable recommendations across three domains: risk, cost, and schedule.

### Recommendation Types

**Risk Recommendations:**

1. **Cost Controls** (triggered: cost_risk > 0.6)
   - Impact: Risk -15%, Cost +$5K, Schedule +2 days
   - Effort: Easy (8 hours)
   - For: High cost risk projects

2. **Schedule Buffer** (triggered: schedule_risk > 0.6)
   - Impact: Risk -12%, Cost $0, Schedule +buffer/4 days
   - Effort: Easy (8 hours)
   - For: Schedule risk projects

3. **Workforce Augmentation** (triggered: workforce_risk > 0.55)
   - Impact: Risk -18%, Cost +$150K, Schedule -5 days
   - Effort: Moderate (40 hours)
   - For: Workforce shortage

4. **Equipment Maintenance** (triggered: equipment_risk > 0.5)
   - Impact: Risk -10%, Cost +$25K, Schedule 0 days
   - Effort: Easy (8 hours)
   - For: Equipment reliability

5. **Compliance Enhancement** (triggered: compliance_risk > 0.55)
   - Impact: Risk -12%, Cost +$8K, Schedule 0 days
   - Effort: Easy (8 hours)
   - For: Compliance exposure

6. **Environmental Safeguards** (triggered: environmental_risk > 0.5)
   - Impact: Risk -8%, Cost +$12K, Schedule +1 day
   - Effort: Moderate (40 hours)
   - For: Environmental hazards

**Cost Recommendations:**

7. **Material Substitution** (triggered: cost_variance > 0.1)
   - Impact: Risk +0.02, Cost -$50K, Schedule 0 days
   - Effort: Moderate (40 hours)
   - For: Cost overruns

8. **Productivity Optimization** (execution phase)
   - Impact: Risk -5%, Cost -$75K, Schedule -3 days
   - Effort: Moderate (40 hours)
   - For: Operational inefficiency

**Schedule Recommendations:**

9. **Fast-Track Critical Path** (triggered: schedule_risk > 0.65)
   - Impact: Risk +15%, Cost +$200K, Schedule -10 days
   - Effort: Hard (160 hours)
   - For: Schedule acceleration

10. **Schedule Recovery** (if behind > 1 week)
    - Impact: Risk +10%, Cost +$300K, Schedule recovery
    - Effort: Hard (160 hours)
    - For: Schedule recovery

### API Usage

```python
from phase10_recommendation_integration import create_feature10_integration

# Create integration
integration = create_feature10_integration(project_id="PRJ001")

# Analyze and get recommendations
from phase10_recommendation_types import RecommendationContext, RecommendationRequest

context = RecommendationContext(
    project_id="PRJ001",
    current_overall_risk=0.6,
    current_total_cost=1500000,
    current_duration_days=240,
    cost_risk=0.7,
    schedule_risk=0.8,
    workforce_risk=0.55,
    # ... other context fields
)

request = RecommendationRequest(
    max_recommendations=10,
    include_types=None,  # All types
    minimum_risk_reduction=0.05,
)

output = integration.analyze_project(context, request, None)

# Access recommendations
for rec in output.recommendations:
    print(f"{rec.title}: {rec.severity.value}")
    print(f"  Risk Delta: {rec.impact.risk_impact.overall_risk_delta}")
    print(f"  Cost Impact: ${rec.impact.cost_impact.total_cost_delta}")
```

## Scenario Simulator

### How It Works

The scenario simulator creates alternative project futures and compares them across multiple dimensions, enabling decision-makers to understand trade-offs before commitment.

### Scenario Types

**Baseline (No Changes)**
- Risk: Current, Cost: Current, Schedule: Current
- Viability: 100%, Confidence: 100%
- Use: Reference point for comparison

**Optimistic**
- Risk: -25%, Cost: -8%, Schedule: -15%
- Viability: 60%, Confidence: 50%
- Best for: Efficient execution with minimal issues
- Trade-offs: Aggressive, uncertain

**Conservative (RECOMMENDED)**
- Risk: -15%, Cost: +12%, Schedule: +20%
- Viability: 95%, Confidence: 90%
- Best for: Risk mitigation with modest impacts
- Includes: Buffers, contingency, mitigations
- Trade-offs: More time/cost for less risk

**Cost-Optimized**
- Risk: +12%, Cost: -15%, Schedule: +5%
- Viability: 70%, Confidence: 70%
- Best for: Lowest cost path
- Via: Material substitution, lean staffing
- Trade-offs: Higher material/schedule risk

**Time-Optimized**
- Risk: +18%, Cost: +35%, Schedule: -25%
- Viability: 65%, Confidence: 60%
- Best for: Fastest completion
- Via: Parallel execution, additional crews
- Trade-offs: Significantly higher cost/risk

**Risk-Optimized (RECOMMENDED)**
- Risk: -30%, Cost: +18%, Schedule: +10%
- Viability: 85%, Confidence: 85%
- Best for: Maximum risk reduction
- Via: Daily audits, quality checkpoints, monitoring
- Trade-offs: Slower, more expensive

### Trade-Off Analysis

Each scenario includes three correlation metrics (-1.0 to +1.0):

- **Cost vs Time**: Shows cost/schedule trade-off
  - Negative = spending more reduces time
  - Positive = spending more increases time

- **Cost vs Risk**: Shows cost/risk trade-off
  - Negative = spending more reduces risk
  - Positive = spending more increases risk

- **Time vs Risk**: Shows time/risk trade-off
  - Negative = faster execution reduces risk
  - Positive = faster execution increases risk

### API Usage

```python
from phase10_recommendation_types import ScenarioRequest

request = ScenarioRequest(
    scenario_types=[
        ScenarioType.BASELINE,
        ScenarioType.CONSERVATIVE,
        ScenarioType.RISK_OPTIMIZED,
        ScenarioType.COST_OPTIMIZED,
    ]
)

comparison = integration.scenario_simulator.simulate_scenarios(context, request)

# Access scenario comparison
for scenario in comparison.scenarios:
    print(f"{scenario.name}:")
    print(f"  Risk: {scenario.estimated_risk_score:.2f}")
    print(f"  Cost: ${scenario.estimated_total_cost:,.0f}")
    print(f"  Schedule: {scenario.estimated_completion_days} days")
    print(f"  Recommended: {scenario.recommended}")
```

## Integration with Features 1-9

### Feature 1 Integration (Core Risk Engine)

Feature 10 provides the following fields to Feature 1:

```python
feature1_input = integration.get_feature1_input()

# Returns:
{
    'feature10_all_recommendations': [
        {
            'title': str,
            'type': str,
            'severity': str,
            'risk_delta': float,
            'cost_delta': float,
            'schedule_delta': float,
            'confidence': float,
        },
        # ... more recommendations
    ],
    'feature10_top_recommendation': {
        'title': str,
        'type': str,
        'impact': dict,
    },
    'feature10_recommended_scenario': {
        'name': str,
        'risk_projection': float,
        'cost_projection': float,
        'schedule_projection': int,
    },
    'feature10_total_risk_reduction_potential': float,
    'feature10_total_cost_reduction_potential': float,
    'feature10_total_schedule_improvement': int,
    'feature10_analysis_timestamp': str,
}
```

### Monday.com Integration

Feature 10 provides formatted data for monday.com without requiring API credentials:

```python
monday_data = integration.get_monday_com_data()

# Returns:
{
    'monday_fields': {
        'feature10_recommendations_count': int,
        'feature10_top_action': str,
        'feature10_impact_risk': str,
        'feature10_impact_cost': str,
        'feature10_effort': str,  # easy|moderate|hard
        'feature10_recommended_scenario': str,
        'feature10_scenario_risk': str,
        'feature10_scenario_cost': str,
        'feature10_scenario_schedule': str,
    }
}
```

## REST API Endpoints

### Base URL
```
/api/feature10
```

### Endpoints

**POST /analyze/{project_id}**
- Analyze project and generate recommendations + scenarios
- Request: Project context (risk, cost, schedule, phases)
- Response: Complete analysis with recommendations, scenarios, comparison
- Status: 200 OK, 500 Error

**GET /recommendations/{project_id}**
- Retrieve all recommendations for project
- Query Parameters:
  - `limit`: Maximum records (default 10)
  - `task_id`: Filter by task (optional)
- Response: List of recommendations with impacts
- Status: 200 OK, 500 Error

**GET /scenarios/{project_id}**
- Retrieve all scenarios for project
- Response: List of scenarios with projections
- Status: 200 OK, 500 Error

**GET /scenario-comparison/{project_id}**
- Get scenario ranking and comparison
- Response: Best-for rankings and scenario details
- Status: 200 OK, 400 Bad Request, 500 Error

**POST /apply-recommendation/{project_id}/{recommendation_id}**
- Apply recommendation to project
- Response: Confirmation and updated projections
- Status: 200 OK, 400 Bad Request, 500 Error

**POST /apply-scenario/{project_id}/{scenario_id}**
- Apply scenario to project
- Response: Confirmation and scenario details
- Status: 200 OK, 400 Bad Request, 500 Error

**GET /monday-data/{project_id}**
- Get data formatted for monday.com
- Response: Column mappings ready for sync
- Status: 200 OK, 500 Error

**GET /feature1-input/{project_id}**
- Get data formatted for Feature 1 (Core Risk Engine)
- Response: Feature 1 input fields
- Status: 200 OK, 500 Error

**GET /health**
- Service health check
- Response: Service status and active projects
- Status: 200 OK

**DELETE /reset/{project_id}**
- Reset all analysis for project (testing only)
- Response: Confirmation of reset
- Status: 200 OK, 500 Error

## Testing

### Unit Tests (test_phase10.py)

**RecommendationEngine Tests:**
- Recommendation trigger conditions (8+ recommendation types)
- Recommendation filtering and sorting
- Impact calculations (risk, cost, schedule)
- Severity scoring
- Confidence calculation
- History tracking

**ScenarioSimulator Tests:**
- Scenario generation (all 5 types)
- Impact projections
- Viability and confidence scoring
- Trade-off analysis
- Scenario comparison and ranking
- History tracking

**Feature10Integration Tests:**
- Engine orchestration
- Feature 1 input formatting
- Monday.com data formatting
- Context history preservation

**Determinism Tests:**
- Same input produces same output
- Recommendations deterministic
- Scenarios deterministic

### Running Tests

```bash
# All tests
python -m pytest backend/app/test_phase10.py -v

# Specific test class
python -m pytest backend/app/test_phase10.py::TestRecommendationEngine -v

# Specific test
python -m pytest backend/app/test_phase10.py::TestRecommendationEngine::test_cost_controls_recommendation_triggered -v

# With coverage
python -m pytest backend/app/test_phase10.py --cov=backend.app.phase10

# API tests
python -m pytest backend/app/test_phase10_api.py -v
```

### Test Coverage

- **Unit Tests**: 50+ tests
  - 25+ RecommendationEngine tests
  - 20+ ScenarioSimulator tests
  - 10+ Integration tests

- **API Tests**: 30+ tests
  - Endpoint structure validation
  - Response format validation
  - Workflow validation
  - Error handling

- **Determinism Tests**: 5+ tests
  - Reproducibility verification

**Target Coverage**: 85%+ code coverage

## Configuration

### Recommendation Thresholds

Edit `phase10_recommendation_engine.py` to customize triggers:

```python
# Cost controls triggered when:
if context.cost_risk > 0.6:  # Adjust threshold
    # Generate recommendation
    
# Workforce augmentation triggered when:
if context.workforce_risk > 0.55:  # Adjust threshold
    # Generate recommendation
```

### Scenario Adjustments

Edit `phase10_scenario_simulator.py` to customize scenario parameters:

```python
# Optimistic scenario
risk_reduction_percent = 0.25  # Adjust
cost_reduction_percent = 0.08  # Adjust
schedule_reduction_percent = 0.15  # Adjust
```

### Impact Calculations

Edit `phase10_recommendation_engine.py` to adjust impact values:

```python
# Cost controls impact
COST_IMPACT = -5000  # Adjust cost impact
RISK_REDUCTION = 0.15  # Adjust risk reduction
SCHEDULE_IMPACT = 2  # Adjust schedule impact
```

## Best Practices

1. **Context Accuracy**: Provide accurate risk, cost, and schedule inputs for better recommendations
2. **Regular Analysis**: Re-run analysis as project progresses to track changes
3. **Scenario Comparison**: Always compare conservative + recommended scenario before decision
4. **Feature 1 Integration**: Use Feature 10 insights to update Feature 1 core engine
5. **Monday.com Sync**: Sync recommendations to monday.com tasks for team visibility
6. **Confidence Thresholds**: Only act on recommendations with confidence > 0.7

## Troubleshooting

### No Recommendations Generated

**Problem**: Analysis returns no recommendations

**Solutions**:
1. Check risk/cost/schedule inputs are > trigger thresholds
2. Check `RecommendationRequest.minimum_*_reduction` isn't too high
3. Verify project phase and completion % are set correctly

### Scenario Viability Too Low

**Problem**: All scenarios have low viability

**Solutions**:
1. Provide accurate context values
2. Check project constraints (budget headroom, schedule headroom)
3. Consider custom scenarios with specific adjustments

### Feature 1 Integration Issues

**Problem**: Feature 10 input not integrating with Feature 1

**Solutions**:
1. Verify Feature 1 expects `feature10_*` prefixed fields
2. Check data types match (float vs string)
3. Ensure timestamps are ISO format

## Performance

- **Recommendation Generation**: <100ms for 10 recommendations
- **Scenario Simulation**: <200ms for 5 scenarios
- **Comparison**: <50ms for ranking
- **API Response Time**: <500ms typical

## Security

- No external API calls required
- No credentials stored
- Project data isolated per project_id
- All outputs deterministic (no randomness)

## Future Enhancements

1. **Machine Learning**: Learn from applied recommendations
2. **Custom Scenarios**: More sophisticated scenario builder
3. **Sensitivity Analysis**: Identify key drivers
4. **Historical Comparison**: Benchmark against similar projects
5. **Predictive Confidence**: Confidence based on project similarity

## Support

For issues or questions:
1. Check test_phase10.py for usage examples
2. Review this documentation
3. Check API integration documentation
4. Contact development team
