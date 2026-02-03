"""
Train and evaluate models on the prepared project dataset splits.

Usage example:
python scripts/train_and_evaluate.py --data-dir data_splits --random-state 42

This script:
- Loads `X_train.csv`, `y_train.csv`, `X_val.csv`, `y_val.csv`, `X_test.csv`, `y_test.csv` from `--data-dir`.
- Builds preprocessing pipelines for numeric and categorical features.
- Trains Logistic Regression and Random Forest (with GridSearchCV tuning).
- Evaluates on validation and test sets (accuracy, precision, recall, f1, roc-auc, confusion matrix).
- Saves models to `logistic_model_v1.pkl` and `rf_model_v1.pkl` in `--output-dir`.
- Saves evaluation plots (ROC curves and confusion matrices) to `--output-dir`.

"""

from __future__ import annotations
import argparse
import logging
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_splits(data_dir: Path):
    """Load split CSV files from data_dir and return DataFrames."""
    X_train = pd.read_csv(data_dir / "X_train.csv", low_memory=False)
    y_train = pd.read_csv(data_dir / "y_train.csv", low_memory=False)
    X_val = pd.read_csv(data_dir / "X_val.csv", low_memory=False)
    y_val = pd.read_csv(data_dir / "y_val.csv", low_memory=False)
    X_test = pd.read_csv(data_dir / "X_test.csv", low_memory=False)
    y_test = pd.read_csv(data_dir / "y_test.csv", low_memory=False)
    # If y are single-column DataFrames, convert to Series
    if y_train.shape[1] == 1:
        y_train = y_train.iloc[:, 0]
    if y_val.shape[1] == 1:
        y_val = y_val.iloc[:, 0]
    if y_test.shape[1] == 1:
        y_test = y_test.iloc[:, 0]
    return X_train, y_train, X_val, y_val, X_test, y_test


def build_preprocessor(X: pd.DataFrame):
    """Create a ColumnTransformer to process numeric and categorical features.

    - Numeric: SimpleImputer(mean) -> StandardScaler
    - Categorical: SimpleImputer(constant 'Unknown') -> OneHotEncoder(handle_unknown='ignore')

    Returns the transformer and lists of feature names for later mapping.
    """
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="mean")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        [
            ("num", numeric_transformer, numeric_cols),
            ("cat", categorical_transformer, categorical_cols),
        ],
        remainder="drop",
    )

    return preprocessor, numeric_cols, categorical_cols


def train_logistic(X_train, y_train, preprocessor, class_weight=None, random_state=42):
    """Train a logistic regression model wrapped in a pipeline.

    Returns the fitted pipeline.
    """
    pipe = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000, class_weight=class_weight, random_state=random_state
                ),
            ),
        ]
    )
    pipe.fit(X_train, y_train)
    return pipe


def train_random_forest(X_train, y_train, preprocessor, random_state=42):
    """Train a Random Forest with basic GridSearchCV on training data.

    Returns the best estimator from GridSearchCV.
    """
    rf = RandomForestClassifier(random_state=random_state, n_jobs=-1)
    pipe = Pipeline([("preprocessor", preprocessor), ("clf", rf)])

    param_grid = {
        "clf__n_estimators": [100, 200],
        "clf__max_depth": [None, 10, 20],
        "clf__min_samples_split": [2, 5],
    }

    gs = GridSearchCV(pipe, param_grid, cv=3, scoring="roc_auc", n_jobs=-1, verbose=1)
    gs.fit(X_train, y_train)
    logger.info("Random Forest best params: %s", gs.best_params_)
    return gs.best_estimator_, gs.best_params_


def evaluate_model(model, X, y, set_name: str, out_dir: Path, plot_prefix: str):
    """Evaluate a fitted pipeline on (X, y), print metrics and save plots.

    Returns a dict of metrics.
    """
    y_pred = model.predict(X)
    # try probability for ROC AUC
    try:
        y_proba = model.predict_proba(X)[:, 1]
    except Exception:
        # fallback to decision_function if available
        try:
            y_proba = model.decision_function(X)
        except Exception:
            y_proba = None

    acc = accuracy_score(y, y_pred)
    prec = precision_score(y, y_pred, zero_division=0)
    rec = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y, y_proba) if y_proba is not None else float("nan")

    logger.info(
        "%s - Accuracy: %.4f, Precision: %.4f, Recall: %.4f, F1: %.4f, ROC-AUC: %.4f",
        set_name,
        acc,
        prec,
        rec,
        f1,
        roc_auc,
    )

    # Confusion matrix
    cm = confusion_matrix(y, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    fig, ax = plt.subplots(figsize=(4, 4))
    disp.plot(ax=ax)
    plt.title(f"Confusion Matrix - {plot_prefix} - {set_name}")
    plt.tight_layout()
    cm_path = out_dir / f"{plot_prefix}_{set_name}_confusion_matrix.png"
    plt.savefig(cm_path)
    plt.close()

    # ROC curve
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y, y_proba)
        plt.figure(figsize=(6, 4))
        plt.plot(fpr, tpr, label=f"ROC (AUC={roc_auc:.3f})")
        plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"ROC Curve - {plot_prefix} - {set_name}")
        plt.legend(loc="lower right")
        roc_path = out_dir / f"{plot_prefix}_{set_name}_roc.png"
        plt.tight_layout()
        plt.savefig(roc_path)
        plt.close()

    return {
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": roc_auc,
    }


def extract_logistic_coefficients(
    model: Pipeline, numeric_cols: List[str], categorical_cols: List[str]
):
    """Return a DataFrame of feature names and logistic coefficients.

    Assumes `model` is a pipeline with a ColumnTransformer preprocessor and a logistic classifier.
    """
    # Retrieve preprocessor and classifier
    preprocessor = model.named_steps["preprocessor"]
    clf = model.named_steps["clf"]

    # numeric feature names
    feature_names: List[str] = []
    if "num" in preprocessor.named_transformers_:
        feature_names.extend(numeric_cols)
    # categorical one-hot names
    if "cat" in preprocessor.named_transformers_:
        cat_trans = preprocessor.named_transformers_["cat"]
        # cat_trans is a Pipeline [imputer, onehot]
        onehot: OneHotEncoder = cat_trans.named_steps["onehot"]
        cat_names = onehot.get_feature_names_out(categorical_cols).tolist()
        feature_names.extend(cat_names)

    coefs = clf.coef_.ravel()
    return pd.DataFrame({"feature": feature_names, "coefficient": coefs}).sort_values(
        by="coefficient", key=lambda s: np.abs(s), ascending=False
    )


def extract_rf_importances(
    model: Pipeline, numeric_cols: List[str], categorical_cols: List[str]
):
    """Return a DataFrame of feature names and Random Forest importances.

    Assumes `model` is a pipeline with a ColumnTransformer preprocessor and a RandomForestClassifier.
    """
    preprocessor = model.named_steps["preprocessor"]
    clf = model.named_steps["clf"]

    feature_names: List[str] = []
    if "num" in preprocessor.named_transformers_:
        feature_names.extend(numeric_cols)
    if "cat" in preprocessor.named_transformers_:
        cat_trans = preprocessor.named_transformers_["cat"]
        onehot: OneHotEncoder = cat_trans.named_steps["onehot"]
        cat_names = onehot.get_feature_names_out(categorical_cols).tolist()
        feature_names.extend(cat_names)

    importances = clf.feature_importances_
    return pd.DataFrame(
        {"feature": feature_names, "importance": importances}
    ).sort_values(by="importance", ascending=False)


def parse_args():
    p = argparse.ArgumentParser(
        description="Train and evaluate models on prepared splits"
    )
    p.add_argument(
        "--data-dir",
        "-d",
        default="data_splits",
        help="Directory containing X_/y_ CSV splits",
    )
    p.add_argument(
        "--output-dir",
        "-o",
        default="models",
        help="Directory to save models and plots",
    )
    p.add_argument(
        "--random-state",
        "-r",
        default=42,
        type=int,
        help="Random seed for reproducibility",
    )
    return p.parse_args()


def main():
    args = parse_args()
    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load splits
    X_train, y_train, X_val, y_val, X_test, y_test = load_splits(data_dir)
    logger.info("Loaded splits: X_train=%s, y_train=%s", X_train.shape, y_train.shape)

    # Ensure target is binary ints
    y_train = y_train.astype(int)
    y_val = y_val.astype(int)
    y_test = y_test.astype(int)

    # Drop columns that are constant or entirely missing in the training set,
    # and drop obvious identifier/source columns that shouldn't be used as features.
    drop_const = [
        c
        for c in X_train.columns
        if X_train[c].nunique(dropna=True) <= 1 or X_train[c].isna().all()
    ]
    drop_identifiers = [
        c
        for c in X_train.columns
        if ("project" in c.lower() and "id" in c.lower())
        or c.lower() in ("source_file", "source", "project_id", "id")
    ]
    drop_cols = sorted(set(drop_const + drop_identifiers))
    if drop_cols:
        logger.info(
            "Dropping %d columns from features (constant/identifier): %s",
            len(drop_cols),
            drop_cols[:10],
        )
        X_train = X_train.drop(columns=drop_cols, errors="ignore")
        X_val = X_val.drop(columns=drop_cols, errors="ignore")
        X_test = X_test.drop(columns=drop_cols, errors="ignore")

    # Class distribution
    class_counts = y_train.value_counts()
    logger.info("Training class distribution:\n%s", class_counts.to_string())

    # Build preprocessor
    preprocessor, numeric_cols, categorical_cols = build_preprocessor(X_train)
    logger.info(
        "Numeric cols: %d, Categorical cols: %d",
        len(numeric_cols),
        len(categorical_cols),
    )

    # If imbalance, use balanced class weight for logistic
    imbalance = (
        (class_counts.min() / class_counts.max()) < 0.5
        if len(class_counts) > 1
        else False
    )
    class_weight = "balanced" if imbalance else None
    if imbalance:
        logger.info(
            "Detected imbalance; using class_weight='balanced' for LogisticRegression"
        )

    # Train logistic regression
    log_pipe = train_logistic(
        X_train,
        y_train,
        preprocessor,
        class_weight=class_weight,
        random_state=args.random_state,
    )

    # Train random forest with GridSearchCV
    rf_best, rf_best_params = train_random_forest(
        X_train, y_train, preprocessor, random_state=args.random_state
    )

    # Evaluate on validation set
    metrics_log_val = evaluate_model(
        log_pipe, X_val, y_val, "Validation", out_dir, "logistic"
    )
    metrics_rf_val = evaluate_model(rf_best, X_val, y_val, "Validation", out_dir, "rf")

    # Evaluate on test set
    metrics_log_test = evaluate_model(
        log_pipe, X_test, y_test, "Test", out_dir, "logistic"
    )
    metrics_rf_test = evaluate_model(rf_best, X_test, y_test, "Test", out_dir, "rf")

    # Feature importances / coefficients
    log_coefs = extract_logistic_coefficients(log_pipe, numeric_cols, categorical_cols)
    rf_imps = extract_rf_importances(rf_best, numeric_cols, categorical_cols)

    log_coefs.to_csv(out_dir / "logistic_coefficients.csv", index=False)
    rf_imps.to_csv(out_dir / "rf_feature_importances.csv", index=False)
    logger.info("Saved feature importance files to %s", out_dir)

    # Save models
    dump(log_pipe, out_dir / "logistic_model_v1.pkl")
    dump(rf_best, out_dir / "rf_model_v1.pkl")
    logger.info("Saved models to %s", out_dir)

    # Print a short summary
    print("\nValidation metrics - Logistic:", metrics_log_val)
    print("Validation metrics - Random Forest:", metrics_rf_val)
    print("\nTest metrics - Logistic:", metrics_log_test)
    print("Test metrics - Random Forest:", metrics_rf_test)


if __name__ == "__main__":
    main()
