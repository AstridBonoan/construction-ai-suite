import os
import json
import tempfile
import importlib


def test_encrypted_config_without_secret_key_raises(monkeypatch, tmp_path):
    """Simulate an _encrypted wrapper file and confirm load_config() errors
    helpfully when MONDAY_SECRET_KEY is not set.
    """
    # prepare a fake encrypted wrapper (payload can be arbitrary since we
    # are asserting the code raises before attempting decryption when secret
    # is unavailable)
    wrapper = {"_encrypted": True, "payload": "fake-payload"}
    cfg_file = tmp_path / "fake_encrypted.json"
    cfg_file.write_text(json.dumps(wrapper))

    # Ensure MONDAY_SECRET_KEY is not set in env
    monkeypatch.delenv("MONDAY_SECRET_KEY", raising=False)

    # Import the module under test and call load_config
    mod = importlib.import_module("scripts.monday_integration")

    # Use the module's public loader if available; otherwise call the
    # internal helper. We expect a RuntimeError explaining the missing key.
    try:
        loader = getattr(mod, "load_config")
    except AttributeError:
        pytest.skip("monday_integration.load_config not present")

    try:
        loader(str(cfg_file))
    except RuntimeError as e:
        assert "MONDAY_SECRET_KEY" in str(e) or "cryptography" in str(e)
    else:
        raise AssertionError("expected RuntimeError for missing MONDAY_SECRET_KEY")
