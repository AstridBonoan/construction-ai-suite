"""
Install Git hooks for this repository from the `scripts/hooks/` templates.

Usage:
    python scripts/install_hooks.py

Behavior:
 - Copies files from `scripts/hooks/` into the local repository `.git/hooks/`.
 - Idempotent: if a hook already exists and matches the template, it is left alone.
 - If a hook exists and differs, it's backed up to `<hook>.bak.TIMESTAMP` before replacing.
 - On Unix, the installed hook is made executable.

This helps teams install the same pre-commit checks (runs `scripts/ci_checks.py`).
"""

import sys
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "scripts" / "hooks"
GIT_HOOKS_DIR = ROOT / ".git" / "hooks"


def read_text(p: Path):
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return None


def ensure_hooks_dir():
    if not GIT_HOOKS_DIR.exists():
        print(f"Creating hooks directory: {GIT_HOOKS_DIR}")
        GIT_HOOKS_DIR.mkdir(parents=True, exist_ok=True)


def install_hook(template_path: Path, target_dir: Path):
    name = template_path.name
    target = target_dir / name
    tmpl = read_text(template_path)
    if tmpl is None:
        print(f"Skipping {template_path} (cannot read)")
        return

    existing = read_text(target) if target.exists() else None
    if existing == tmpl:
        print(f"{name}: already installed and identical — skipping")
        return

    if target.exists() and existing is not None and existing != tmpl:
        ts = int(time.time())
        bak = target.with_suffix(target.suffix + f".bak.{ts}")
        print(f"{name}: backing up existing hook to {bak}")
        shutil.copy2(target, bak)

    print(f"Installing {name} -> {target}")
    shutil.copy2(template_path, target)
    try:
        # make executable on POSIX
        target.chmod(0o755)
    except Exception:
        pass


def main():
    if not TEMPLATES_DIR.exists():
        print(f"Error: templates directory not found: {TEMPLATES_DIR}")
        sys.exit(2)

    ensure_hooks_dir()

    for p in sorted(TEMPLATES_DIR.iterdir()):
        if p.is_file():
            install_hook(p, GIT_HOOKS_DIR)

    print("Hooks installation complete.")


if __name__ == "__main__":
    main()
