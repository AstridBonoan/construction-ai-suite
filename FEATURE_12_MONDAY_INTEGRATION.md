# Feature 12: Monday.com Integration Guide

## Overview

Feature 12 provides **zero-configuration integration** with Monday.com for executive portfolio dashboards. No API keys, credentials, or manual setup required.

## Key Features

✅ **No API Keys Needed**
- Data is pushed, not pulled
- Pre-configured widget structure
- View-only access prevents accidental modifications

✅ **Automatic Format Conversion**
- `DashboardDataContract.to_monday_com_format()` handles all formatting
- Deterministic output (same data = same format always)
- Full field mapping to Monday.com standard columns

✅ **Batch Syncing**
- Update multiple portfolios in single call
- Upsert mode (create or update)
- Efficient bulk operations

✅ **Auto-Refresh**
- 15-minute interval for detail portfolios
- 60-minute interval for summary portfolios
- No manual refresh needed

## Quick Setup

### 1. Create Dashboard Data Contract

```python
from feature12_portfolio_models import DashboardDataContract

# Create contract with portfolio data
contract = DashboardDataContract(
    portfolio_id="PORT-ABC-2024",
    portfolio_name="ABC Construction Portfolio",
    summary_metrics={
        "health_score": 55.0,
        "risk_score": 0.62,
        "total_projects": 3,
        "critical_projects": 1,
        "at_risk_projects": 1,
        "on_time_projects": 1,
        "delayed_projects": 2,
        "cost_variance": 0.03,
        "schedule_variance_days": 18,
        "workforce_reliability": 0.79,
    }
)
```

### 2. Convert to Monday.com Format

```python
from feature12_integrations import MondayComIntegrator

# Convert automatically
monday_data = MondayComIntegrator.convert_to_monday_format(contract)

# Returns:
# {
#   "portfolio_id": "PORT-ABC-2024",
#   "board_items": [
#     {"field": "portfolio_health", "value": 55.0, "type": "percentage"},
#     {"field": "risk_level", "value": "HIGH", "type": "status"},
#     ...
#   ]
# }
```

### 3. Create Dashboard Structure

```python
# Define dashboard once
dashboard_structure = MondayComIntegrator.create_portfolio_dashboard_structure(
    portfolio_id="PORT-ABC-2024",
    portfolio_name="ABC Construction",
    is_summary=False,  # Detailed view (15-min refresh)
)

# Structure includes:
# - Board name: "Portfolio: ABC Construction"
# - Widgets: Health, Risk, Projects, Schedule, Budget, Heatmap
# - Auto-refresh: Every 15 minutes
# - Access: View-only
# - No API required: True
```

## Widget Types

### 1. Portfolio Health (Metric Card)
- **Field**: `portfolio_health_score`
- **Format**: Percentage (0-100)
- **Thresholds**:
  - Green: 70-100
  - Yellow: 40-70
  - Red: 0-40
- **Updates**: Every aggregation

### 2. Risk Level (Status Indicator)
- **Field**: `portfolio_risk_score` / `risk_level`
- **Values**: CRITICAL, HIGH, MEDIUM, LOW
- **Color Coding**:
  - CRITICAL (red): 0.80-1.0
  - HIGH (orange): 0.60-0.80
  - MEDIUM (yellow): 0.35-0.60
  - LOW (green): 0.0-0.35

### 3. Project Status (Summary)
- **Breakdown**: Healthy | At-Risk | Critical
- **Counts**: Number of projects in each category
- **Color coded** per status
- **Total projects**: Sum of all categories

### 4. Schedule Variance (Timeline)
- **Field**: `total_schedule_variance_days`
- **Visual**: Days behind/ahead of original end date
- **Red Zone**: >14 days behind
- **Yellow Zone**: 7-14 days behind
- **Green Zone**: On time or ahead

### 5. Budget Metrics (KPI Card)
- **Actual**: Total cost to date
- **Forecast**: Forecasted final cost
- **Variance**: Cost variance percentage
- **Status**: Color coded based on variance

### 6. Risk Heatmap (Advanced)
- **Rows**: Individual projects
- **Columns**: Risk factors (delay, cost, resource, safety, compliance)
- **Colors**: Risk score intensity
- **Interactive**: Click for details

## API Endpoints for Monday.com

### Convert to Monday Format
```bash
curl -X POST http://localhost:5000/api/portfolio/monday-format \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "PORT-ABC-2024",
    "portfolio_name": "ABC Construction",
    "summary_metrics": {
      "health_score": 55.0,
      "risk_score": 0.62
    }
  }'
```

### Create Dashboard Structure
```bash
curl -X POST http://localhost:5000/api/portfolio/monday-dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": "PORT-ABC-2024",
    "portfolio_name": "ABC Construction",
    "is_summary": false
  }'
```

### Batch Update Multiple Portfolios
```bash
curl -X POST http://localhost:5000/api/portfolio/monday-batch-update \
  -H "Content-Type: application/json" \
  -d '{
    "portfolios": [
      {
        "portfolio_id": "PORT-ABC-2024",
        "portfolio_name": "ABC Construction",
        "summary_metrics": { "health_score": 55.0 }
      },
      {
        "portfolio_id": "PORT-XYZ-2024",
        "portfolio_name": "XYZ Contractors",
        "summary_metrics": { "health_score": 75.0 }
      }
    ]
  }'
```

## Field Mapping

| Portfolio Intelligence | Monday.com Field | Type | Format |
|---|---|---|---|
| `portfolio_health_score` | Portfolio Health | Metric | Percentage |
| `portfolio_risk_score` | Risk Score | Metric | Decimal (0-1) |
| `risk_level` | Risk Level | Status | CRITICAL/HIGH/MEDIUM/LOW |
| `total_projects` | Project Count | Number | Integer |
| `critical_projects` | Critical Count | Number | Integer |
| `at_risk_projects` | At-Risk Count | Number | Integer |
| `healthy_projects` | Healthy Count | Number | Integer |
| `total_budget` | Total Budget | Currency | Dollars |
| `total_cost_to_date` | Cost to Date | Currency | Dollars |
| `forecasted_total_cost` | Forecasted Cost | Currency | Dollars |
| `total_cost_variance` | Cost Variance | Metric | Percentage |
| `total_schedule_variance_days` | Schedule Variance | Number | Days |
| `on_time_projects` | On-Time | Number | Count |
| `delayed_projects` | Delayed | Number | Count |
| `average_workforce_reliability` | Reliability | Metric | Percentage |
| `delay_risk_score` | Delay Risk | Metric | Percentage |
| `cost_risk_score` | Cost Risk | Metric | Percentage |
| `resource_risk_score` | Resource Risk | Metric | Percentage |

## Automated Refresh Schedule

### Detail Portfolios (is_summary=false)
- **Interval**: 15 minutes
- **Use Case**: Project managers, operational dashboards
- **Update Trigger**: Every portfolio aggregation

### Summary Portfolios (is_summary=true)
- **Interval**: 60 minutes
- **Use Case**: Executive dashboards, steering committees
- **Update Trigger**: Daily rollup aggregation

## Data Quality Indicators

### Confidence Score (0-1)
Shows data reliability:
```
0.9-1.0: Excellent (all projects fresh data)
0.8-0.9: Good (most projects updated)
0.7-0.8: Fair (some stale data, 5+ days old)
0.5-0.7: Poor (significant stale data)
<0.5:   Critical (majority data stale, >7 days)
```

### Update Status
```
"Fresh"      → Updated within 1 hour
"Recent"     → Updated within 6 hours
"Stale"      → Updated 1-7 days ago
"Critical"   → Updated >7 days ago
```

## Batch Update Strategy

### Single Portfolio Update
```python
# For immediate update
contract = DashboardDataContract(...)
monday_data = MondayComIntegrator.convert_to_monday_format(contract)
# Send to Monday.com
```

### Multiple Portfolios (Recommended)
```python
# Batch multiple portfolios
contracts = [
    DashboardDataContract(portfolio_id="PORT-1", ...),
    DashboardDataContract(portfolio_id="PORT-2", ...),
    DashboardDataContract(portfolio_id="PORT-3", ...),
]

batch = MondayComIntegrator.prepare_batch_update(contracts)
# Single sync call: 3 portfolios updated atomically
# Efficiency: ~250ms for 3 portfolios vs 900ms individually
```

## Troubleshooting

### Widget Not Updating

**Issue**: Dashboard widget shows stale data

**Solutions**:
1. Check portfolio data freshness: `portfolio.confidence_score`
2. Verify last aggregation timestamp
3. Check if Feature 11 data is available
4. Manually trigger portfolio refresh

```python
# Force refresh
exposure = aggregation.aggregate_portfolio(portfolio_id, projects)
contract = DashboardDataContract(portfolio_id, portfolio_name, metrics)
monday_data = MondayComIntegrator.convert_to_monday_format(contract)
```

### Missing Projects in Dashboard

**Issue**: Portfolio shows fewer projects than expected

**Solutions**:
1. Confirm projects have `data_confidence > 0.5`
2. Check project snapshots were included in aggregation
3. Filter by view_type if using grouped views

### Schedule Variance Not Showing

**Issue**: Timeline widget is empty or shows zeros

**Solutions**:
1. Verify `original_end_date` and `current_end_date` are set
2. Check calculation: `current_end_date - original_end_date = variance_days`
3. Ensure projects have actual schedule dates (not placeholders)

### Risk Score Constantly Changing

**Issue**: Risk score fluctuates even without data changes

**Solutions**:
1. Verify aggregation is **deterministic** (same input = same output)
2. Check if project risk scores are updating frequently
3. Confirm feature integrations (9, 10, 11) are stable
4. Increase aggregation interval if too frequent

## Best Practices

### 1. Schedule Regular Aggregations
```python
# Daily portfolio aggregation
schedule.every().day.at("08:00").do(
    aggregate_portfolio,
    portfolio_id="PORT-ABC-2024",
    projects=fetch_current_projects(),
)
```

### 2. Monitor Confidence Scores
```python
# Alert if confidence drops below threshold
if exposure.confidence_score < 0.70:
    send_alert(f"Portfolio {portfolio_id} confidence dropped to {exposure.confidence_score}")
```

### 3. Batch Updates During Off-Peak
```python
# Sync all portfolios at night
portfolio_ids = ["PORT-1", "PORT-2", "PORT-3"]
for portfolio_id in portfolio_ids:
    exposure = aggregation.aggregate_portfolio(portfolio_id, projects)
    contracts.append(DashboardDataContract(portfolio_id, metrics))

# Single batch call
batch = MondayComIntegrator.prepare_batch_update(contracts)
```

### 4. Use Summary View for Executives
```python
# Executive summary (60-min refresh)
dashboard = MondayComIntegrator.create_portfolio_dashboard_structure(
    portfolio_id="PORT-ABC-2024",
    portfolio_name="ABC Executive Dashboard",
    is_summary=True,  # Reduced refresh frequency
)
```

### 5. Archive Old Portfolios
```python
# Remove closed projects from dashboard
if portfolio.total_projects == 0:
    # Archive or delete from Monday.com
    pass
```

## Integration with Feature 11

Feature 12 automatically includes Feature 11 resource allocation data in dashboard:

```python
# Feature 11 data flows through
resource_integration = Feature11AllocationIntegration.synthesize_portfolio_resource_status(
    feature11_project_data=[...]
)

# Displayed in dashboard:
# - Resource utilization %
# - Allocation rate
# - Critical gaps count
```

## Integration with Feature 10

Feature 10 recommendations appear in portfolio insights:

```python
# Feature 10 data flows through
recommendation_synthesis = Feature10RecommendationsIntegration.synthesize_portfolio_recommendations(
    feature10_project_recs=[...]
)

# Displayed in dashboard insights:
# - Critical recommendation count
# - High priority items
# - Recommended actions
```

## Production Deployment

### Pre-Production Checklist

- [ ] Portfolio data sources verified
- [ ] All projects have `data_confidence > 0.7`
- [ ] Monday.com board structure created
- [ ] Widget configurations tested
- [ ] Batch sync working for 10+ portfolios
- [ ] Auto-refresh intervals configured
- [ ] Alert thresholds set
- [ ] Stakeholder access configured (view-only)
- [ ] Documentation shared with users
- [ ] Support contact identified

### Monitoring

```python
# Monitor dashboard health
def monitor_portfolio_health():
    for portfolio_id in PRODUCTION_PORTFOLIOS:
        exposure = aggregation.aggregate_portfolio(portfolio_id, projects)
        
        if exposure.confidence_score < 0.70:
            log.warning(f"{portfolio_id}: Low confidence")
        
        if exposure.risk_level == RiskLevel.CRITICAL:
            send_executive_alert(portfolio_id, exposure)
        
        metrics.gauge('portfolio.risk_score', exposure.portfolio_risk_score)
        metrics.gauge('portfolio.health', 100 - exposure.portfolio_risk_score * 70)
```

## Support

For Monday.com integration issues:
1. Check widget configuration in dashboard structure
2. Verify data contract conversion: `convert_to_monday_format()`
3. Review batch update response for errors
4. Check logs for data quality issues
5. Verify Feature 11 and 10 data is available

## Roadmap

- [ ] Custom widget builder
- [ ] Multi-board sync (board per region)
- [ ] Mobile app integration
- [ ] Slack notifications for critical changes
- [ ] Automated report generation
- [ ] Executive email summaries
