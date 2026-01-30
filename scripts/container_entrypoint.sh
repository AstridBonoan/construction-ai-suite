#!/usr/bin/env bash
set -euo pipefail

WORKDIR=/workspace
cd "$WORKDIR"

echo "Initializing git-lfs inside container..."
git lfs install || true

PY_REQ="backend/requirements.txt"
# Create and activate a virtual environment to avoid system-managed Python restrictions (PEP 668)
VENV_DIR=/opt/venv
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
echo "Using virtualenv at $VENV_DIR"

if [ -f "$PY_REQ" ]; then
  echo "Installing Python dependencies from $PY_REQ into venv"
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install -r "$PY_REQ"
else
  echo "No requirements.txt found at $PY_REQ; installing minimal dependencies into venv"
  python3 -m pip install --upgrade pip setuptools wheel
  python3 -m pip install pandas numpy scikit-learn matplotlib seaborn joblib
fi

# Ensure ML/runtime packages required by training script are present
python3 -m pip install --upgrade joblib pandas numpy scikit-learn matplotlib seaborn || true

if [ "${RUN_TRAINING:-true}" = "true" ]; then
  echo "Running baseline training and analysis script..."
  python3 backend/train_baseline_project_delay.py --splits-dir data_splits \
    --model-out models/baseline_project_delay_model.pkl \
    --metrics-out analysis_outputs/metrics.json \
    --plots-out analysis_outputs
else
  echo "RUN_TRAINING is set to false; skipping automatic training step."
fi

echo "Staging model and analysis outputs for commit..."
git config --global user.email "ci@example.com" || true
git config --global user.name "CI Bot" || true
git add models analysis_outputs || true

# Create commit if there are staged changes
if ! git diff --staged --quiet; then
  git commit -m "Train baseline model and add analysis outputs" || true
  echo "Pushing to branch feature/project-delay-prediction..."
  git push origin feature/project-delay-prediction || echo "git push failed — check credentials from host"
else
  echo "No changes to commit"
fi

echo "Pipeline complete. Files saved under models/ and analysis_outputs/"

# If a command was provided to the container, run it now (allows running preparation steps)
if [ "$#" -gt 0 ]; then
  echo "Executing container CMD: $@"
  exec "$@"
fi
