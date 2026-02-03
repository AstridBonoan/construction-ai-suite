#!/usr/bin/env python3
"""Prepare relaxed splits and run exploratory training on v8 relaxed aggregated CSV.

Outputs:
- data_splits/v8/X_train_relaxed.csv, X_test_relaxed.csv, y_train_relaxed.csv, y_test_relaxed.csv
- diagnostics: data_splits/v8/diagnostics_relaxed_training.txt
- model: models/v8/model_relaxed.joblib (if trained)
- metrics: models/v8/metrics_relaxed.json
- model card: MODEL_CARD_relaxed.md
"""

import os
from pathlib import Path
import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
import joblib

ROOT = Path(".")
IN_AGG = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT_DIR = ROOT / "data_splits" / "v8"
MODEL_DIR = ROOT / "models" / "v8"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if not IN_AGG.exists():
        raise FileNotFoundError(f"Input aggregated not found: {IN_AGG}")
    agg = pd.read_csv(IN_AGG, dtype=str)

    # Ensure numeric conversions
    for n in [
        "planned_duration_days",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
    ]:
        if n in agg.columns:
            agg[n] = pd.to_numeric(agg[n], errors="coerce")
        else:
            agg[n] = np.nan

    # Imputation flags
    agg["actual_start_imputed"] = (
        agg.get("actual_start_imputed", False).astype(str).fillna("False")
    )
    agg["imputation_rule"] = agg.get("imputation_rule", "none").fillna("none")

    # Assign label_confidence
    def assign_confidence(row):
        imputed = str(row["actual_start_imputed"]).strip().lower() in (
            "1",
            "true",
            "t",
            "yes",
        )
        rule = str(row["imputation_rule"] or "").strip()
        pdur = row.get("planned_duration_days")
        try:
            pdur = float(pdur)
        except Exception:
            pdur = np.nan
        if not imputed:
            return "high"
        # imputed
        if rule.lower() in ("rulea", "rulec") and not np.isnan(pdur) and pdur > 0:
            return "medium"
        return "low"

    agg["label_confidence"] = agg.apply(assign_confidence, axis=1)

    # Filter to rows with computable numeric delay_days
    computable = agg[agg["delay_days"].notna()].copy()

    # Save counts by confidence
    counts_conf = computable["label_confidence"].value_counts(dropna=False).to_dict()
    total_computable = len(computable)

    # Prepare X and y
    # Use will_delay label if present, else create binary from delay_days>0
    if "will_delay" in computable.columns:
        computable["will_delay"] = (
            pd.to_numeric(computable["will_delay"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
    else:
        computable["will_delay"] = (computable["delay_days"] > 0).astype(int)

    y = computable["will_delay"]
    X = computable.drop(
        columns=["will_delay", "will_delay_abs30", "will_delay_rel5pct"], errors=True
    )

    # Save full computable CSV for reference
    computable.to_csv(
        OUT_DIR / "project_level_aggregated_v8_relaxed_computable.csv", index=False
    )

    # Splitting
    # Keep all computable rows in splits; user may later filter by confidence
    stratify = y if y.nunique() > 1 and y.sum() > 0 else None
    if len(X) < 2:
        X_train = X.copy()
        X_test = X.iloc[0:0].copy()
        y_train = y.copy()
        y_test = y.iloc[0:0].copy()
    else:
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=stratify
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

    # Save relaxed splits
    X_train.to_csv(OUT_DIR / "X_train_relaxed.csv", index=False)
    X_test.to_csv(OUT_DIR / "X_test_relaxed.csv", index=False)
    y_train.to_frame("will_delay").to_csv(OUT_DIR / "y_train_relaxed.csv", index=False)
    y_test.to_frame("will_delay").to_csv(OUT_DIR / "y_test_relaxed.csv", index=False)

    # Also save a filtered-by-confidence version (exclude low)
    keep_mask = computable["label_confidence"].isin(["high", "medium"])
    comp_filtered = computable.loc[keep_mask]
    if len(comp_filtered) >= 1:
        yf = comp_filtered["will_delay"]
        Xf = comp_filtered.drop(
            columns=["will_delay", "will_delay_abs30", "will_delay_rel5pct"],
            errors=True,
        )
        if len(Xf) < 2:
            Xf_train = Xf.copy()
            Xf_test = Xf.iloc[0:0].copy()
            yf_train = yf.copy()
            yf_test = yf.iloc[0:0].copy()
        else:
            try:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(
                    Xf,
                    yf,
                    test_size=0.2,
                    random_state=42,
                    stratify=(yf if yf.nunique() > 1 and yf.sum() > 0 else None),
                )
            except Exception:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(
                    Xf, yf, test_size=0.2, random_state=42
                )
        Xf_train.to_csv(OUT_DIR / "X_train_relaxed_filtered.csv", index=False)
        Xf_test.to_csv(OUT_DIR / "X_test_relaxed_filtered.csv", index=False)
        yf_train.to_frame("will_delay").to_csv(
            OUT_DIR / "y_train_relaxed_filtered.csv", index=False
        )
        yf_test.to_frame("will_delay").to_csv(
            OUT_DIR / "y_test_relaxed_filtered.csv", index=False
        )

    # Training: basic RandomForest on numeric columns
    # Drop deny-list columns
    DENY_LIST = set(
        [
            c.lower()
            for c in (
                [
                    "will_delay",
                    "schedule_slippage_pct",
                    "award",
                    "bbl",
                    "bin",
                    "cost",
                    "cost_estimated",
                ]
            )
        ]
    )
    for df in (X_train, X_test):
        for c in list(df.columns):
            if c.lower() in DENY_LIST:
                df.drop(columns=[c], inplace=True, errors="ignore")

    # Keep numeric features only
    numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    X_train_num = X_train[numeric_cols].fillna(0)
    X_test_num = X_test[numeric_cols].fillna(0)

    train_counts = y_train.value_counts(dropna=False).to_dict()
    test_counts = y_test.value_counts(dropna=False).to_dict()

    metrics = {
        "train_counts": train_counts,
        "test_counts": test_counts,
        "counts_by_confidence": counts_conf,
    }

    model_path = MODEL_DIR / "model_relaxed.joblib"
    metrics_path = MODEL_DIR / "metrics_relaxed.json"

    if (
        len(train_counts) <= 1
        or sum(v for k, v in train_counts.items() if str(k) in ("1", "True")) == 0
    ):
        metrics["warning"] = (
            "Single-class or no positive examples in training set; skipping model training."
        )
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        # write model card
        with open("MODEL_CARD_relaxed.md", "w") as f:
            f.write("# Model Card - v8 relaxed baseline\n\n")
            f.write("Training skipped: insufficient positive examples.\n")
    else:
        clf = RandomForestClassifier(
            n_estimators=100, random_state=42, class_weight="balanced"
        )
        clf.fit(X_train_num, y_train)
        y_pred = clf.predict(X_test_num)
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        metrics.update({"accuracy": acc, "precision": prec, "recall": rec, "f1": f1})
        joblib.dump(clf, model_path)
        with open("MODEL_CARD_relaxed.md", "w") as f:
            f.write("# Model Card - v8 relaxed baseline\n\n")
            f.write(f"Training size: {len(X_train_num)}\n")
            f.write("Train label counts:\n")
            f.write(json.dumps(train_counts) + "\n")
            f.write("Test label counts:\n")
            f.write(json.dumps(test_counts) + "\n")
            f.write("\nMetrics:\n")
            f.write(
                json.dumps(
                    {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
                    indent=2,
                )
                + "\n"
            )

    # Write metrics & diagnostics
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    diag_path = OUT_DIR / "diagnostics_relaxed_training.txt"
    with open(diag_path, "w") as f:
        f.write(f"total_computable={total_computable}\n")
        f.write("counts_by_confidence=" + json.dumps(counts_conf) + "\n")
        f.write("train_label_counts=" + json.dumps(train_counts) + "\n")
        f.write("test_label_counts=" + json.dumps(test_counts) + "\n")

    print("Wrote relaxed splits and diagnostics to", OUT_DIR)
    print("Wrote metrics to", metrics_path)
    print("Wrote model card to MODEL_CARD_relaxed.md")


if __name__ == "__main__":
    main()
