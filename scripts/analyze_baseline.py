#!/usr/bin/env python3
"""
Post-training analysis for the baseline `will_delay` model.

Loads a trained pipeline (preprocessor + classifier), evaluates on the
validation set, produces metrics, ROC/PR curves, and a feature-importance
bar chart for the top features.

Outputs:
 - data_splits/baseline_model_metrics.csv
 - data_splits/baseline_metrics.json
 - data_splits/feature_importance.png
 - data_splits/roc_curve.png
 - data_splits/precision_recall_curve.png (optional)

This script does NOT retrain the model; it only loads an existing model.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from joblib import load
from sklearn.metrics import (auc, average_precision_score, confusion_matrix,
                             precision_recall_curve, roc_curve, roc_auc_score,
                             accuracy_score, precision_score, recall_score, f1_score)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_model(path: Path):
    """Load a joblib pipeline from `path`."""
    logger.info("Loading model from %s", path)
    return load(path)


def load_splits(splits_dir: Path):
    """Load X_val and y_val from `splits_dir`."""
    X_val = pd.read_csv(splits_dir / "X_val.csv")
    y_val = pd.read_csv(splits_dir / "y_val.csv").iloc[:, 0]
    return X_val, y_val


def get_feature_names_from_preprocessor(preprocessor, input_df: pd.DataFrame) -> List[str]:
    """Extract feature names after the preprocessor transformation.

    Works for a ColumnTransformer where transformers were created with explicit
    column name lists (as in the baseline pipeline).
    """
    feature_names: List[str] = []
    # transformers_ holds tuples: (name, transformer, columns)
    for name, transformer, cols in preprocessor.transformers_:
        if name == "remainder":
            continue
        if transformer == "drop":
            continue

        # cols is a list of column names (we built the pipeline that way)
        if hasattr(transformer, "named_steps") and "onehot" in transformer.named_steps:
            # categorical pipeline: imputer -> onehot
            ohe = transformer.named_steps["onehot"]
            # ensure cols is list
            input_cols = list(cols)
            try:
                names = list(ohe.get_feature_names_out(input_cols))
            except Exception:
                # fallback
                names = []
                for c in input_cols:
                    # best-effort: include original name as placeholder
                    names.append(c)
            feature_names.extend(names)
        else:
            # numeric pipeline - keep original numeric column names
            feature_names.extend(list(cols))

    return feature_names


def evaluate_and_save(model, X_val: pd.DataFrame, y_val: pd.Series, out_dir: Path):
    """Evaluate the pipeline on validation data, save metrics and plots."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # Predictions and probabilities
    logger.info("Predicting on validation set (%d rows)", len(X_val))
    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1] if hasattr(model, "predict_proba") else None

    # Basic metrics
    metrics = {
        "accuracy": accuracy_score(y_val, preds),
        "precision": precision_score(y_val, preds, zero_division=0),
        "recall": recall_score(y_val, preds, zero_division=0),
        "f1": f1_score(y_val, preds, zero_division=0),
        "support_positive": int((y_val == 1).sum()),
        "support_negative": int((y_val == 0).sum()),
    }

    if probs is not None and len(np.unique(y_val)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_val, probs))
        fpr, tpr, _ = roc_curve(y_val, probs)
        roc_auc_val = auc(fpr, tpr)
    else:
        fpr = tpr = roc_auc_val = None

    # Save metrics CSV
    metrics_csv = out_dir / "baseline_model_metrics.csv"
    pd.DataFrame([metrics]).to_csv(metrics_csv, index=False)
    logger.info("Saved metrics CSV to %s", metrics_csv)

    # Save JSON for readability
    with open(out_dir / "baseline_metrics.json", "w") as fh:
        json.dump(metrics, fh, indent=2)

    # Confusion matrix
    cm = confusion_matrix(y_val, preds)
    logger.info("Confusion matrix:\n%s", cm)

    # ROC curve plot
    if probs is not None and fpr is not None:
        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, label=f"ROC (AUC = {roc_auc_val:.4f})")
        plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title("ROC Curve")
        plt.legend(loc="lower right")
        plt.tight_layout()
        roc_path = out_dir / "roc_curve.png"
        plt.savefig(roc_path)
        plt.close()
        logger.info("Saved ROC curve to %s", roc_path)

    # Precision-Recall curve (helpful for imbalanced data)
    if probs is not None:
        precision, recall, _ = precision_recall_curve(y_val, probs)
        ap = average_precision_score(y_val, probs)
        plt.figure(figsize=(6, 5))
        plt.plot(recall, precision, label=f"AP = {ap:.4f}")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Precision-Recall Curve")
        plt.legend(loc="lower left")
        plt.tight_layout()
        pr_path = out_dir / "precision_recall_curve.png"
        plt.savefig(pr_path)
        plt.close()
        logger.info("Saved precision-recall curve to %s", pr_path)

    # Feature importances: attempt to extract post-preprocessor feature names
    fi_path = out_dir / "feature_importance.png"
    try:
        preprocessor = model.named_steps["preprocessor"]
        feature_names = get_feature_names_from_preprocessor(preprocessor, X_val)
        importances = model.named_steps["clf"].feature_importances_

        if len(feature_names) != len(importances):
            # fallback: create simple numeric indices
            feature_names = [f"f{i}" for i in range(len(importances))]

        fi_series = pd.Series(importances, index=feature_names).sort_values(ascending=False)
        topk = fi_series.head(15)

        plt.figure(figsize=(8, 6))
        topk[::-1].plot(kind="barh")
        plt.title("Top 15 Feature Importances")
        plt.xlabel("Importance")
        plt.tight_layout()
        plt.savefig(fi_path)
        plt.close()
        logger.info("Saved feature importance plot to %s", fi_path)
    except Exception as exc:
        logger.warning("Could not compute feature importances: %s", exc)

    # Console summary
    pos_recall = metrics.get("recall")
    pos_f1 = metrics.get("f1")
    logger.info("Positive-class recall=%.4f, F1=%.4f", pos_recall, pos_f1)

    # Return metrics and paths for further programmatic use
    return {
        "metrics": metrics,
        "paths": {
            "metrics_csv": str(metrics_csv),
            "roc": str(out_dir / "roc_curve.png") if probs is not None else None,
            "pr": str(out_dir / "precision_recall_curve.png") if probs is not None else None,
            "feature_importance": str(fi_path) if fi_path.exists() or True else None,
        },
    }


def main():
    model_path = Path("models/baseline_rf_v1.joblib")
    splits_dir = Path("data_splits")
    out_dir = Path("data_splits")

    if not model_path.exists():
        logger.error("Model file not found at %s. Ensure the trained model exists.", model_path)
        raise SystemExit(2)

    model = load_model(model_path)
    X_val, y_val = load_splits(splits_dir)

    result = evaluate_and_save(model, X_val, y_val, out_dir)

    # Short console summary printed for quick review
    metrics = result["metrics"]
    print("\n=== Baseline Model Summary ===")
    print(f"Validation rows: {len(X_val)}")
    print(f"Positives (support): {metrics['support_positive']}")
    print(f"Negative support: {metrics['support_negative']}")
    print(f"Recall (positive class): {metrics['recall']:.4f}")
    print(f"F1 (positive class): {metrics['f1']:.4f}")
    print("Saved metrics to:", result["paths"]["metrics_csv"]) 
    print("Plots: ", result["paths"]["roc"], result["paths"]["feature_importance"])


if __name__ == "__main__":
    main()
