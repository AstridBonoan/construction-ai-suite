#!/usr/bin/env python3
"""Train baseline model on v6 splits and save artifacts.

This mirrors the v5 trainer but writes outputs to models/v6 and analysis_outputs/v6.
"""

from __future__ import annotations
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

ROOT = Path(".")
DATA_SPLITS = ROOT / "data_splits" / "v6"
OUT_MODEL = ROOT / "models" / "v6"
ANALYSIS = ROOT / "analysis_outputs" / "v6"


def load_data():
    X_train = pd.read_csv(DATA_SPLITS / "X_train.csv")
    X_test = pd.read_csv(DATA_SPLITS / "X_test.csv")
    y_train = pd.read_csv(DATA_SPLITS / "y_train.csv").squeeze()
    y_test = pd.read_csv(DATA_SPLITS / "y_test.csv").squeeze()
    return X_train, X_test, y_train, y_test


def build_pipeline(X: pd.DataFrame):
    numeric = X.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in X.columns if c not in numeric]

    num_pipeline = Pipeline(
        [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    cat_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
            ("ohe", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    pre = ColumnTransformer(
        [("num", num_pipeline, numeric), ("cat", cat_pipeline, categorical)]
    )

    pipe = Pipeline(
        [("pre", pre), ("rf", RandomForestRegressor(n_jobs=-1, random_state=42))]
    )
    return pipe


def train_and_save():
    X_train, X_test, y_train, y_test = load_data()
    pipe = build_pipeline(X_train)

    param_dist = {
        "rf__n_estimators": [100, 200, 400],
        "rf__max_depth": [None, 10, 20],
        "rf__min_samples_split": [2, 5, 10],
    }

    search = RandomizedSearchCV(
        pipe, param_distributions=param_dist, n_iter=8, cv=3, n_jobs=1, random_state=42
    )
    search.fit(X_train, y_train)

    OUT_MODEL.mkdir(parents=True, exist_ok=True)
    ANALYSIS.mkdir(parents=True, exist_ok=True)

    best = search.best_estimator_
    joblib.dump(best, OUT_MODEL / "baseline_project_delay_model_v6.pkl")

    y_pred = best.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    metrics = {
        "MAE": float(mean_absolute_error(y_test, y_pred)),
        "RMSE": float(np.sqrt(mse)),
        "R2": float(r2_score(y_test, y_pred)),
    }
    with open(ANALYSIS / "metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)

    fi = None
    try:
        rf = best.named_steps["rf"]
        pre = best.named_steps["pre"]
        # attempt to get feature names
        try:
            num_cols = pre.transformers_[0][2]
            cat_cols = pre.transformers_[1][2]
            ohe = pre.transformers_[1][1].named_steps["ohe"]
            cat_names = ohe.get_feature_names_out(cat_cols)
            feature_names = list(num_cols) + list(cat_names)
            importances = rf.feature_importances_
            fi = pd.DataFrame(
                {"feature": feature_names, "importance": importances}
            ).sort_values("importance", ascending=False)
            fi.to_csv(ANALYSIS / "feature_importances_v6.csv", index=False)
        except Exception:
            pass
    except Exception:
        pass

    with open(ANALYSIS / "train_summary.txt", "w") as fh:
        fh.write(f"Best params: {search.best_params_}\nMetrics: {metrics}\n")

    print("Training complete. Metrics:", metrics)


if __name__ == "__main__":
    train_and_save()
