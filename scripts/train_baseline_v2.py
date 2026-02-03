#!/usr/bin/env python3
"""Train Baseline v2: preprocessing + RandomizedSearchCV on RandomForest.

Saves:
- models/v2/baseline_project_delay_model_v2.pkl
- analysis_outputs/v2/metrics.json
- analysis_outputs/v2/plots (same set as v1)
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import RandomizedSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(".")
SPLITS = ROOT / "data_splits"
OUT_MODEL = ROOT / "models" / "v2" / "baseline_project_delay_model_v2.pkl"
OUT_METRICS = ROOT / "analysis_outputs" / "v2" / "metrics.json"
OUT_PLOTS = ROOT / "analysis_outputs" / "v2"


def load_splits(splits_dir: Path):
    X_train = pd.read_csv(splits_dir / "X_train.csv", low_memory=False)
    y_train = pd.read_csv(splits_dir / "y_train.csv", low_memory=False)
    X_test = pd.read_csv(splits_dir / "X_test.csv", low_memory=False)
    y_test = pd.read_csv(splits_dir / "y_test.csv", low_memory=False)
    if isinstance(y_train, pd.DataFrame) and y_train.shape[1] == 1:
        y_train = y_train.iloc[:, 0]
    if isinstance(y_test, pd.DataFrame) and y_test.shape[1] == 1:
        y_test = y_test.iloc[:, 0]
    return X_train, y_train, X_test, y_test


def detect_column_types(df: pd.DataFrame):
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if c not in num_cols]
    return num_cols, cat_cols


def train_v2(random_state: int = 42, n_iter: int = 12):
    X_train, y_train, X_test, y_test = load_splits(SPLITS)
    num_cols, cat_cols = detect_column_types(X_train)

    num_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    cat_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
            # produce sparse output to limit memory use
            (
                "ohe",
                OneHotEncoder(
                    handle_unknown="ignore", sparse_output=True, drop="if_binary"
                ),
            ),
        ]
    )

    pre = ColumnTransformer(
        [
            ("num", num_pipeline, num_cols),
            ("cat", cat_pipeline, cat_cols),
        ],
        remainder="drop",
    )

    pipe = Pipeline(
        [
            ("pre", pre),
            ("rf", RandomForestRegressor(random_state=random_state, n_jobs=-1)),
        ]
    )

    param_dist = {
        "rf__n_estimators": [100, 200, 300],
        "rf__max_depth": [None, 10, 20, 30],
        "rf__max_features": ["auto", "sqrt", 0.2, 0.5],
        "rf__min_samples_split": [2, 5, 10],
    }

    search = RandomizedSearchCV(
        pipe,
        param_dist,
        n_iter=n_iter,
        scoring="neg_mean_absolute_error",
        cv=3,
        random_state=random_state,
        verbose=1,
    )
    search.fit(X_train, y_train)

    best = search.best_estimator_
    OUT_MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best, OUT_MODEL)

    # Evaluate
    X_test_pre = best.named_steps["pre"].transform(X_test)
    # if sparse, convert to dense for sklearn estimator
    try:
        if hasattr(X_test_pre, "toarray"):
            X_test_pre = X_test_pre.toarray()
    except Exception:
        pass
    preds = best.named_steps["rf"].predict(X_test_pre)
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))

    OUT_PLOTS.mkdir(parents=True, exist_ok=True)
    # Actual vs Predicted
    plt.figure(figsize=(6, 6))
    sns.scatterplot(x=y_test, y=preds, alpha=0.5)
    lims = [min(y_test.min(), preds.min()), max(y_test.max(), preds.max())]
    plt.plot(lims, lims, "--", color="gray")
    plt.xlabel("Actual")
    plt.ylabel("Predicted")
    plt.title("v2 Actual vs Predicted")
    plt.tight_layout()
    plt.savefig(OUT_PLOTS / "actual_vs_predicted.png")
    plt.close()

    # Residuals
    errors = preds - y_test.values
    plt.figure(figsize=(6, 4))
    sns.histplot(errors, kde=True, bins=50)
    plt.xlabel("Residual")
    plt.title("v2 Residuals Distribution")
    plt.tight_layout()
    plt.savefig(OUT_PLOTS / "residuals_distribution.png")
    plt.close()

    # Error histogram
    plt.figure(figsize=(6, 4))
    sns.histplot(np.abs(errors), bins=50)
    plt.xlabel("Absolute Error")
    plt.title("v2 Absolute Error Histogram")
    plt.tight_layout()
    plt.savefig(OUT_PLOTS / "error_histogram.png")
    plt.close()

    metrics = {"MAE": mae, "RMSE": rmse, "R2": r2}
    OUT_METRICS.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_METRICS, "w") as fh:
        json.dump(metrics, fh, indent=2)

    print("Saved v2 model to", OUT_MODEL)
    print("Saved v2 metrics to", OUT_METRICS)
    print("Saved v2 plots to", OUT_PLOTS)

    return search


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--n-iter", type=int, default=12)
    args = parser.parse_args()
    train_v2(random_state=args.random_state, n_iter=args.n_iter)
