#!/usr/bin/env python3
"""Train a baseline regression model for project delay and produce analysis outputs.

This script:
- Verifies presence of data_splits/X_train.csv, y_train.csv, X_test.csv, y_test.csv
- Trains a RandomForestRegressor on X_train/y_train
- Saves model to specified path
- Computes MAE, RMSE, R2 and writes metrics JSON
- Produces plots: actual vs predicted, residuals distribution, error histogram
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def verify_files(splits_dir: Path):
    required = ["X_train.csv", "y_train.csv", "X_test.csv", "y_test.csv"]
    missing = [f for f in required if not (splits_dir / f).exists()]
    if missing:
        print(f"ERROR: Missing required split files in {splits_dir}: {missing}")
        sys.exit(2)


def load_splits(splits_dir: Path):
    X_train = pd.read_csv(splits_dir / "X_train.csv", low_memory=False)
    y_train = pd.read_csv(splits_dir / "y_train.csv", low_memory=False)
    X_test = pd.read_csv(splits_dir / "X_test.csv", low_memory=False)
    y_test = pd.read_csv(splits_dir / "y_test.csv", low_memory=False)

    # If y are single-column DataFrames, convert to Series
    if isinstance(y_train, pd.DataFrame) and y_train.shape[1] == 1:
        y_train = y_train.iloc[:, 0]
    if isinstance(y_test, pd.DataFrame) and y_test.shape[1] == 1:
        y_test = y_test.iloc[:, 0]

    return X_train, y_train, X_test, y_test


def train_and_save(X_train, y_train, model_out: Path, random_state: int = 42):
    # Basic preprocessing: drop all-NA or constant columns from X_train
    drop_const = [c for c in X_train.columns if X_train[c].nunique(dropna=True) <= 1 or X_train[c].isna().all()]
    if drop_const:
        X_train = X_train.drop(columns=drop_const, errors="ignore")

    # Encode categorical (object) columns via factorize so all inputs are numeric
    cat_maps = {}
    for col in X_train.columns:
        if pd.api.types.is_numeric_dtype(X_train[col]):
            # fill numeric NA with median
            median = X_train[col].median()
            X_train[col] = X_train[col].fillna(median)
        else:
            # factorize training values; map unseen to -1
            codes, uniques = pd.factorize(X_train[col].astype(str), sort=True)
            X_train[col] = codes.astype(float)
            cat_maps[col] = {val: i for i, val in enumerate(uniques)}

    model = RandomForestRegressor(n_estimators=200, random_state=random_state, n_jobs=-1)
    model.fit(X_train, y_train)

    model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_out)
    return model, X_train.columns.tolist(), cat_maps


def prepare_X(X: pd.DataFrame, reference_cols, cat_maps: dict | None = None):
    # Keep only reference_cols if present; create missing numeric columns as zeros
    Xp = X.copy()
    # Ensure same columns order and create missing cols
    for col in reference_cols:
        if col not in Xp.columns:
            Xp[col] = 0

    # Apply same encoding as training: numeric -> fill median; categorical -> map using cat_maps
    for col in reference_cols:
        if pd.api.types.is_numeric_dtype(Xp[col]):
            Xp[col] = pd.to_numeric(Xp[col], errors="coerce").fillna(Xp[col].median())
        else:
            # map categorical using training mapping if available
            if cat_maps and col in cat_maps:
                Xp[col] = Xp[col].map(cat_maps[col]).fillna(-1).astype(float)
            else:
                # fallback: factorize in-place
                codes, _ = pd.factorize(Xp[col].astype(str), sort=True)
                Xp[col] = codes.astype(float)
    return Xp[reference_cols]


def evaluate_and_plot(model, X_test: pd.DataFrame, y_test: pd.Series, plots_out: Path):
    preds = model.predict(X_test)
    errors = preds - y_test.values
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))

    plots_out.mkdir(parents=True, exist_ok=True)

    # Actual vs Predicted
    plt.figure(figsize=(6, 6))
    sns.scatterplot(x=y_test, y=preds, alpha=0.6)
    lims = [min(y_test.min(), preds.min()), max(y_test.max(), preds.max())]
    plt.plot(lims, lims, '--', color='gray')
    plt.xlabel('Actual')
    plt.ylabel('Predicted')
    plt.title('Actual vs Predicted')
    plt.tight_layout()
    (plots_out / 'actual_vs_predicted.png').unlink(missing_ok=True)
    plt.savefig(plots_out / 'actual_vs_predicted.png')
    plt.close()

    # Residuals distribution
    plt.figure(figsize=(6, 4))
    sns.histplot(errors, kde=True, bins=50)
    plt.xlabel('Residual (Predicted - Actual)')
    plt.title('Residuals Distribution')
    plt.tight_layout()
    (plots_out / 'residuals_distribution.png').unlink(missing_ok=True)
    plt.savefig(plots_out / 'residuals_distribution.png')
    plt.close()

    # Error histogram (absolute errors)
    plt.figure(figsize=(6, 4))
    sns.histplot(np.abs(errors), bins=50)
    plt.xlabel('Absolute Error')
    plt.title('Absolute Error Histogram')
    plt.tight_layout()
    (plots_out / 'error_histogram.png').unlink(missing_ok=True)
    plt.savefig(plots_out / 'error_histogram.png')
    plt.close()

    metrics = {"MAE": mae, "RMSE": rmse, "R2": r2}
    return metrics


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--splits-dir", default="data_splits")
    p.add_argument("--model-out", default="models/baseline_project_delay_model.pkl")
    p.add_argument("--metrics-out", default="analysis_outputs/metrics.json")
    p.add_argument("--plots-out", default="analysis_outputs")
    p.add_argument("--random-state", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    splits_dir = Path(args.splits_dir)
    verify_files(splits_dir)
    X_train, y_train, X_test, y_test = load_splits(splits_dir)

    # Print row/column counts
    print(f"X_train: {X_train.shape}, y_train: {getattr(y_train, 'shape', 'n/a')}")
    print(f"X_test: {X_test.shape}, y_test: {getattr(y_test, 'shape', 'n/a')}")

    # Train
    model_out = Path(args.model_out)
    model, ref_cols, cat_maps = train_and_save(X_train, y_train, model_out, random_state=args.random_state)

    # Prepare test features to match training
    X_test_prepared = prepare_X(X_test, ref_cols, cat_maps=cat_maps)

    # Evaluate and plot
    plots_out = Path(args.plots_out)
    metrics = evaluate_and_plot(model, X_test_prepared, y_test, plots_out)

    # Save metrics
    metrics_out = Path(args.metrics_out)
    metrics_out.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_out, "w") as fh:
        json.dump(metrics, fh, indent=2)

    # Confirm saved files
    print("Saved model:", str(model_out))
    print("Saved plots:")
    for p in ["actual_vs_predicted.png", "residuals_distribution.png", "error_histogram.png"]:
        print(" -", str(plots_out / p))
    print("Saved metrics:", str(metrics_out))


if __name__ == "__main__":
    main()
