def test_run_attack_dry_run(monkeypatch):
    from redteam.attacker.engine import run_attack

    # dry run default
    res = run_attack("http://localhost:8000/login", {"type": "test", "payload": "x"})
    assert isinstance(res, dict)
