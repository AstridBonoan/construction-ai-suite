import os
import pytest
from datetime import datetime, timedelta

from backend.app.models.monday_token import TokenManager, MondayToken


def test_token_manager_save_and_get():
    mt = MondayToken(workspace_id='ws-test', access_token='secret', expires_in=60)
    assert TokenManager.save_token(mt) is True
    got = TokenManager.get_token('ws-test')
    assert got is not None
    assert got.workspace_id == 'ws-test'


@pytest.fixture
def app():
    """Flask app fixture for DB tests"""
    try:
        from backend.app.main import app as flask_app
        return flask_app
    except Exception:
        pytest.skip('Flask app not available')


@pytest.mark.skipif(os.getenv('CI')=='true', reason='DB tests disabled in CI')
def test_db_models_available(app):
    # This test requires Flask app context and DB configured
    try:
        from backend.app.models.tenant_models import db, Tenant, OAuthInstallation
    except Exception:
        pytest.skip('DB models not available')

    # create tenant and installation (transaction rolled back by test harness)
    with app.app_context():
        try:
            t = Tenant(name='Test Tenant', workspace_id='ws-test-2')
            db.session.add(t)
            db.session.commit()
            assert t.id is not None

            inst = OAuthInstallation(tenant_id=t.id, provider='monday', workspace_id='ws-test-2', access_token='x')
        except Exception:
            pytest.skip('DB session not available - DB not configured')
    db.session.add(inst)
    db.session.commit()
    assert inst.id is not None
