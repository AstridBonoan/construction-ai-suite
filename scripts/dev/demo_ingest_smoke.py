"""Demo smoke script: run Monday sync which should trigger demo ingestion bridge.

Run with: .venv\Scripts\python.exe scripts\dev\demo_ingest_smoke.py
"""
import os
from pathlib import Path
import sys

# Ensure the backend package is importable as a top-level package `app`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'backend'))

os.environ['DEMO_MODE'] = 'true'

from app.oauth.monday_api_client import MondayAPIClient
from app.oauth.monday_sync_service import MondayDataSyncService
# Demo helper: ensure external context is present and connected so ingestion bridge runs
from app.external_context_store import upsert_context, get_context


def main():
    print('Starting demo sync -> ingest smoke test')
    # Upsert demo external context (local file-backed store) to connected
    try:
        existing = get_context('demo_tenant') or {}
        upsert_context('demo_tenant', {
            'tenant_id': 'demo_tenant',
            'status': 'connected',
            'available_boards': ['board_123'],
            'selected_board_ids': ['board_123'],
            'provider': 'monday'
        })
        print('[SMOKE] demo external context upserted (connected)')
    except Exception as e:
        print(f'[SMOKE][WARN] Failed to upsert demo external context: {e}')
    api = MondayAPIClient('demo_token')
    res = MondayDataSyncService.sync_board_items('demo_tenant', 'board_123', api)
    print('Sync finished; result type:', type(res))

    p = Path('data/ingestion_log_demo.json')
    if p.exists():
        print('Ingestion log exists; sample:')
        print(p.read_text()[:800])
    else:
        print('Ingestion log not found')


if __name__ == '__main__':
    main()
