#!/usr/bin/env python3
"""
Train and save a baseline classifier and preprocessing pipeline.

Saves:
 - models/baseline_model.joblib (full pipeline: preprocessor + classifier)
 - models/baseline_rf_v1.joblib (same, for compatibility)
 - models/preprocessing_pipeline.joblib (preprocessor only)

This script uses the CSV splits in `data_splits/` and DOES NOT modify them.
"""
from __future__ import annotations
import logging
from pathlib import Path

import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
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


def build_preprocessor(X: pd.DataFrame):
    # Identify numeric and categorical columns
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

    logger.info("Numeric columns: %d, Categorical columns: %d", len(numeric_cols), len(categorical_cols))

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
        ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer([
        ("num", numeric_pipeline, numeric_cols),
        ("cat", categorical_pipeline, categorical_cols),
    ], remainder="drop")

    return preprocessor


def main():
    splits_dir = Path("data_splits")
    model_dir = Path("models")
    model_dir.mkdir(parents=True, exist_ok=True)

    X_train, y_train, X_val, y_val, X_test, y_test = load_splits(splits_dir)

    # Ensure categorical columns are strings to avoid mixed-type issues
    for df in (X_train, X_val, X_test):
        for c in df.select_dtypes(include=["object"]).columns:
            df[c] = df[c].astype(str).fillna("__MISSING__")

    preprocessor = build_preprocessor(X_train)

    clf = RandomForestClassifier(n_estimators=200, class_weight="balanced", n_jobs=-1, random_state=42)

    pipeline = Pipeline([("preprocessor", preprocessor), ("clf", clf)])

    logger.info("Fitting pipeline on training data (%d rows)", len(X_train))
    pipeline.fit(X_train, y_train)

    # Save the full pipeline and the preprocessor separately
    full_model_path = model_dir / "baseline_model.joblib"
    compat_model_path = model_dir / "baseline_rf_v1.joblib"
    preproc_path = model_dir / "preprocessing_pipeline.joblib"

    dump(pipeline, full_model_path)
    dump(pipeline, compat_model_path)
    dump(preprocessor, preproc_path)

    logger.info("Saved full pipeline to %s and %s", full_model_path, compat_model_path)
    logger.info("Saved preprocessor to %s", preproc_path)


if __name__ == "__main__":
    main()
