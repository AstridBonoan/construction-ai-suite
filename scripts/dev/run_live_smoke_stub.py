"""Smoke-test stub for live mode.

This script demonstrates how to run live-mode checks. It will only proceed
if required environment variables (`DATABASE_URL`, `FLASK_SECRET_KEY`,
`MONDAY_CLIENT_ID`, `MONDAY_CLIENT_SECRET`) are provided. Otherwise it will
skip, leaving demo data intact.

Usage:
  .venv\Scripts\Activate.ps1
  python scripts\dev\run_live_smoke_stub.py
"""
import os
from pathlib import Path

required = ['DATABASE_URL', 'FLASK_SECRET_KEY', 'MONDAY_CLIENT_ID', 'MONDAY_CLIENT_SECRET']
missing = [k for k in required if not os.environ.get(k)]

if missing:
    print('[SMOKE][SKIP] Missing required env vars for live smoke:', missing)
    print('Provide these in a .env or your environment to run live smoke tests.')
    raise SystemExit(0)

print('[SMOKE] Required env vars found — running live smoke (stub).')
# Here you would: run DB migrations, start backend in live config, run ingestion against live monday
print('[SMOKE] Note: this is a scaffold. Replace with real smoke test steps when credentials available.')
