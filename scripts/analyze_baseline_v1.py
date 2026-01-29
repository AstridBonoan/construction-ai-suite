#!/usr/bin/env python3
"""Analyze Baseline v1 artifacts: load model, metrics, compute feature importance and diagnostics.

Produces:
- analysis_outputs/v1/feature_importances.csv
- analysis_outputs/v1/diagnostics.txt
- copies of existing plots into analysis_outputs/v1/
"""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(".")
SPLITS = ROOT / "data_splits"
MODEL = ROOT / "models" / "baseline_project_delay_model.pkl"
METRICS = ROOT / "analysis_outputs" / "metrics.json"
OUTDIR = ROOT / "analysis_outputs" / "v1"


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)

    # Load metrics
    if METRICS.exists():
        with open(METRICS, "r") as fh:
            metrics = json.load(fh)
    else:
        metrics = {}

    # Basic checks
    print("Loaded metrics:", metrics)

    # Load model and train features
    if not MODEL.exists():
        print("Model not found at", MODEL)
        return
    model = joblib.load(MODEL)

    X_train = pd.read_csv(SPLITS / "X_train.csv", low_memory=False)

    # Feature importance if available
    fi = None
    if hasattr(model, "feature_importances_"):
        try:
            fi = model.feature_importances_
        except Exception:
            fi = None

    if fi is not None:
        # Reconstruct the training columns selection used in train_and_save: drop constant or all-NA columns
        drop_const = [c for c in X_train.columns if X_train[c].nunique(dropna=True) <= 1 or X_train[c].isna().all()]
        ref_cols = [c for c in X_train.columns if c not in drop_const]
        # If lengths match, map directly; otherwise attempt best-effort alignment by using first N columns
        if len(fi) == len(ref_cols):
            fi_series = pd.Series(fi, index=ref_cols).sort_values(ascending=False)
        elif len(fi) == len(X_train.columns):
            fi_series = pd.Series(fi, index=X_train.columns).sort_values(ascending=False)
        else:
            # best-effort: align to first len(fi) columns of ref_cols
            align_cols = ref_cols[: len(fi)]
            fi_series = pd.Series(fi, index=align_cols).sort_values(ascending=False)

        fi_series.to_csv(OUTDIR / "feature_importances.csv", header=["importance"])  # save
        print("Saved feature importances to", OUTDIR / "feature_importances.csv")
    else:
        print("Model does not expose feature_importances_")

    # Copy existing plots if present
    for plot in ("actual_vs_predicted.png", "residuals_distribution.png", "error_histogram.png"):
        src = ROOT / "analysis_outputs" / plot
        if src.exists():
            dst = OUTDIR / plot
            dst.write_bytes(src.read_bytes())
            print("Copied", plot, "to", dst)

    # Simple diagnostics: check for perfect metrics or suspicious values
    diag_lines = []
    if metrics:
        mae = metrics.get("MAE")
        rmse = metrics.get("RMSE")
        r2 = metrics.get("R2")
        diag_lines.append(f"MAE: {mae}")
        diag_lines.append(f"RMSE: {rmse}")
        diag_lines.append(f"R2: {r2}")
        if r2 is not None and r2 >= 0.999:
            diag_lines.append("WARNING: R² is ~1.0 — check for data leakage or training-on-test.")
    # Feature value checks
    sample_counts = X_train.shape[0]
    diag_lines.append(f"Training rows: {sample_counts}")
    # Check for constant columns
    const_cols = [c for c in X_train.columns if X_train[c].nunique(dropna=True) <= 1]
    diag_lines.append(f"Constant columns: {len(const_cols)}")

    with open(OUTDIR / "diagnostics.txt", "w") as fh:
        fh.write("\n".join(diag_lines))

    print("Diagnostics written to", OUTDIR / "diagnostics.txt")


if __name__ == "__main__":
    main()
