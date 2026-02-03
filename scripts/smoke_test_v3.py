#!/usr/bin/env python3
"""Smoke test for Baseline v3: load model, run predictions, compute metrics, and save plots."""

from __future__ import annotations
import json
import os
from pathlib import Path
import sys

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(".")
MODEL_PATH = ROOT / "models" / "v3" / "baseline_project_delay_model_v3.pkl"
X_TEST_PATH = ROOT / "data_splits" / "v3" / "X_test.csv"
Y_TEST_PATH = ROOT / "data_splits" / "v3" / "y_test.csv"
METRICS_PATH = ROOT / "analysis_outputs" / "v3" / "metrics.json"
OUT_DIR = ROOT / "analysis_outputs" / "v3" / "smoke_test"
OUT_DIR.mkdir(parents=True, exist_ok=True)

errors = []


def fail(msg):
    print("ERROR:", msg)
    errors.append(msg)


# 1. existence checks
for p in (MODEL_PATH, X_TEST_PATH, Y_TEST_PATH):
    if not p.exists():
        fail(f"Missing required file: {p}")

if errors:
    sys.exit(2)

# 2. load model
try:
    model = joblib.load(MODEL_PATH)
    print("Loaded model:", MODEL_PATH)
except Exception as e:
    fail(f"Failed to load model: {e}")
    sys.exit(3)

# 3. load test splits
try:
    X_test = pd.read_csv(X_TEST_PATH, low_memory=False)
    y_test = pd.read_csv(Y_TEST_PATH, low_memory=False)
    print("X_test shape:", X_test.shape)
    print("y_test shape:", y_test.shape)
    # if y_test has multiple columns, take the first
    if y_test.shape[1] == 1:
        y_true = y_test.iloc[:, 0].values
    else:
        # try column named 'will_delay'
        if "will_delay" in y_test.columns:
            y_true = y_test["will_delay"].values
        else:
            y_true = y_test.iloc[:, 0].values
except Exception as e:
    fail(f"Failed to read test splits: {e}")
    sys.exit(4)

# 4. predict
try:
    y_pred = model.predict(X_test)
    y_pred = np.asarray(y_pred).ravel()
    print("Predictions produced, length:", len(y_pred))
except Exception as e:
    fail(f"Prediction failed: {e}")
    sys.exit(5)

# 5. compute metrics
try:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    metrics = {"MAE": mae, "RMSE": rmse, "R2": r2}
    print("Computed metrics:", metrics)
    with open(OUT_DIR / "metrics_smoke.json", "w") as fh:
        json.dump(metrics, fh, indent=2)
except Exception as e:
    fail(f"Metric computation failed: {e}")
    sys.exit(6)

# 6. compare to saved metrics if present
if METRICS_PATH.exists():
    try:
        saved = json.loads(METRICS_PATH.read_text())
        print("Saved metrics:", saved)
        # quick comparison
        diffs = {}
        for k in ("MAE", "RMSE", "R2"):
            if k in saved:
                diff = abs(saved[k] - metrics[k])
                diffs[k] = diff
        with open(OUT_DIR / "metrics_comparison.json", "w") as fh:
            json.dump(
                {"computed": metrics, "saved": saved, "diffs": diffs}, fh, indent=2
            )
        print("Wrote metrics comparison to", OUT_DIR / "metrics_comparison.json")
    except Exception as e:
        print("Warning: could not read saved metrics:", e)

# 7. plots
try:
    # Actual vs Predicted
    plt.figure(figsize=(6, 6))
    sns.scatterplot(x=y_true, y=y_pred, alpha=0.3)
    mn = min(np.min(y_true), np.min(y_pred))
    mx = max(np.max(y_true), np.max(y_pred))
    plt.plot([mn, mx], [mn, mx], color="red", linewidth=1)
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title("Actual vs Predicted (v3 smoke)")
    plt.tight_layout()
    p1 = OUT_DIR / "actual_vs_predicted_smoke.png"
    plt.savefig(p1)
    plt.close()

    # Residuals distribution
    residuals = y_true - y_pred
    plt.figure(figsize=(6, 4))
    sns.histplot(residuals, kde=True, bins=50)
    plt.xlabel("Residual (Actual - Predicted)")
    plt.title("Residuals Distribution (v3 smoke)")
    plt.tight_layout()
    p2 = OUT_DIR / "residuals_distribution_smoke.png"
    plt.savefig(p2)
    plt.close()

    # Error histogram (absolute errors)
    abs_err = np.abs(residuals)
    plt.figure(figsize=(6, 4))
    sns.histplot(abs_err, bins=50)
    plt.xlabel("Absolute Error")
    plt.title("Absolute Error Histogram (v3 smoke)")
    plt.tight_layout()
    p3 = OUT_DIR / "error_histogram_smoke.png"
    plt.savefig(p3)
    plt.close()

    print("Saved plots to", OUT_DIR)
except Exception as e:
    fail(f"Plot generation failed: {e}")
    sys.exit(7)

# 8. final report
print("\nSmoke test summary:")
print(" - model:", MODEL_PATH)
print(" - X_test:", X_TEST_PATH, "shape=", X_test.shape)
print(" - y_test:", Y_TEST_PATH, "shape=", y_test.shape)
print(" - computed metrics:", metrics)
print(" - smoke outputs:", list(OUT_DIR.iterdir()))

if errors:
    print("\nErrors encountered:")
    for e in errors:
        print(" -", e)
    sys.exit(8)

print("\nSmoke test completed successfully")
sys.exit(0)
