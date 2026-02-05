"""Lightweight test stub for the core risk engine used in integration tests.

Provides `update_project_risk` which records the last update payload to
`last_update` for test assertions.
"""

last_update = None


def update_project_risk(payload):
    global last_update
    last_update = payload


def reset():
    global last_update
    last_update = None
