from __future__ import annotations
import os
from pathlib import Path
from typing import Dict

# Simple config loader that prefers real environment variables, then .env file
# placed at the project root, then falls back to placeholders in `.env.example`.

ROOT = Path(__file__).resolve().parents[2]
DOTENV = ROOT / ".env"
EXAMPLE_ENV = ROOT / ".env.example"


def _load_dotenv(path: Path) -> Dict[str, str]:
    vals: Dict[str, str] = {}
    if not path.exists():
        return vals
    try:
        for line in path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            k, v = line.split('=', 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return vals


def init_config(app=None) -> Dict[str, str]:
    """Initialize configuration from environment, .env, or .env.example.

    - Loads `.env` if present and sets missing env vars (does not overwrite existing env vars).
    - Returns a dict of effective configuration values.
    - If `app` (Flask app) is provided, populates `app.config` with keys used elsewhere.
    """
    # Prioritize existing environment
    cfg: Dict[str, str] = dict(os.environ)

    # Load .env file into a dict but do not overwrite existing environment variables
    if DOTENV.exists():
        file_vals = _load_dotenv(DOTENV)
        for k, v in file_vals.items():
            cfg.setdefault(k, v)

    # Load example as fallback
    if EXAMPLE_ENV.exists():
        example_vals = _load_dotenv(EXAMPLE_ENV)
        for k, v in example_vals.items():
            cfg.setdefault(k, v)

    # Populate os.environ for downstream modules that read os.environ directly
    for k, v in cfg.items():
        os.environ.setdefault(k, v)

    # Normalize a few keys and defaults
    cfg.setdefault('DEMO_MODE', os.environ.get('DEMO_MODE', 'true'))
    cfg.setdefault('FLASK_ENV', os.environ.get('FLASK_ENV', 'development'))

    # Inject into Flask app config if provided
    if app is not None:
        app.config['DEMO_MODE'] = cfg.get('DEMO_MODE', 'true').lower() == 'true'
        app.config['DATABASE_URL'] = cfg.get('DATABASE_URL')
        app.config['FLASK_SECRET_KEY'] = cfg.get('FLASK_SECRET_KEY')
        app.config['MONDAY_CLIENT_ID'] = cfg.get('MONDAY_CLIENT_ID')
        app.config['MONDAY_CLIENT_SECRET'] = cfg.get('MONDAY_CLIENT_SECRET')
        app.config['MONDAY_REDIRECT_URI'] = cfg.get('MONDAY_REDIRECT_URI')

    return cfg


__all__ = ['init_config']
