import os
import pytest
from backend.app.feature13_monday_oauth import bp as oauth_bp
from flask import Flask

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(oauth_bp)
    return app

def test_login_redirect(client, app):
    # Ensure the login endpoint redirects to monday auth
    resp = app.test_client().get('/api/saas/auth/monday/login')
    assert resp.status_code in (302, 301)
    assert 'monday.com' in resp.location
