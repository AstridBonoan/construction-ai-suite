"""Upsert a connected external context for the demo tenant.

Run with: .venv\Scripts\python.exe scripts\dev\upsert_demo_context.py
"""
import json
from urllib.request import Request, urlopen

payload = {
    "tenant_id": "demo_tenant",
    "status": "connected",
    "available_boards": ["board_123"],
    "selected_board_ids": ["board_123"],
    "provider": "monday"
}

req = Request('http://127.0.0.1:5000/api/external/context', data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
try:
    with urlopen(req, timeout=5) as r:
        print('Upsert response:', r.status)
        print(r.read().decode('utf-8')[:400])
except Exception as e:
    print('Failed to upsert external context:', e)
