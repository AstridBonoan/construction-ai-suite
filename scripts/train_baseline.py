#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Train a simple baseline RandomForest for `will_delay` using existing row-level splits.

This script:
 - Loads `data_splits/X_train.csv`, `y_train.csv`, `X_val.csv`, `y_val.csv`, `X_test.csv`, `y_test.csv`.
 - Builds preprocessing pipeline: numeric impute+scale, categorical impute+OHE.
 - Trains RandomForestClassifier with `class_weight='balanced'`.
 - Evaluates on validation and test sets and saves metrics and model.
"""

from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_splits(splits_dir: Path):
    X_train = pd.read_csv(splits_dir / "X_train.csv")
    y_train = pd.read_csv(splits_dir / "y_train.csv").iloc[:, 0]
    X_val = pd.read_csv(splits_dir / "X_val.csv")
    y_val = pd.read_csv(splits_dir / "y_val.csv").iloc[:, 0]
    X_test = pd.read_csv(splits_dir / "X_test.csv")
    y_test = pd.read_csv(splits_dir / "y_test.csv").iloc[:, 0]
    return X_train, y_train, X_val, y_val, X_test, y_test


def build_pipeline(X_sample: pd.DataFrame) -> Pipeline:
    numeric_cols = X_sample.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X_sample.select_dtypes(
        include=["object", "category"]
    ).columns.tolist()

    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ],
        remainder="drop",
    )

    clf = RandomForestClassifier(
        n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=42
    )
    pipeline = Pipeline([("preprocessor", preprocessor), ("clf", clf)])
    return pipeline


def evaluate(model: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    preds = model.predict(X)
    probs = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else None
    return {
        "accuracy": float(accuracy_score(y, preds)),
        "precision": float(precision_score(y, preds, zero_division=0)),
        "recall": float(recall_score(y, preds, zero_division=0)),
        "f1": float(f1_score(y, preds, zero_division=0)),
        "roc_auc": (
            float(roc_auc_score(y, probs))
            if probs is not None and len(np.unique(y)) > 1
            else None
        ),
        "confusion_matrix": confusion_matrix(y, preds).tolist(),
    }


def parse_args():
    p = argparse.ArgumentParser(description="Train baseline model for will_delay")
    p.add_argument(
        "--splits-dir",
        "-s",
        default="data_splits",
        help="Directory containing split CSVs",
    )
    p.add_argument(
        "--model-out", default="models/baseline_rf_v1.joblib", help="Model output path"
    )
    p.add_argument(
        "--metrics-out",
        default="data_splits/baseline_metrics.json",
        help="Metrics JSON output path",
    )
    return p.parse_args()


def main():
    args = parse_args()
    X_train, y_train, X_val, y_val, X_test, y_test = load_splits(Path(args.splits_dir))

    # Ensure categorical columns are strings to avoid mixed-type issues
    for df in (X_train, X_val, X_test):
        for c in df.select_dtypes(include=["object"]).columns:
            df[c] = df[c].astype(str).fillna("__MISSING__")

    # Sanity checks for positives
    for name, y in (("train", y_train), ("val", y_val)):
        pos = int((y == 1).sum())
        logger.info(
            "%s: rows=%d, positives=%d (%.2f%%)",
            name,
            len(y),
            pos,
            100.0 * pos / len(y) if len(y) > 0 else 0.0,
        )
        if pos == 0:
            logger.error("No positive examples in %s set — aborting", name)
            raise SystemExit(2)

    pipeline = build_pipeline(X_train)
    logger.info("Fitting pipeline and classifier...")
    pipeline.fit(X_train, y_train)

    metrics_val = evaluate(pipeline, X_val, y_val)
    logger.info("Validation metrics: %s", json.dumps(metrics_val, indent=2))

    metrics_test = evaluate(pipeline, X_test, y_test)
    logger.info("Test metrics: %s", json.dumps(metrics_test, indent=2))

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    dump(pipeline, args.model_out)
    logger.info("Saved model to %s", args.model_out)

    with open(args.metrics_out, "w") as fh:
        json.dump({"validation": metrics_val, "test": metrics_test}, fh, indent=2)
    logger.info("Saved metrics to %s", args.metrics_out)


if __name__ == "__main__":
    main()
    pipeline = build_pipeline(X_train)
