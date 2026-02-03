#!/usr/bin/env python3
"""Leakage audit: compute correlations between features and targets, flag suspicious features.

Outputs:
- analysis_outputs/leakage_audit/feature_correlations.csv
- analysis_outputs/leakage_audit/diagnostics.txt
- analysis_outputs/leakage_audit/heatmap.png
- analysis_outputs/leakage_audit/top_correlated_bar.png

Run inside project root (container):
    python3 scripts/leakage_audit.py
"""

from __future__ import annotations
import math
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(".")
SPLITS = ROOT / "data_splits"
OUT = ROOT / "analysis_outputs" / "leakage_audit"
OUT.mkdir(parents=True, exist_ok=True)


def is_id_like(col: str) -> bool:
    lc = col.lower()
    id_keywords = ["id", "project", "proj", "uid", "ref", "reference"]
    return any(k in lc for k in id_keywords) and not ("date" in lc)


def is_date_like(col: str) -> bool:
    lc = col.lower()
    date_keywords = ["date", "start", "end", "planned", "actual", "through"]
    return any(k in lc for k in date_keywords)


def analyze():
    # Load splits
    X_train_path = SPLITS / "X_train.csv"
    y_train_path = SPLITS / "y_train.csv"

    if not X_train_path.exists() or not y_train_path.exists():
        print("Missing split files in", SPLITS)
        return 1

    X = pd.read_csv(X_train_path, low_memory=False)
    y = pd.read_csv(y_train_path, low_memory=False)
    if isinstance(y, pd.DataFrame) and y.shape[1] == 1:
        y = y.iloc[:, 0]

    # Try to locate schedule_slippage_pct in X or in aggregated file
    schedule_col = None
    if "schedule_slippage_pct" in X.columns:
        schedule_col = "schedule_slippage_pct"
    else:
        # look for aggregated file
        agg = ROOT / "data_splits" / "project_dataset_v1_cleaned.csv"
        if agg.exists():
            dfagg = pd.read_csv(agg, low_memory=False)
            if "schedule_slippage_pct" in dfagg.columns:
                # try to align by index if possible (skip alignment if indices differ)
                schedule_col = "schedule_slippage_pct"
                # merge schedule into X if shared index present
                if len(dfagg) == len(X):
                    try:
                        X[schedule_col] = dfagg[schedule_col].values
                    except Exception:
                        pass

    # Prepare results
    rows = []

    # For each column compute correlation with will_delay (y) and with schedule_slippage_pct if available
    for col in X.columns:
        col_series = X[col]
        # compute basic stats
        nunique = col_series.nunique(dropna=True)
        dtype = str(col_series.dtype)
        const = nunique <= 1
        id_like = is_id_like(col)
        date_like = is_date_like(col)

        # prepare numeric representation for correlation
        # if numeric, use as-is; else factorize
        if pd.api.types.is_numeric_dtype(col_series):
            col_num = pd.to_numeric(col_series, errors="coerce")
        else:
            col_num, _ = pd.factorize(col_series.astype(str))

        # compute Pearson correlation with binary target y
        try:
            corr_with_y = float(pd.Series(col_num).corr(pd.Series(y).astype(float)))
        except Exception:
            corr_with_y = float("nan")

        corr_with_schedule = float("nan")
        if schedule_col and schedule_col in X.columns:
            try:
                s = pd.to_numeric(X[schedule_col], errors="coerce")
                corr_with_schedule = float(pd.Series(col_num).corr(s))
            except Exception:
                corr_with_schedule = float("nan")

        rows.append(
            {
                "feature": col,
                "dtype": dtype,
                "nunique": nunique,
                "constant": const,
                "id_like": id_like,
                "date_like": date_like,
                "corr_with_will_delay": corr_with_y,
                "abs_corr_with_will_delay": (
                    abs(corr_with_y) if not math.isnan(corr_with_y) else float("nan")
                ),
                "corr_with_schedule_slippage_pct": corr_with_schedule,
                "abs_corr_with_schedule_slippage_pct": (
                    abs(corr_with_schedule)
                    if not math.isnan(corr_with_schedule)
                    else float("nan")
                ),
            }
        )

    dfres = pd.DataFrame(rows).sort_values(
        by="abs_corr_with_will_delay", ascending=False
    )
    dfres.to_csv(OUT / "feature_correlations.csv", index=False)

    # diagnostics summary
    diag_lines = []
    diag_lines.append(f"Total features analyzed: {len(dfres)}")
    const_count = int(dfres["constant"].sum())
    diag_lines.append(f"Constant columns: {const_count}")
    id_count = int(dfres["id_like"].sum())
    diag_lines.append(f"ID-like columns: {id_count}")

    high_corr = dfres[dfres["abs_corr_with_will_delay"] >= 0.9]
    diag_lines.append(f"Features with |corr(will_delay)| >= 0.9: {len(high_corr)}")
    if len(high_corr) > 0:
        diag_lines.append("Top high-correlation features:")
        for _, r in high_corr.head(20).iterrows():
            diag_lines.append(
                f" - {r['feature']}: corr_with_will_delay={r['corr_with_will_delay']:.4f}, constant={r['constant']}, id_like={r['id_like']}, date_like={r['date_like']}"
            )

    # also check schedule correlations if present
    if schedule_col and schedule_col in X.columns:
        high_sched = dfres[dfres["abs_corr_with_schedule_slippage_pct"] >= 0.9]
        diag_lines.append(
            f"Features with |corr(schedule_slippage_pct)| >= 0.9: {len(high_sched)}"
        )
        for _, r in high_sched.head(20).iterrows():
            diag_lines.append(
                f" - {r['feature']}: corr_with_schedule={r['corr_with_schedule_slippage_pct']:.4f}"
            )

    # Suggest removals: id-like, date-like, constant, or very high corr
    suggestions = []
    for _, r in dfres.iterrows():
        if (
            r["constant"]
            or r["id_like"]
            or r["date_like"]
            or r["abs_corr_with_will_delay"] >= 0.95
            or r["abs_corr_with_schedule_slippage_pct"] >= 0.95
        ):
            suggestions.append(r["feature"])

    diag_lines.append(
        "\nSuggested features to inspect/remove (id/date/constant/high-corr):"
    )
    diag_lines.extend([f" - {f}" for f in suggestions[:200]])

    with open(OUT / "diagnostics.txt", "w") as fh:
        fh.write("\n".join(diag_lines))

    # Visualizations
    try:
        topn = dfres[~dfres["abs_corr_with_will_delay"].isna()].head(30)
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            topn[["corr_with_will_delay", "corr_with_schedule_slippage_pct"]]
            .astype(float)
            .fillna(0)
            .T,
            annot=True,
            cmap="coolwarm",
        )
        plt.title("Top features: correlations with targets")
        plt.tight_layout()
        plt.savefig(OUT / "heatmap.png")

        # bar plot
        plt.figure(figsize=(10, 6))
        sns.barplot(
            x="abs_corr_with_will_delay",
            y="feature",
            data=topn.head(20),
            palette="viridis",
        )
        plt.xlabel("|corr(feature, will_delay)|")
        plt.tight_layout()
        plt.savefig(OUT / "top_correlated_bar.png")
    except Exception as e:
        print("Visualization failed:", e)

    print("Leakage audit saved to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(analyze())
