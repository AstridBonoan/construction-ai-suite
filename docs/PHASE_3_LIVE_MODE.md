# Phase 3 — Live Mode Scaffolding (Internal Testing)

This document explains the non-destructive scaffolding added to prepare the
AI Construction Suite for Phase 3 (Live Mode Activation). The code added is
safe to commit and will not perform live writes unless you explicitly provide
credentials and run the live smoke tests.

Key additions (scaffold only):

- `.env.example` at repository root: example variables to copy to `.env`.
- `backend/app/config.py`: lightweight config loader (`init_config(app)`) that
  reads `.env` and `.env.example` and populates `os.environ` and Flask
  `app.config` defaults.
- `backend/app/db_placeholder.py`: safe DB connection/migration placeholders.
- `scripts/dev/run_live_smoke_stub.py`: smoke-test stub that skips unless
  required live env vars are present.
- `scripts/dev/demo_ingest_smoke.py` (existing) and `scripts/dev/upsert_demo_context.py` remain for demo validation.

How it works
------------

1. On startup `backend/app/main.py` calls `init_config(app)` which:
   - Loads `.env` if present (local overrides).
   - Applies any missing keys from `.env.example` as safe defaults.
   - Sets `os.environ` variables and `app.config` entries used by the app.

2. Demo mode remains the default (`DEMO_MODE=true`) unless you set it to
   `false` in `.env` or your environment. All demo artifacts and demo-only
   code paths remain intact and are used when `DEMO_MODE=true`.

3. The DB placeholders allow importing modules that reference the DB without
   failing in demo mode. Replace the placeholders with your real DB client
   (e.g., SQLAlchemy) and implement migrations (Alembic) during integration.

Running live smoke tests (internal)
----------------------------------

1. Create a `.env` from `.env.example` and populate values for:
   - `DATABASE_URL`, `FLASK_SECRET_KEY`, `MONDAY_CLIENT_ID`, `MONDAY_CLIENT_SECRET`.
2. Start the backend: `.venv\Scripts\Activate.ps1; python run_server.py`.
3. Run the live smoke stub:
   `python scripts\dev\run_live_smoke_stub.py` — it will exit if required
   variables are missing. Replace the stub with real smoke steps when
   credentials and test accounts are available.

Safety notes
------------

- No real credentials are bundled; never commit `.env` with real secrets.
- Demo artifacts (`data/external_contexts.json`, `data/ingestion_log_demo.json`)
  remain and are used when `DEMO_MODE=true`.
- Live-mode code paths should be gated by `DEMO_MODE` and the presence of
  valid credentials. The scaffolding does not perform live external writes.

Next steps for Phase 3 integration
---------------------------------

- Replace `backend/app/db_placeholder.py` with a real DB integration and
  implement secure migrations (Alembic).
- Implement production-grade ingestion: wire Monday sync results into the
  AI pipelines and persist canonical tasks to the DB.
- Add comprehensive smoke tests that exercise Monday OAuth + sync + AI
  processing against test tenant accounts.
