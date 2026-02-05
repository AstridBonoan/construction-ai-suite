# Phase 18 — Workforce Reliability & Attendance Intelligence

Status: Feature branch `feature/workforce-reliability-attendance` — committed

Overview
- Purpose: Track attendance, tardiness, and no-shows; detect unreliable patterns; produce explainable workforce risk outputs consumable by Feature 1 (core risk engine) and monday.com.
- Scope: Data models, scoring algorithm, API endpoints, integration hooks, unit tests and mapping guidance for monday.com.

Data models (see backend/app/phase18_workforce_types.py)
- `Worker`: `worker_id`, `name`, `role`, `team_id`, `monday_user_id`.
- `AttendanceRecord`: `shift_date`, `shift_id`, `status`, `scheduled_start`, `actual_start`, `minutes_late`, `project_id`, `task_id`, `monday_task_id`.
- `WorkerAttendanceSummary`, `TeamAttendanceSummary`, `WorkforceRiskInsight`, `WorkforceProjectSummary`, `WorkforceIntelligence` — structured outputs for reporting and integration.

Scoring & Pattern Detection (see backend/app/phase18_workforce_analyzer.py)
- Worker reliability score: 1.0 - (absence_rate * 0.4) - (tardiness_rate * 0.2) (clamped to 0-1).
- Confidence based on data volume: `min(1.0, total_shifts / 20)`.
- Recent pattern detection compares last N records to overall rates to classify `improving`, `stable`, or `declining`.
- Team and project aggregation: average reliability, estimated schedule slip (sum of per-worker risk scaled to days), estimated cost impact.

Integration with Core AI (Feature 1)
- Hook: `feed_workforce_to_core_risk_engine(intelligence)` in `backend/app/phase18_workforce_integration.py`.
- Payload is deterministic JSON with keys: `workforce_risk_score`, `avg_team_reliability`, `total_workers`, `high_risk_workers`, `estimated_schedule_slip_days`, `estimated_cost_impact`, `key_insights`, `recommendations`, and sample per-worker indicators.
- The hook attempts to call `core_risk_engine.update_project_risk(payload)` if available; otherwise it logs the payload (CI-safe).

API Endpoints (Flask blueprint in backend/app/phase18_workforce_api.py)
- POST `/api/workforce/analyze` — Accepts project, workers, teams, and attendance_records JSON; returns `WorkforceIntelligence` summary and per-worker/team explainable fields.
- GET `/api/workforce/worker/<worker_id>` — Placeholder (returns 404) until persistent storage added.
- GET `/api/workforce/project/<project_id>` — Placeholder (returns 404) until persistent storage added.
- GET `/api/workforce/health` — Health check.

monday.com integration
- `create_workforce_risk_update()` in `phase18_workforce_integration.py` produces `monday_updates` mapping with keys: `workforce_reliability` (0-1 health), `workforce_risk_flag` (yes/no), `schedule_impact_estimate`, `cost_impact_estimate`.
- Objects include `monday_user_id` and `monday_task_id` fields in models for future mapping.
- Use existing monday integration tooling in `scripts/phase9/monday_mapping.py` and `scripts/monday_integration.py` for account-level dry-runs before writing live updates.

Testing
- Unit tests: `backend/tests/test_phase18.py` covers models, analyzer, and project intelligence generation.
- Run locally (from repo root):
```powershell
$env:PYTHONPATH='backend/app'; python -m pytest backend/tests/test_phase18.py -q
```
- Tests passed locally (11 passed, 1 DeprecationWarning) when run with `PYTHONPATH=backend/app`.

Production notes & next steps
- Persisted lookups: implement DB/cache-backed GET endpoints for `/worker/<id>` and `/project/<id>` when real data flows in.
- Add an end-to-end dry-run integration test that maps `create_workforce_risk_update()` output into `scripts/phase9/monday_mapping.py` to validate column translations in CI (DRY_RUN=1).
- Consider adding telemetry events for each `feed_workforce_to_core_risk_engine` call and rate-limiting on integration retries.
- Add a short Phase 18 architecture doc to the docs folder if you want a higher-level diagram.

Files of interest
- backend/app/phase18_workforce_types.py
- backend/app/phase18_workforce_analyzer.py
- backend/app/phase18_workforce_integration.py
- backend/app/phase18_workforce_api.py
- backend/tests/test_phase18.py

Authorship & commit
- Committed to branch `feature/workforce-reliability-attendance`.

If you'd like, I can:
- add the suggested end-to-end dry-run test now, or
- implement DB-backed GET endpoints for persistent lookups.
