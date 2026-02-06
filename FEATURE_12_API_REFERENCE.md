# Feature 12: API Reference

## Base URL
```
/api/portfolio
```

## Authentication
No authentication required for local deployment. All endpoints return JSON.

---

## 1. Aggregate Portfolio
**Endpoint**: `POST /api/portfolio/aggregate`

**Purpose**: Combine project-level data into portfolio risk exposure.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "projects": [
    {
      "project_id": "P001",
      "project_name": "North Tower",
      "client": "ABC Construction",
      "region": "North",
      "program": "Build Phase 1",
      "division": "Civil Works",
      "current_budget": 500000,
      "original_budget": 500000,
      "current_cost": 200000,
      "forecasted_final_cost": 480000,
      "original_end_date": "2024-06-30",
      "current_end_date": "2024-07-10",
      "delay_risk_score": 0.35,
      "cost_risk_score": 0.25,
      "resource_risk_score": 0.20,
      "safety_risk_score": 0.10,
      "overall_risk_score": 0.55,
      "total_tasks": 150,
      "completed_tasks": 60,
      "unallocated_tasks": 12,
      "total_workers": 20,
      "average_worker_reliability": 0.82,
      "last_updated": "2024-01-15T10:00:00",
      "data_confidence": 0.88
    }
  ],
  "view_type": "client"
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "view_type": "client",
  "grouping_key": "ABC Construction",
  "portfolio_risk_score": 0.52,
  "risk_level": "MEDIUM",
  "delay_risk_score": 0.32,
  "cost_risk_score": 0.24,
  "resource_risk_score": 0.19,
  "safety_risk_score": 0.10,
  "compliance_risk_score": 0.05,
  "critical_projects": [],
  "at_risk_projects": ["P001"],
  "healthy_projects": [],
  "total_projects": 1,
  "total_budget": 500000,
  "total_cost_to_date": 200000,
  "forecasted_total_cost": 480000,
  "total_schedule_variance_days": 10,
  "total_cost_variance": -0.04,
  "average_workforce_reliability": 0.82,
  "total_resource_gaps": 12,
  "risk_trend": "stable",
  "risk_trend_magnitude": 0.0,
  "project_count_in_calc": 1,
  "confidence_score": 0.88
}
```

### Error Responses
- **400**: Missing `portfolio_id` or `projects` array
- **500**: Server error

---

## 2. Identify Risk Drivers
**Endpoint**: `POST /api/portfolio/drivers`

**Purpose**: Detect systemic risk patterns affecting multiple projects.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "exposure": {
    "portfolio_id": "PORT-ABC-2024",
    "portfolio_risk_score": 0.65,
    "delay_risk_score": 0.40,
    "cost_risk_score": 0.35,
    "risk_level": "HIGH",
    "critical_projects": ["P001", "P002"],
    "at_risk_projects": ["P003"]
  },
  "projects": [...]
}
```

### Response (200 OK)
```json
[
  {
    "driver_id": "DRV-DELAY-PORT-ABC-2024",
    "driver_name": "Schedule Delay Risk",
    "description": "Multiple projects facing schedule delay",
    "risk_category": "delay",
    "affected_project_count": 2,
    "total_impact_weight": 0.40,
    "percentage_of_portfolio_risk": 0.615,
    "affected_projects": [
      ["P001", 0.70],
      ["P002", 0.60]
    ],
    "examples": [
      "P001: 10 days behind",
      "P002: 8 days behind"
    ],
    "trend": "persistent",
    "recommended_actions": [
      "Increase crew sizes for critical path",
      "Accelerate material procurement",
      "Implement daily schedule tracking"
    ]
  },
  {
    "driver_id": "DRV-COST-PORT-ABC-2024",
    "driver_name": "Cost Overrun Risk",
    "description": "Projects exceeding budgets",
    "risk_category": "cost",
    "affected_project_count": 1,
    "total_impact_weight": 0.35,
    "percentage_of_portfolio_risk": 0.538,
    "affected_projects": [["P002", 0.65]],
    "examples": ["P002: $50,000 over budget"],
    "trend": "degrading"
  }
]
```

---

## 3. Generate Executive Summary
**Endpoint**: `POST /api/portfolio/summary`

**Purpose**: Create executive-friendly portfolio findings.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "exposure": { ...PortfolioRiskExposure... },
  "projects": [ ...ProjectSnapshot... ]
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "report_date": "2024-01-15T10:30:00",
  "report_period": "weekly",
  "project_count": 3,
  "portfolio_health_score": 55.0,
  "overall_risk_level": "HIGH",
  "headline": "3 projects in ABC Construction: 1 healthy, 1 at risk, 1 critical",
  "key_findings": [
    "1 project at critical risk, representing $250,000",
    "Portfolio behind schedule by 18 days, driven by 2 delayed projects",
    "Cost exposure: estimated overrun of $45,000 (9%)"
  ],
  "top_risks": [
    "Schedule Delay Risk",
    "Cost Overrun Risk",
    "Workforce Reliability"
  ],
  "on_time_projects": 1,
  "delayed_projects": 2,
  "over_budget_projects": 1,
  "critical_risk_projects": 1,
  "total_portfolio_value": 1500000,
  "cumulative_at_risk_value": 450000,
  "potential_cost_overrun": 45000
}
```

---

## 4. Generate Trends
**Endpoint**: `POST /api/portfolio/trends`

**Purpose**: Analyze portfolio trends with future projections.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "current_exposure": { ...PortfolioRiskExposure... },
  "time_period": "weekly",
  "comparison_exposures": [
    { ...PortfolioRiskExposure from 1 week ago... },
    { ...PortfolioRiskExposure from 2 weeks ago... }
  ]
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "timestamp": "2024-01-15T10:30:00",
  "time_period": "weekly",
  "risk_score": 0.62,
  "risk_level": "HIGH",
  "trend_direction": "degrading",
  "trend_magnitude": 0.05,
  "key_metrics": {
    "delay_risk": 0.38,
    "cost_risk": 0.34,
    "resource_risk": 0.22,
    "safety_risk": 0.11,
    "workforce_reliability": 0.79
  },
  "metrics_trend": {
    "delay_trend": "degrading",
    "cost_trend": "stable",
    "resource_trend": "improving",
    "safety_trend": "stable"
  },
  "projected_score_date": "2024-01-22T10:30:00",
  "projected_score": 0.67,
  "confidence_interval_lower": 0.57,
  "confidence_interval_upper": 0.77,
  "data_completeness": 0.85
}
```

---

## 5. Period Comparison
**Endpoint**: `POST /api/portfolio/comparison`

**Purpose**: Compare portfolio metrics between two periods (WoW/MoM).

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "current_exposure": { ...PortfolioRiskExposure this week... },
  "previous_exposure": { ...PortfolioRiskExposure last week... }
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "current_period_start": "2024-01-08",
  "current_period_end": "2024-01-15",
  "previous_period_start": "2024-01-01",
  "previous_period_end": "2024-01-08",
  "current_risk_score": 0.62,
  "previous_risk_score": 0.57,
  "risk_score_change": 0.05,
  "risk_score_change_pct": 8.77,
  "risk_level_change": "escalated",
  "critical_projects_change": 1,
  "at_risk_projects_change": 0,
  "total_projects_change": 0,
  "budget_change": 0,
  "cost_variance_change": 0.02,
  "schedule_variance_change_days": 5,
  "health_score_delta": -3.5,
  "key_changes": [
    "+1 project(s) now critical",
    "Schedule variance worsened by 5 days"
  ],
  "data_quality": "high"
}
```

---

## 6. Generate Recommendations
**Endpoint**: `POST /api/portfolio/recommendations`

**Purpose**: Generate actionable recommendations based on portfolio state.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "exposure": { ...PortfolioRiskExposure... },
  "drivers": [ ...RiskDriver... ],
  "projects": [ ...ProjectSnapshot... ],
  "feature11_allocations": { ...optional Feature 11 data... },
  "feature10_recommendations": { ...optional Feature 10 data... }
}
```

### Response (200 OK)
```json
[
  {
    "id": "REC-CRITICAL-PORT-ABC-2024",
    "title": "Immediate intervention required for critical projects",
    "priority": "critical",
    "affected_projects": ["P001", "P002"],
    "affected_project_count": 2,
    "impact": "$450,000 at immediate risk",
    "recommended_actions": [
      "Schedule immediate project reviews with stakeholders",
      "Activate escalation procedures per project protocols",
      "Allocate additional resources to resolve blockers"
    ],
    "success_metrics": [
      "1+ critical projects move to at-risk within 1 week",
      "Schedule variance reduced by 20%"
    ],
    "generated_at": "2024-01-15T10:30:00"
  },
  {
    "id": "REC-SCHEDULE-PORT-ABC-2024",
    "title": "Execute schedule recovery plan",
    "priority": "high",
    "delayed_projects": 2,
    "total_variance_days": 18,
    "recommended_actions": [
      "Identify and resolve schedule constraints (critical path analysis)",
      "Increase crew sizes for longest-pole activities",
      "Execute weekend/overtime work with ROI approval"
    ],
    "success_metrics": [
      "Recover 6 days within 2 weeks",
      "Get 50% of delayed projects back to schedule"
    ]
  }
]
```

---

## 7. Get Portfolio Insights
**Endpoint**: `POST /api/portfolio/insights`

**Purpose**: Comprehensive portfolio snapshot for executive dashboards.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "exposure": { ...PortfolioRiskExposure... },
  "summary": { ...ExecutiveSummary... },
  "drivers": [ ...RiskDriver... ]
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "report_time": "2024-01-15T10:30:00",
  "executive_summary": {
    "health_score": 55.0,
    "risk_level": "HIGH",
    "headline": "3 projects in ABC Construction portfolio",
    "key_findings": ["1 at critical risk", "18 days behind schedule"]
  },
  "portfolio_metrics": {
    "total_projects": 3,
    "project_health": {
      "healthy": 1,
      "at_risk": 1,
      "critical": 1
    },
    "total_budget": 1500000,
    "total_cost": 600000,
    "forecast": 1545000
  },
  "risk_breakdown": {
    "delay_risk": 0.38,
    "cost_risk": 0.34,
    "resource_risk": 0.22,
    "safety_risk": 0.11,
    "compliance_risk": 0.05
  },
  "top_risks": [
    {
      "driver": "Schedule Delay Risk",
      "category": "delay",
      "impact": "61.5%",
      "affected_projects": 2,
      "trend": "persistent"
    }
  ],
  "performance_indicators": {
    "on_schedule": 1,
    "delayed": 2,
    "cost_overrun_projects": 1,
    "schedule_variance_days": 18,
    "cost_variance_pct": 0.03,
    "workforce_reliability": 0.79,
    "resource_gaps": 8
  },
  "confidence": {
    "data_quality": 0.84,
    "recommendation_confidence": "high"
  }
}
```

---

## 8. Convert to Monday.com Format
**Endpoint**: `POST /api/portfolio/monday-format`

**Purpose**: Convert portfolio data to Monday.com dashboard format.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "portfolio_name": "ABC Construction Portfolio",
  "summary_metrics": {
    "health_score": 55.0,
    "risk_score": 0.62,
    "total_projects": 3,
    "critical_projects": 1,
    "at_risk_projects": 1
  }
}
```

### Response (200 OK)
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "portfolio_name": "ABC Construction Portfolio",
  "board_type": "portfolio_dashboard",
  "sync_timestamp": "2024-01-15T10:30:00",
  "board_items": [
    {
      "item_id": "health-metric",
      "type": "metric",
      "name": "Portfolio Health",
      "value": 55.0,
      "format": "percentage",
      "threshold_warning": 60,
      "threshold_critical": 40
    },
    {
      "item_id": "risk-indicator",
      "type": "status",
      "name": "Risk Level",
      "value": "HIGH",
      "color": "orange"
    },
    {
      "item_id": "project-status",
      "type": "group",
      "name": "Project Status",
      "breakdown": {
        "healthy": 1,
        "at_risk": 1,
        "critical": 1
      }
    }
  ],
  "last_sync": "2024-01-15T10:30:00",
  "next_sync": "2024-01-15T10:45:00",
  "access_level": "view_only"
}
```

---

## 9. Create Monday.com Dashboard Structure
**Endpoint**: `POST /api/portfolio/monday-dashboard`

**Purpose**: Pre-configure Monday.com dashboard structure.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "portfolio_name": "ABC Construction",
  "is_summary": false
}
```

### Response (200 OK)
```json
{
  "board_name": "Portfolio: ABC Construction",
  "board_description": "Executive portfolio intelligence and dashboard",
  "widgets": [
    {
      "type": "metric",
      "name": "Portfolio Health",
      "field": "portfolio_health_score",
      "format": "percentage"
    },
    {
      "type": "metric",
      "name": "Overall Risk",
      "field": "portfolio_risk_score",
      "format": "risk_level"
    },
    {
      "type": "summary",
      "name": "Project Status",
      "breakdown": ["critical", "at_risk", "healthy"]
    },
    {
      "type": "timeline",
      "name": "Schedule Variance",
      "field": "schedule_variance_days"
    },
    {
      "type": "kpi",
      "name": "Budget",
      "fields": ["total_budget", "forecasted_cost", "cost_variance"]
    },
    {
      "type": "heatmap",
      "name": "Risk Heatmap",
      "dimensions": ["projects", "risk_factors"]
    }
  ],
  "auto_refresh": true,
  "refresh_interval_minutes": 15,
  "access_level": "view_only",
  "no_api_required": true,
  "data_source": "Feature 12 Portfolio Intelligence"
}
```

---

## 10. Batch Update for Monday.com
**Endpoint**: `POST /api/portfolio/monday-batch-update`

**Purpose**: Sync multiple portfolios to Monday.com efficiently.

### Request
```json
{
  "portfolios": [
    {
      "portfolio_id": "PORT-ABC-2024",
      "portfolio_name": "ABC Construction",
      "summary_metrics": { ...metrics1... }
    },
    {
      "portfolio_id": "PORT-XYZ-2024",
      "portfolio_name": "XYZ Contractors",
      "summary_metrics": { ...metrics2... }
    }
  ]
}
```

### Response (200 OK)
```json
{
  "update_timestamp": "2024-01-15T10:30:00",
  "portfolio_count": 2,
  "updates": [
    { ...monday_format_1... },
    { ...monday_format_2... }
  ],
  "sync_required": true,
  "sync_strategy": "upsert",
  "estimated_sync_duration_ms": 250
}
```

---

## 11. Integrate Feature Data
**Endpoint**: `POST /api/portfolio/integrate`

**Purpose**: Build integrated context from multiple features.

### Request
```json
{
  "projects": [ ...ProjectSnapshot... ],
  "feature9_risks": [
    {
      "project_id": "P001",
      "risk_score": 0.6,
      "risk_drivers": ["Schedule pressure"]
    }
  ],
  "feature10_recommendations": [
    {
      "project_id": "P001",
      "recommendations": [
        {"title": "Increase resources", "urgency": "critical"}
      ]
    }
  ],
  "feature11_allocations": [
    {
      "project_id": "P001",
      "allocation_percentage": 85
    }
  ]
}
```

### Response (200 OK)
```json
{
  "project_count": 1,
  "integration_timestamp": "2024-01-15T10:30:00",
  "base_data": {
    "projects": 1,
    "total_budget": 500000
  },
  "feature_integrations": {
    "feature9_risk": {
      "portfolio_overall_risk": 0.55,
      "systemic_risk_drivers": ["Schedule pressure"]
    },
    "feature10_recommendations": {
      "critical_count": 1,
      "examples": ["Increase resources"]
    },
    "feature11_allocations": {
      "allocation_rate": 85.0,
      "unallocated_tasks": 15
    }
  }
}
```

---

## 12. Trace Risk to Root Cause
**Endpoint**: `POST /api/portfolio/trace-risk`

**Purpose**: Map portfolio risk back to feature origins for traceability.

### Request
```json
{
  "portfolio_id": "PORT-ABC-2024",
  "exposure": { ...PortfolioRiskExposure... },
  "feature9_data": { ...Feature 9 output... },
  "feature10_data": { ...Feature 10 output... },
  "feature11_data": { ...Feature 11 output... }
}
```

### Response (200 OK)
```json
{
  "portfolio_risk_score": 0.62,
  "risk_components": {
    "delay_risk": {
      "score": 0.38,
      "source": "Feature 9 delay synthesis",
      "projects_affected": 2
    },
    "cost_risk": {
      "score": 0.34,
      "source": "Feature 10 cost forecast",
      "projects_affected": 1
    },
    "resource_risk": {
      "score": 0.22,
      "source": "Feature 11 allocation gaps",
      "allocation_rate": 85.0
    }
  },
  "integration_status": {
    "feature9_integrated": true,
    "feature10_integrated": true,
    "feature11_integrated": true
  },
  "traceability_depth": "full",
  "trace_timestamp": "2024-01-15T10:30:00"
}
```

---

## 13. Health Check
**Endpoint**: `GET /api/portfolio/health`

**Purpose**: Verify service health and available endpoints.

### Response (200 OK)
```json
{
  "status": "healthy",
  "service": "Feature 12 Portfolio Intelligence",
  "timestamp": "2024-01-15T10:30:00",
  "endpoints": {
    "aggregate": "POST /api/portfolio/aggregate",
    "drivers": "POST /api/portfolio/drivers",
    "summary": "POST /api/portfolio/summary",
    "trends": "POST /api/portfolio/trends",
    "comparison": "POST /api/portfolio/comparison",
    "recommendations": "POST /api/portfolio/recommendations",
    "insights": "POST /api/portfolio/insights",
    "monday-format": "POST /api/portfolio/monday-format",
    "monday-dashboard": "POST /api/portfolio/monday-dashboard",
    "monday-batch": "POST /api/portfolio/monday-batch-update",
    "integrate": "POST /api/portfolio/integrate",
    "trace-risk": "POST /api/portfolio/trace-risk",
    "health": "GET /api/portfolio/health"
  }
}
```

---

## Common Error Responses

### 400 - Bad Request
```json
{
  "error": "portfolio_id required"
}
```

### 500 - Server Error
```json
{
  "error": "Error aggregating portfolio: [specific error message]"
}
```

---

## Data Types Reference

### PortfolioViewType
```
- "client": Group by client
- "region": Group by region
- "program": Group by program
- "division": Group by division
- "portfolio": No grouping (all projects)
```

### RiskLevel
```
- "LOW": 0.0 - 0.35
- "MEDIUM": 0.35 - 0.60
- "HIGH": 0.60 - 0.80
- "CRITICAL": 0.80 - 1.0
```

### TimePeriod
```
- "weekly": 7-day period
- "monthly": 30-day period
- "quarterly": 90-day period
```

### RecommendationPriority
```
- "critical": Immediate action required
- "high": Urgent but not immediate
- "medium": Should address within 1-2 weeks
- "low": Nice to have improvements
```

---

## Rate Limiting

Currently no rate limiting. In production:
- Recommend: 100 requests per minute per portfolio
- Batch endpoints: 10 portfolios per request maximum

---

## Changelog

### v1.0 (Released)
- Initial Portfolio Intelligence feature
- 13 endpoints
- Monday.com integration
- Cross-feature data integration
