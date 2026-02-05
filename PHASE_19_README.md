# Phase 19 — Subcontractor Performance Intelligence

Status: branch `feature/subcontractor-performance` (work in progress)

Overview
- Purpose: Score subcontractors on timeliness, reliability, and delay impact; flag high-risk dependencies; provide explainable outputs for project-level risk modeling and monday.com mapping.

Files added
- `backend/app/phase19_subcontractor_types.py` - data models
- `backend/app/phase19_subcontractor_analyzer.py` - scoring and intelligence
- `backend/app/phase19_subcontractor_integration.py` - core risk integration + monday updates
- `backend/app/phase19_subcontractor_api.py` - Flask blueprint endpoints
- `backend/tests/test_phase19.py` - unit tests

How to run tests (from repo root)
```powershell
$env:PYTHONPATH='backend/app'; python -m pytest backend/tests/test_phase19.py -q
```

Notes & next steps
- GET endpoints are placeholders; add persistence (SQLite/Postgres) for production.
- Consider adding CI dry-run tests mapping outputs to monday mapping helpers.
