"""
Full bootstrap and environment setup for developers.

Features:
- Runs `scripts/bootstrap.py` to install git hooks.
- Creates a Python virtual environment at `.venv` if missing.
- Installs Python dependencies from `backend/requirements.txt` (if present).
- Optionally installs and enables `pre-commit`.
- Idempotent: skips steps already completed.

Usage:
    python scripts/bootstrap_all.py

This script is safe to run multiple times.
"""

import os
import sys
import subprocess
from pathlib import Path
import venv

ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / ".venv"
PY = sys.executable


def run(cmd, **kwargs):
    print(">", " ".join(cmd) if isinstance(cmd, (list, tuple)) else cmd)
    return subprocess.run(cmd, **kwargs)


def ensure_venv():
    if VENV_DIR.exists() and (VENV_DIR / "pyvenv.cfg").exists():
        print(f"Virtualenv already exists at {VENV_DIR}")
        return False
    print(f"Creating virtualenv at {VENV_DIR}")
    venv.create(VENV_DIR, with_pip=True)
    return True


def get_venv_python():
    if os.name == "nt":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def install_requirements(python):
    req = ROOT / "backend" / "requirements.txt"
    if not req.exists():
        print("No backend/requirements.txt found; skipping dependency installation")
        return False
    print(f"Installing dependencies from {req}...")
    returncode = run([python, "-m", "pip", "install", "-r", str(req)]).returncode
    if returncode != 0:
        print("pip install returned non-zero exit code")
    return returncode == 0


def maybe_install_precommit(python):
    try:
        import importlib

        importlib.import_module("pre_commit")
        print("pre-commit already installed in this environment")
        return True
    except Exception:
        pass
    if input("Install pre-commit now into the venv? [Y/n]: ").strip().lower() in (
        "",
        "y",
        "yes",
    ):
        rc = run([python, "-m", "pip", "install", "pre-commit"]).returncode
        if rc == 0:
            run([str(python), "-m", "pre_commit", "install"])
            return True
        print("Failed to install pre-commit")
        return False


def main():
    # Step 1: run platform bootstrap (installs hooks)
    print("Running repository bootstrap (hooks installer)")
    run([sys.executable, str(ROOT / "scripts" / "bootstrap.py")])

    # Step 2: ensure venv
    created = ensure_venv()
    python = get_venv_python() if VENV_DIR.exists() else sys.executable

    # Step 3: install requirements if venv created or user chooses
    if created:
        install_requirements(python)
    else:
        if input(
            "Reinstall dependencies into existing venv? [y/N]: "
        ).strip().lower() in ("y", "yes"):
            install_requirements(python)

    # Step 4: optional pre-commit installation
    maybe_install_precommit(python)

    print("Bootstrap-all complete.")


if __name__ == "__main__":
    main()
