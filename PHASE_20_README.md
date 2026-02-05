# PHASE 20: Predictive Equipment Maintenance

## Overview

Phase 20 implements **Predictive Equipment Maintenance Intelligence** for the Construction AI Suite. This feature analyzes equipment health by combining historical maintenance patterns, failure events, and overdue maintenance status to predict failure risk and guide preventive interventions at the project level.

## Data Models

### Core Types (phase20_equipment_types.py)

**Equipment**
- `equipment_id`: Unique identifier for the equipment asset
- `name`: Human-readable name
- `equipment_type`: EquipmentType enum (EXCAVATOR, CRANE, CONCRETE_PUMP, COMPRESSOR, GENERATOR, BULLDOZER, OTHER)
- `acquisition_date`: Date equipment was purchased
- `current_status`: EquipmentStatus enum (OPERATIONAL, MAINTENANCE_DUE, MAINTENANCE_OVERDUE, FAILED, OUT_OF_SERVICE)
- `location`: Current project or facility location
- `operator_id`: (Optional) Assigned operator user ID for monday.com integration

**MaintenanceRecord**
- `project_id`: Project where maintenance occurred
- `equipment_id`: Equipment receiving maintenance
- `maintenance_date`: Date of maintenance
- `maintenance_type`: 'preventive' | 'corrective' | 'inspection'
- `duration_hours`: Hours spent on maintenance
- `cost`: USD cost of maintenance
- `completed`: Boolean indicating completion status

**FailureEvent**
- `project_id`: Project where failure occurred
- `task_id`: Task that was interrupted
- `equipment_id`: Equipment that failed
- `failure_date`: Date of failure
- `failure_type`: e.g. 'engine_failure', 'hydraulic_failure', 'electrical_failure'
- `repair_duration_hours`: Hours to repair
- `repair_cost`: USD cost of repair
- `downtime_impact_days`: Project delay caused by failure

**EquipmentHealthSummary**
- `equipment_id`: Equipment being assessed
- `name`: Equipment name
- `failure_probability`: Float 0.0–1.0 (combination of past failure rate + overdue maintenance)
- `risk_level`: 'minimal' | 'low' | 'medium' | 'high' | 'critical'
- `total_maintenance_events`: Count of maintenance records
- `total_failure_events`: Count of failures in history
- `days_since_last_maintenance`: Days since last maintenance action
- `explanation`: Human-readable description of health status
- `recommended_action`: e.g., "Schedule preventive maintenance immediately" or "Monitor closely"
- `integration_ready`: Boolean (always True if calculation succeeds)
- `generated_at`: ISO timestamp of calculation

**EquipmentRiskInsight**
- `equipment_id`: Equipment with risk
- `name`: Equipment name
- `insight_type`: 'high_failure_risk' | 'maintenance_overdue' | 'age_concern' | 'frequency_concern'
- `severity`: 'low' | 'medium' | 'high' | 'critical'
- `description`: Details of the risk condition
- `recommended_action`: Mitigation steps

**EquipmentIntelligence** (Project-Level)
- `project_id`: Project being analyzed
- `project_name`: Project name
- `equipment_summaries`: Dict[equipment_id] → EquipmentHealthSummary
- `equipment_risk_insights`: List of EquipmentRiskInsight objects (for equipment with issues)
- `equipment_risk_score`: Float 0.0–1.0 (average of failure_probabilities across equipment)
- `project_summary`: Aggregated description of fleet health
- `critical_equipment_count`: Count of equipment with risk_level='critical'
- `integration_ready`: Boolean flag for pipeline integration
- `generated_at`: ISO timestamp

## Failure Risk Algorithm

The **Failure Probability** calculation combines two factors:

```
failure_probability = base_probability + overdue_probability

where:
  base_probability = (recent_failures_per_year × 0.2)
  overdue_probability = (days_since_last_maintenance / maintenance_interval × 0.1) capped at 0.5
```

**Risk Level Mapping:**
- **minimal**: failure_probability ≤ 0.1
- **low**: 0.1 < failure_probability ≤ 0.25
- **medium**: 0.25 < failure_probability ≤ 0.5
- **high**: 0.5 < failure_probability ≤ 0.75
- **critical**: failure_probability > 0.75

**Key Insights:**
- Equipment with failure_probability > 0.5 triggers "high_failure_risk" intelligence
- Equipment with maintenance overdue by >50% of interval triggers "maintenance_overdue" intelligence
- Aging equipment (>7 years) with maintenance gaps triggers "age_concern" intelligence

## API Endpoints

### POST /api/phase20/equipment/analyze

Analyze equipment health for a project.

**Request Body:**
```json
{
  "project_id": "P001",
  "project_name": "Downtown Renovation",
  "equipment": [
    {
      "equipment_id": "EQ001",
      "name": "Excavator Alpha",
      "equipment_type": "EXCAVATOR",
      "acquisition_date": "2020-01-15",
      "current_status": "OPERATIONAL",
      "location": "Site A",
      "operator_id": "USER123"
    }
  ],
  "maintenance_records": [
    {
      "project_id": "P001",
      "equipment_id": "EQ001",
      "maintenance_date": "2025-01-10",
      "maintenance_type": "preventive",
      "duration_hours": 8.0,
      "cost": 1200.0,
      "completed": true
    }
  ],
  "failure_events": [
    {
      "project_id": "P001",
      "task_id": "T001",
      "equipment_id": "EQ001",
      "failure_date": "2024-12-01",
      "failure_type": "engine_failure",
      "repair_duration_hours": 24.0,
      "repair_cost": 3500.0,
      "downtime_impact_days": 2.0
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "equipment_id": "PROJECT_EQUIPMENT",
  "project_id": "P001",
  "project_name": "Downtown Renovation",
  "equipment_summaries": {
    "EQ001": {
      "equipment_id": "EQ001",
      "name": "Excavator Alpha",
      "failure_probability": 0.32,
      "risk_level": "medium",
      "total_maintenance_events": 1,
      "total_failure_events": 1,
      "days_since_last_maintenance": 25,
      "explanation": "Equipment has experienced 1 failure with limited maintenance history. Overdue property detected.",
      "recommended_action": "Schedule preventive maintenance immediately"
    }
  },
  "equipment_risk_insights": [
    {
      "equipment_id": "EQ001",
      "name": "Excavator Alpha",
      "insight_type": "high_failure_risk",
      "severity": "high",
      "description": "Equipment shows elevated failure probability (0.32).",
      "recommended_action": "Increase monitoring frequency and schedule preventive maintenance"
    }
  ],
  "equipment_risk_score": 0.32,
  "project_summary": "Fleet contains 1 equipment asset(s). 1 equipment flagged with high_failure_risk. Overall risk score: 0.32.",
  "critical_equipment_count": 0,
  "integration_ready": true
}
```

### GET /api/phase20/equipment/health

Returns recent intelligence (cached from last analyze call).

### GET /api/phase20/health

Health check endpoint (returns `{"status": "ok"}`).

## Integration with Core AI Engine

The analyzer includes a **feed_equipment_to_core_risk_engine()** function that:
1. Wraps EquipmentIntelligence output
2. Attempts to import and call `core_risk_engine.register_equipment_risk()`
3. Falls back gracefully to logging if unavailable (CI-safe)

Output structure for core engine integration:
```python
{
  "source": "phase_20_equipment_maintenance",
  "equipment_risk_score": 0.32,
  "risk_level": "medium",
  "critical_equipment_count": 0,
  "summaries": {...},
  "insights": [...]
}
```

## monday.com Mapping

For each equipment with elevated risk, a **monday_updates** dict is created containing columns ready for mapping:
```python
{
  "equipment_name": "Excavator Alpha",
  "equipment_health_status": "medium",
  "failure_probability": "0.32",
  "risk_level": "medium",
  "days_since_maintenance": "25",
  "recommended_action": "Schedule preventive maintenance immediately",
  "equipment_id": "EQ001"
}
```

These fields can be mapped to monday.com custom columns via the Phase 14–16 Integration framework. Optional `equipment_id` and `operator_id` fields enable linking to external equipment registries.

## Testing

**Unit Tests** (test_phase20.py):
- `test_equipment_health_summary_basic`: Verifies basic health calculation with preventive maintenance
- `test_equipment_health_with_failures`: Tests health scoring when equipment has past failures
- `test_create_project_intelligence`: End-to-end project-level intelligence generation

**Run tests:**
```bash
cd backend
$env:PYTHONPATH='app'; python -m pytest tests/test_phase20.py -v
```

**Expected Output:**
```
test_phase20.py::test_equipment_health_summary_basic PASSED
test_phase20.py::test_equipment_health_with_failures PASSED
test_phase20.py::test_create_project_intelligence PASSED
===================== 3 passed in 0.10s =====================
```

## Files

- `backend/app/phase20_equipment_types.py` — Data models
- `backend/app/phase20_equipment_analyzer.py` — EquipmentMaintenanceAnalyzer with failure risk scoring
- `backend/app/phase20_equipment_integration.py` — Core engine integration + monday mapping
- `backend/app/phase20_equipment_api.py` — Flask blueprint endpoints
- `backend/tests/test_phase20.py` — Unit tests (3 tests, all passing)
- `PHASE_20_README.md` — This documentation

## Next Steps

1. **Integrate with Feature 1 Core Risk Engine** — Ensure hook is called in Phase 1 response pipeline
2. **Add CI/CD Tests** — Dry-run integration test (like Phase 18/19) validating monday mapping
3. **Deploy to Staging** — Test with real equipment data and maintenance schedules
4. **Configure monday.com Columns** — Map Phase 20 outputs to equipment health tracking board
5. **Monitor in Production** — Track failure prediction accuracy and refine weights

## Notes

- **Deterministic Scoring:** All calculations are reproducible; no randomness introduced
- **Confidence Metric:** Risk level and recommended actions are based on data volume (e.g., equipment with 1 failure is scored cautiously)
- **Data Quality:** Assumes maintenance_date and failure_date are ISO-formatted strings or datetime objects
- **Backward Compatibility:** If core_risk_engine is unavailable, analyzer logs a warning and continues (safe for CI environments)
