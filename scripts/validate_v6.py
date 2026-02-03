#!/usr/bin/env python3
"""Validate v6 model: recompute metrics and run quick leakage checks."""

from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(".")
DATA_SPLITS = ROOT / "data_splits" / "v6"
OUT_MODEL = ROOT / "models" / "v6" / "baseline_project_delay_model_v6.pkl"
ANALYSIS = ROOT / "analysis_outputs" / "v6"


def run():
    X_test = pd.read_csv(DATA_SPLITS / "X_test.csv")
    y_test = pd.read_csv(DATA_SPLITS / "y_test.csv").squeeze()
    if not OUT_MODEL.exists():
        print("Model not found at", OUT_MODEL)
        return 1
    model = joblib.load(OUT_MODEL)
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    metrics = {
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(__import__("math").sqrt(mse)),
        "R2": float(r2_score(y_test, y_pred)),
    }
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    with open(ANALYSIS / "validation_metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)

    # quick perfect-predictor check on raw X_test
    perfect = []
    for c in X_test.columns:
        try:
            if (
                X_test[c].astype(str).fillna("") == y_test.astype(str).fillna("")
            ).all():
                perfect.append(c)
        except Exception:
            continue

    with open(ANALYSIS / "validation.txt", "w") as fh:
        fh.write(f"Metrics: {metrics}\n")
        fh.write(f"Perfect raw predictors: {perfect}\n")

    print("Validation complete. Metrics:", metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
