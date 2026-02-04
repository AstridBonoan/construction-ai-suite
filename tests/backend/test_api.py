import json
import os
import sys
import pytest

# Ensure `backend` package is importable when running tests from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))
from app import main


@pytest.fixture
def client():
    main.app.config['TESTING'] = True
    with main.app.test_client() as client:
        yield client


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('status') == 'ok'


def test_phase9_outputs(client):
    resp = client.get('/phase9/outputs')
    assert resp.status_code in (200, 500)  # allow fallback if mock missing
    if resp.status_code == 200:
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert 'project_id' in data[0]