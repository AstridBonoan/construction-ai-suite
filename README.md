## Development

This repository contains scripts and services for the Construction AI Suite.

- `scripts/ci_checks.py` - CI/pre-commit script to detect plaintext `api_key`/`token` in `configs/`.

### Installing Git Hooks

To ensure all developers run the same pre-commit checks locally, run the installer which copies hook templates into your local `.git/hooks/` directory:

```bash
python scripts/install_hooks.py
```

The installer is idempotent: it will skip identical hooks and back up existing differing hooks to `<hook>.bak.<timestamp>`.

After installing hooks, commits will be blocked if `scripts/ci_checks.py` detects plaintext secrets in `configs/*.json` (templates and placeholder values are ignored).

If you prefer to manage hooks via the `pre-commit` tool or other mechanisms, you can instead integrate `scripts/ci_checks.py` as part of your pipeline.

### Bootstrapping repository for new developers

Run the bootstrap script for your platform to install the repository's git hook templates and optionally enable the `pre-commit` framework:

Unix/macOS:
```bash
python scripts/bootstrap.sh
```

Windows (PowerShell):
```powershell
python scripts\bootstrap.ps1
```

The bootstrap step is idempotent: running it multiple times will not break existing hooks. If an existing hook differs from the template, the installer backs it up to `.git/hooks/<hook>.bak.<timestamp>`.

To enable managed hooks across developers using `pre-commit` (recommended):

```bash
pip install pre-commit
pre-commit install
```

You can run all pre-commit checks locally with:

```bash
pre-commit run --all-files
```

CI Integration

The repository includes a sample GitHub Actions workflow `.github/workflows/monday-ci.yml` that runs `scripts/ci_checks.py` and an optional dry-run integration step. The workflow will not write real tokens because the integration step is run with `DRY_RUN=1`.

Verification steps

1. Install hooks: run the bootstrap command for your platform.
2. Verify the hooks were installed (look in `.git/hooks/`).
3. Run the CI check locally:

```bash
python scripts/ci_checks.py
```

4. Dry-run OAuth onboarding (no real tokens persisted):

```bash
python scripts/monday_setup.py --output configs/acme_monday.json --oauth
```

5. Dry-run multi-account integration:

PowerShell:
```powershell
$env:DRY_RUN='1'; python scripts/monday_integration.py --configs-dir configs/
```

Unix/macOS:
```bash
DRY_RUN=1 python scripts/monday_integration.py --configs-dir configs/
```

Security notes

- Dry-run mode (`DRY_RUN=1`) simulates onboarding and integration and never persists real tokens.
- `scripts/ci_checks.py` ignores template/example files and common placeholder values to avoid false positives.
- Logs are redacted using `scripts/logger.py`; secrets such as `api_key`, `access_token`, `refresh_token`, and `MONDAY_SECRET_KEY` are redacted from console output.

Developer note — CI-safe guard for `monday_integration.py`:

- To keep `pre-commit` and CI runs offline-safe, `scripts/monday_integration.py` avoids importing network libraries (for example, `requests`) when the environment variable `MOCK_CENTRAL_HANDLER` is set to `1`.
- This guard allows maintainers to run `pre-commit run --all-files` and other local checks without installing external runtime deps or performing network calls. If you need to run the integration locally against real services, unset `MOCK_CENTRAL_HANDLER` and install the required dependencies (e.g., `requests`).

Ensuring JSON console logs

In some environments (test runners, frameworks, or tools that configure logging late), the root logger may be configured after modules are imported and may attach non-JSON console handlers. `scripts/logger.py` intentionally avoids mutating the root logger to remain non-invasive.

To guarantee JSON console logs across all processes, do one of the following near your process entrypoint:

1. Import `scripts.logger` early (before other logging configuration):

```python
from scripts.logger import get_logger
get_logger('my_service')
```

2. Or explicitly set JSON formatters for the root handlers at process start:

```python
import logging
from scripts.logger import RedactingJSONFormatter

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler()])
for h in logging.getLogger().handlers:
	h.setFormatter(RedactingJSONFormatter(service='my_service', env='ci'))
```

CI tip: Import `scripts.logger` as early as possible in CI job scripts to ensure all console output is structured and redacted.

### Python bootstrap helper

You can run a cross-platform Python bootstrap helper which picks the right platform script and optionally installs `pre-commit`:

```bash
python scripts/bootstrap.py
```

The Python helper runs `scripts/bootstrap.sh` (Unix/macOS) or `scripts/bootstrap.ps1` (Windows) if present, otherwise falls back to `scripts/install_hooks.py`.

Verification checklist

1. Run `python scripts/bootstrap.py` to install hooks and optionally enable `pre-commit`.
2. Confirm hooks exist in `.git/hooks/` (both `pre-commit` and `pre-commit.ps1` for Windows).
3. Run `python scripts/ci_checks.py` — it should pass (templates and placeholders are ignored).
4. Run dry-run onboarding:

```bash
python scripts/monday_setup.py --output configs/acme_monday.json --oauth
```

5. Run dry-run multi-account integration:

PowerShell:
```powershell
### Required CI check (Strict dry-run integration)

This repository includes a stricter workflow `.github/workflows/monday-ci-strict.yml` intended to be required for protected branches (e.g., `main`, `develop`). It runs:

- `scripts/ci_checks.py` — scans `configs/*.json` for accidental plaintext secrets.
- `scripts/monday_integration.py --configs-dir configs/` in `DRY_RUN=1` using a synthetic config — this validates multi-account integration logic without making any live writes.

To enforce this as a required check in GitHub:

1. Go to your repository Settings → Branches → Branch protection rules.
2. Create or edit a rule for `main` (or the protected branch) and enable "Require status checks to pass before merging".
3. Select the workflow job name `strict-checks` from the `Monday CI (Strict)` workflow as a required status check.

Notes:
- The strict workflow uses a synthetic config (`configs/strict_synthetic.json`) created at runtime; the dry-run integration runs with `DRY_RUN=1`, so no real Monday tokens or writes occur.
- The workflow will fail (block merges) if the dry-run integration fails with an error. This ensures regressions in integration logic or config handling are caught before merge.

### Centralized logging (optional)

You can configure centralized logging to send redacted logs to Datadog or AWS CloudWatch. This is optional — by default logs are written to stdout and redacted.

Environment variables:
- `ENABLE_CENTRAL_LOGS=1` — enable centralized logging handlers.
- `CENTRAL_LOG_SINK` — `datadog` or `cloudwatch`.

Datadog configuration (HTTP intake):
- `DATADOG_API_KEY` — required when `CENTRAL_LOG_SINK=datadog`.
- (optional) `DATADOG_SITE` — defaults to `datadoghq.com`.

CloudWatch configuration:
- Ensure AWS credentials are available in the environment (usual boto3 methods).
- `CLOUDWATCH_LOG_GROUP` — log group name (default `construction-ai`).
- `CLOUDWATCH_LOG_STREAM` — log stream name (default `monday-integration`).

How to test centralized logging locally (dry-run safe):

1. Enable centralized logging and choose sink. Example (Datadog):

```bash
export ENABLE_CENTRAL_LOGS=1
export CENTRAL_LOG_SINK=datadog
export DATADOG_API_KEY=your_key_here
python scripts/logging_test.py
```

2. Example (CloudWatch): ensure AWS creds available and run:

```bash
export ENABLE_CENTRAL_LOGS=1
export CENTRAL_LOG_SINK=cloudwatch
export CLOUDWATCH_LOG_GROUP=construction-ai
export CLOUDWATCH_LOG_STREAM=local-test
python scripts/logging_test.py
```

The `scripts/logging_test.py` will emit messages containing simulated token-like strings; the centralized handlers and console formatter will redact those values before sending or printing.

### Enhanced logging reliability and CI test

The logging handlers now include retry/backoff and safe async behavior for Datadog and retry logic for CloudWatch. For local CI testing there is a dedicated workflow:

- `.github/workflows/logging-ci.yml` — runs `scripts/logging_test.py` with `MOCK_CENTRAL_HANDLER=1` and `FAIL_ON_LOG_ERRORS=1`. This simulates centralized sinks and fails the job if any handler reports a send error.

To run the logging CI test locally (simulate handler success):

```bash
export ENABLE_CENTRAL_LOGS=1
export CENTRAL_LOG_SINK=datadog
export MOCK_CENTRAL_HANDLER=1
export FAIL_ON_LOG_ERRORS=1
python scripts/logging_test.py
```

Notes:
- `MOCK_CENTRAL_HANDLER=1` activates dummy clients that simulate successful sends (useful for CI or local verification without credentials).
- To test end-to-end against a real sink, set the appropriate credentials (e.g., `DATADOG_API_KEY` or AWS credentials), unset `MOCK_CENTRAL_HANDLER`, and run `scripts/logging_test.py`. Be cautious: do not send real secrets in logs.



$env:DRY_RUN='1'; python scripts/monday_integration.py --configs-dir configs/
```

Unix/macOS:
```bash
DRY_RUN=1 python scripts/monday_integration.py --configs-dir configs/
```

6. Confirm per-account reports in `reports/` (e.g. `reports/monday_integration_report_synthetic_account.json`).

### Full bootstrap and environment setup (optional)

Run the all-in-one bootstrap that also creates a virtual environment and installs backend Python dependencies:

```bash
python scripts/bootstrap_all.py
```

Behavior:
- Creates `.venv/` if missing (idempotent).
- Installs dependencies from `backend/requirements.txt` into the venv (if present).
- Runs the repository bootstrap to install hooks.
- Prompts to install `pre-commit` into the venv.

If `.venv/` already exists, the script will prompt whether to reinstall dependencies.



