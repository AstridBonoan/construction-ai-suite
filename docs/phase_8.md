# Phase 8 — monday.com integration

This document describes the Phase 8 onboarding and usage for the monday.com
integration implemented in `scripts/monday_integration.py`.

## Key features

- Multi-tenant support via per-account JSON configs (`--configs-dir`).
- DRY_RUN-first behavior (default `DRY_RUN=1`) that prevents any live network
  calls and writes simulated reports to `reports/`.
- Encrypted configs supported via `_encrypted` wrapper and `MONDAY_SECRET_KEY`,
  or via a pluggable `secret_manager` backend.
- Token refresh flow supported when OAuth tokens (`refresh_token`) are used,
  leveraging `MONDAY_OAUTH_CLIENT_ID` and `MONDAY_OAUTH_CLIENT_SECRET`.
- Structured JSON logging with redaction via `scripts/logger.py` (`get_logger`).

## Creating per-account JSON configs

Create a simple JSON file under `configs/` for each account. Minimal fields:

```json
{
  "api_key": "OPTIONAL_API_KEY",
  "board_id": 12345678,
  "columns": {
    "project_id": "proj_col_internal_id",
    "predicted_delay": "col_pred",
    "revenue": "col_rev",
    "risk": "col_risk",
    "status": "col_status"
  }
}
```

Notes:
- If you provide `api_key` in the file, live runs will use it.
- If you prefer encryption, wrap the config into an `_encrypted` wrapper using
  your `MONDAY_SECRET_KEY` or the `secret_manager` backend.

## Encrypting configs

Two options:

1. Use the `secret_manager` backend provided by your environment (preferred).
   Implement `secret_manager.get_manager()` to return an object with `load` and
   `save` methods.

2. Use local Fernet encryption wrapper:

```python
from cryptography.fernet import Fernet
f = Fernet(MONDAY_SECRET_KEY.encode())
payload = f.encrypt(json.dumps(cfg).encode()).decode()
wrapper = {"_encrypted": True, "payload": payload}
# write wrapper to configs/<account>.json
```

`scripts/monday_integration.py` will detect `_encrypted` and attempt to
decrypt using `MONDAY_SECRET_KEY` if `secret_manager` is not configured.

## Dry-run (safe) usage

By default the integration runs in dry-run mode and will not make network calls:

PowerShell:
```powershell
$env:DRY_RUN=1
$env:MOCK_CENTRAL_HANDLER=1
$env:ENABLE_CENTRAL_LOGS=1
python scripts\monday_integration.py --configs-dir configs/
```

Unix/macOS:
```bash
DRY_RUN=1 MOCK_CENTRAL_HANDLER=1 ENABLE_CENTRAL_LOGS=1 python scripts/monday_integration.py --configs-dir configs/
```

Dry-run will create `reports/monday_integration_report_<cfg>.json` files containing
simulated operations for each account.

## Live usage

After onboarding and verifying configs, run with `DRY_RUN=0` and provide either
`MONDAY_API_KEY` env or per-account configs with `api_key`:

```powershell
$env:DRY_RUN=0
python scripts\monday_integration.py --configs-dir configs/
```

The script enforces that placeholder column IDs are replaced before making live
calls. It will raise a `RuntimeError` if required fields are missing.

## Token refresh

If a per-account config contains a `token` object with `refresh_token`, the
integration will attempt to refresh using `MONDAY_OAUTH_CLIENT_ID` and
`MONDAY_OAUTH_CLIENT_SECRET`. On successful refresh the new token is persisted
back to the config (using `secret_manager` if enabled, or local save/encrypt).

## CI smoke job

A GitHub Actions smoke job (`monday-integration-smoke`) runs on PRs to `main`
with `DRY_RUN=1` and `MOCK_CENTRAL_HANDLER=1` to validate integration logic is
working without network calls. The job runs:

```bash
python scripts/monday_integration.py --configs-dir configs/
```

and validates that `reports/monday_integration_report_*.json` files are produced.

## Troubleshooting

- If you see an error about missing `MONDAY_SECRET_KEY` when loading an
  encrypted config, set `MONDAY_SECRET_KEY` to your Fernet key or supply a
  `secret_manager` implementation.
- To ensure JSON redacted logs in CI, import `scripts.logger` early in your
  process entry point.
