# PHASE 21: Automated Material Ordering & Forecasting

## Overview

Phase 21 implements **Automated Material Ordering & Forecasting Intelligence** for the Construction AI Suite. This feature analyzes material stock levels, predicts shortages, and recommends reorder timing and quantities based on project schedules, supplier reliability, and lead times. By preventing material shortages, it reduces schedule delays and cost escalations.

## Problem & Solution

**Problem:**
- Material shortages unexpectedly halt construction tasks
- Procurement decisions are reactive rather than predictive
- Supplier unreliability and long lead times create cascading delays
- No integrated view of material risk across projects

**Solution Phase 21 Provides:**
- Predict material shortages 2–4 weeks in advance
- Recommend proactive reorder timing and quantities
- Account for supplier reliability and lead time variability
- Feed material risk signals into Feature 1's project risk engine
- Provide actionable insights to procurement teams

## Data Models

### Core Types (phase21_material_types.py)

**Material**
- `material_id`: Unique identifier
- `name`: Human-readable name (e.g., "Concrete Grade C40")
- `material_type`: MaterialType enum (CONCRETE, STEEL, LUMBER, DRYWALL, COPPER, ALUMINUM, INSULATION, ROOFING, PIPING, ELECTRICAL, OTHER)
- `unit_type`: UnitType enum (METRIC_TONS, CUBIC_METERS, LINEAR_METERS, PIECES, GALLONS, LITERS, KILOGRAMS, SQUARE_METERS)
- `standard_unit_quantity`: Quantity per standard order unit
- `cost_per_unit`: USD cost per unit
- `description`: Notes on material specifications

**SupplierInfo**
- `supplier_id`: Unique supplier identifier
- `name`: Supplier company name
- `lead_time_days`: Average days from order to delivery
- `reliability_score`: Float 0.0–1.0; fraction of on-time deliveries
- `price_per_unit`: Current supplier price
- `primary_materials`: List of material_ids supplied
- `notes`: Supplier notes (e.g., "minimum order 10 tons")

**StockRecord**
- `project_id`: Project ID for this inventory
- `material_id`: Material being tracked
- `quantity_on_hand`: Current stock level
- `quantity_on_order`: Units already ordered but not yet received
- `reorder_point`: Minimum stock level before automatic reorder trigger
- `last_updated`: ISO timestamp of last inventory update
- `supplier_id`: Primary supplier for this material
- `notes`: Inventory notes

**DemandRecord**
- `project_id`: Project where material is needed
- `task_id`: Task consuming the material
- `material_id`: Material being consumed
- `quantity_needed`: Expected consumption quantity
- `needed_by_date`: ISO date by which material must be available
- `unit_type`: Unit type for this demand
- `task_duration_days`: How long the task runs
- `flexibility_days`: Buffer days before hard deadline
- `notes`: Notes on demand specifics

**MaterialForecast**
- `material_id`: Material being forecast
- `current_stock`: Current inventory level
- `predicted_shortage`: Boolean; True if shortage expected
- `shortage_date`: ISO date when stock reaches zero (if predicted)
- `days_until_shortage`: Days before depletion
- `reorder_needed`: Boolean; True if reorder is urgent
- `reorder_quantity`: Recommended order quantity
- `reorder_urgency`: ForecastUrgency enum (MINIMAL, LOW, MEDIUM, HIGH, CRITICAL)
- `supplier_lead_time_days`: Supplier's typical lead time
- `confidence`: Float 0.0–1.0; confidence in forecast (higher with more historical data)
- `explanation`: Human-readable forecast reasoning
- `recommended_action`: Procurement action (e.g., "Reorder immediately")
- `explainability`: Dict with scoring components (consumption_rate, reliability factor, etc.)

**MaterialRiskInsight**
- `material_id`: Material with identified risk
- `insight_type`: Risk type ('shortage_risk', 'schedule_impact', 'cost_escalation')
- `severity`: 'low', 'medium', 'high', 'critical'
- `description`: Details of the risk
- `affected_tasks`: List of task_ids that would be impacted
- `estimated_delay_days`: Days of schedule delay if shortage occurs
- `estimated_cost_impact`: USD cost impact
- `recommended_action`: Mitigation steps

**MaterialIntelligence** (Project-Level)
- `project_id`: Project being analyzed
- `project_name`: Project name
- `material_summaries`: Dict[material_id] → MaterialHealthSummary
- `material_risk_insights`: List of MaterialRiskInsight objects
- `material_risk_score`: Float 0.0–1.0 (proportion of materials with predicted shortages)
- `project_summary`: Narrative overview of fleet health
- `critical_material_count`: Count of materials at critical shortage risk
- `reorder_recommendations`: List of {material_id, quantity, urgency, reason}
- `schedule_impact_risk`: Float 0.0–1.0 (probability that materials delay project)
- `integration_ready`: Boolean flag for pipeline integration
- `generated_at`: ISO timestamp
- `monday_updates`: Dict of material metrics for monday.com mapping

## Forecasting Algorithm

### Consumption Rate Calculation

```
consumption_rate = total_demand_quantity / (latest_demand_date - earliest_demand_date)
```

Consumption rate (units/day) is derived from scheduled tasks requiring the material and their deadlines.

### Shortage Prediction

```
days_until_empty = current_stock / consumption_rate

shortage_risk_factor = 0.5 + (supplier_reliability × 0.5)  # 0.5-1.0 scale

adjusted_days = days_until_empty × shortage_risk_factor

shortage_date = today + adjusted_days days
```

**Key Points:**
- Lower supplier reliability → earlier shortage warning (wider safety margin)
- Shortage is only flagged if `adjusted_days ≤ 2 × lead_time_days`
- This prevents false positives for slowly-consumed materials

### Reorder Quantity (Economic Order Quantity)

```
lead_time_demand = consumption_rate × lead_time_days

safety_stock = consumption_rate × 30  # Target 30 days of supply

reorder_quantity = lead_time_demand + safety_stock
```

Reorder quantity ensures material covers supplier lead time plus 30-day buffer for demand variability.

### Urgency Classification

| days_until_shortage | Urgency | Action |
|---------------------|---------|--------|
| < 0 | CRITICAL | Order immediately |
| 0–7 | HIGH | Order within 2–3 days |
| 7–14 | MEDIUM | Plan reorder within 1 week |
| > 14 | LOW | Monitor; no urgent action |
| N/A (no shortage) | MINIMAL | Normal monitoring |

## API Endpoints

### POST /api/phase21/material/analyze

Analyze material ordering and forecasting for a project.

**Request Body:**
```json
{
  "project_id": "P001",
  "project_name": "Downtown Renovation",
  "materials": [
    {
      "material_id": "MAT001",
      "name": "Concrete Grade C40",
      "material_type": "CONCRETE",
      "unit_type": "CUBIC_METERS",
      "standard_unit_quantity": 10.0,
      "cost_per_unit": 120.0
    }
  ],
  "suppliers": [
    {
      "supplier_id": "SUP001",
      "name": "Concrete Supply Co",
      "lead_time_days": 7,
      "reliability_score": 0.95,
      "price_per_unit": 120.0,
      "primary_materials": ["MAT001"]
    }
  ],
  "stock_records": [
    {
      "project_id": "P001",
      "material_id": "MAT001",
      "quantity_on_hand": 500.0,
      "quantity_on_order": 200.0,
      "supplier_id": "SUP001",
      "last_updated": "2026-02-04T10:00:00Z"
    }
  ],
  "demand_records": [
    {
      "project_id": "P001",
      "task_id": "TASK_FOUNDATION",
      "material_id": "MAT001",
      "quantity_needed": 100.0,
      "needed_by_date": "2026-02-20",
      "task_duration_days": 10
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "project_id": "P001",
  "project_name": "Downtown Renovation",
  "material_summaries": {
    "MAT001": {
      "material_id": "MAT001",
      "material_name": "Concrete Grade C40",
      "current_stock": 500.0,
      "stock_status": "adequate",
      "total_demand": 100.0,
      "consumption_rate_per_day": 10.0,
      "days_of_supply": 50.0,
      "forecast": {
        "material_id": "MAT001",
        "predicted_shortage": false,
        "shortage_date": null,
        "days_until_shortage": null,
        "reorder_needed": false,
        "reorder_quantity": 0.0,
        "reorder_urgency": "minimal",
        "confidence": 0.85,
        "explanation": "Material stock adequate; no shortage predicted."
      },
      "risks_count": 0
    }
  },
  "material_risk_insights": [],
  "material_risk_score": 0.0,
  "project_summary": "Project 'Downtown Renovation' tracks 1 material(s). 0 flagged with shortage risk. Overall material risk score: 0.0. 0 reorder(s) recommended.",
  "critical_material_count": 0,
  "schedule_impact_risk": 0.0,
  "reorder_recommendations": [],
  "integration_ready": true
}
```

### GET /api/phase21/material/intelligence

Retrieve the last calculated material intelligence (cached).

### GET /api/phase21/material/score-detail

Get detailed breakdown of material risk score components.

### GET /api/phase21/material/monday-mapping

Get material data formatted for monday.com integration.

### GET /api/phase21/material/health

Health check endpoint.

## Integration with Core AI Engine

Phase 21 feeds material risk signals into Feature 1's core risk engine via:

```python
feed_material_to_core_risk_engine(intelligence)
```

This function:
1. Wraps MaterialIntelligence output
2. Attempts to import `core_risk_engine.register_material_risk()`
3. Falls back to logging if unavailable (CI-safe)

**Integration Payload:**
```python
{
  "source": "phase_21_material_ordering",
  "project_id": "P001",
  "material_risk_score": 0.45,
  "critical_material_count": 2,
  "schedule_impact_risk": 0.3,
  "reorder_count": 5,
  "material_summaries": {...},
  "risk_insights": [...]
}
```

**Propagation:**
- Material shortages → project risk increase
- Schedule impact risk → task-level delay predictions
- Cost impact → budget variance warnings

## monday.com Integration

Phase 21 outputs are structured for monday.com mapping:

**Material-Level Columns:**
- Material Stock Level (current inventory)
- Days of Supply (before depletion)
- Shortage Predicted (Yes/No)
- Shortage Date (ISO date when stock runs out)
- Reorder Needed (Yes/No)
- Reorder Urgency (Critical/High/Medium/Low)
- Reorder Quantity (recommended order size)
- Recommended Action (procurement guidance)

**Project-Level Columns:**
- Material Risk Score (0.0–1.0)
- Critical Materials (count)
- Reorders Pending (count)
- Schedule Impact Risk (0.0–1.0)

**Example Mapping via /monday-mapping endpoint:**
```json
{
  "material_updates": [
    {
      "material_id": "MAT001",
      "material_name": "Concrete",
      "current_stock": 500.0,
      "stock_status": "adequate",
      "days_of_supply": 50.0,
      "shortage_predicted": "No",
      "reorder_needed": "No"
    }
  ],
  "project_update": {
    "material_risk_score": 0.0,
    "critical_materials": 0,
    "reorders_needed": 0,
    "schedule_impact_risk": 0.0
  }
}
```

## Testing

**Unit Tests** (test_phase21.py):
- `test_material_health_calculation_adequate_stock`: Verifies adequate stock with normal consumption
- `test_material_shortage_prediction`: Tests shortage detection with high demand
- `test_reorder_quantity_calculation`: Validates EOQ formula with lead time
- `test_project_material_intelligence`: End-to-end project-level intelligence generation
- `test_multiple_materials_and_suppliers`: Multi-material forecasting across suppliers

**Run tests:**
```bash
cd backend
$env:PYTHONPATH='app'; python -m pytest tests/test_phase21.py -v
```

**Expected Output:**
```
test_phase21.py::test_material_health_calculation_adequate_stock PASSED
test_phase21.py::test_material_shortage_prediction PASSED
test_phase21.py::test_reorder_quantity_calculation PASSED
test_phase21.py::test_project_material_intelligence PASSED
test_phase21.py::test_multiple_materials_and_suppliers PASSED
===================== 5 passed in 0.12s =====================
```

## Files

- `backend/app/phase21_material_types.py` — Data models and enums
- `backend/app/phase21_material_analyzer.py` — MaterialOrderingAnalyzer with forecasting logic
- `backend/app/phase21_material_integration.py` — Core engine integration + monday mapping
- `backend/app/phase21_material_api.py` — Flask blueprint endpoints
- `backend/tests/test_phase21.py` — Unit tests (5 tests, all passing)
- `PHASE_21_README.md` — This documentation

## Next Steps

1. **Integrate with Feature 1 Core Risk Engine** — Hook into Phase 1 response pipeline
2. **Add CI/CD Integration Tests** — Dry-run test validating monday.com column mapping (like Feature 18)
3. **Supplier Data Pipeline** — Integrate with external supplier databases (lead times, reliability scores)
4. **Historical Analysis** — Backfill material consumption data from past projects
5. **Demand Forecasting ML** — Enhance consumption rate prediction with time-series forecasting (ARIMA, Prophet)
6. **monday.com Automation** — Trigger auto-reorder workflows when urgency reaches HIGH
7. **Alerts & Notifications** — Notify procurement when material risk increases

## Algorithm Notes

**Deterministic Scoring:**
- All calculations are reproducible; no randomness
- Confidence metric decreases with fewer demand records
- Safety stock targets are configurable (currently 30 days)

**Data Quality Assumptions:**
- `needed_by_date` and `last_updated` are valid ISO date strings
- `consumption_rate` is derived from task schedule, not historical usage (for new projects)
- Supplier reliability scores reflect past on-time delivery fraction

**Confidence Calibration:**
- With 1 demand record: confidence = 0.6 (uncertain consumption pattern)
- With 2+ demand records: confidence = 0.85 (reasonable pattern visibility)

**Failure Modes & Handling:**
- Missing supplier: defaults to 14-day lead time, 0.85 reliability
- No demands for a material: no shortage predicted
- Consumption rate ≤ 0: treated as no demand; no shortage predicted

## Enterprise Considerations

- **Audit Trail:** All forecasts are timestamped and include explainability dict
- **Backward Compatibility:** If core_risk_engine is unavailable, analyzer logs warning and continues
- **Scalability:** Analyzer supports N materials, M suppliers, K demand records per project
- **Cost Tracking:** Material costs are aggregated for project-level budget impact
- **Supplier Diversification:** Can associate multiple suppliers per material for resilience analysis

## References

- Feature 1: Core AI Project Risk & Delay Intelligence
- Feature 2: Smart Schedule Dependencies & Delay Propagation
- Feature 3: Workforce Reliability & Attendance Intelligence
- Feature 4: Subcontractor Performance Intelligence
- Feature 5: Predictive Equipment Maintenance
- Phase 14–16: monday.com Integration Framework
