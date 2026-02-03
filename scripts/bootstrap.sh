#!/usr/bin/env bash
# Bootstrap script for Unix/macOS: installs git hooks and optionally pre-commit
set -euo pipefail

PY=python
if [ -f .venv/Scripts/python.exe ]; then
  PY=.venv/Scripts/python.exe
fi

echo "Running installer: $PY scripts/install_hooks.py"
$PY scripts/install_hooks.py

if command -v pre-commit >/dev/null 2>&1; then
  echo "pre-commit found; installing pre-commit hooks"
  pre-commit install || true
else
  echo "pre-commit not found. To enable managed hooks, run: pip install pre-commit && pre-commit install"
fi

echo "Bootstrap complete."
