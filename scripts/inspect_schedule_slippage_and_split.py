#!/usr/bin/env python3
"""
Inspect `schedule_slippage_pct`, recommend threshold, redefine `will_delay`,
prepare ML-ready features, and create/save stratified splits.

Usage (example):
  python scripts/inspect_schedule_slippage_and_split.py \
      --input-agg data_splits/project_level_aggregated.csv \
      --output-dir data_splits --random-state 42

This script is idempotent and will overwrite outputs in `--output-dir`.
"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def detect_project_id_column(df: pd.DataFrame) -> str | None:
    # heuristic: common names
    for c in df.columns:
        lc = c.lower()
        if lc in ("project_id", "project id", "proj_id", "id"):
            return c
    for c in df.columns:
        lc = c.lower()
        if "project" in lc and "id" in lc:
            return c
    return None


def load_agg(path: Path) -> pd.DataFrame:
    if not path.exists():
        logger.error("Aggregated file not found: %s", path)
        raise SystemExit(1)
    df = pd.read_csv(path, low_memory=False)
    return df


def inspect_distribution(df: pd.DataFrame, col: str, output_dir: Path) -> dict:
    # Ensure numeric
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    q = df[col].quantile([0.0, 0.25, 0.5, 0.75, 0.9, 1.0]).to_dict()
    logger.info("Descriptive quantiles for %s: %s", col, q)

    # Counts for thresholds
    thresholds = [0.0, 0.01, 0.02, 0.05]
    counts = {}
    total = len(df)
    for t in thresholds:
        n = int((df[col] > t).sum())
        counts[t] = {"count": n, "pct": 100.0 * n / total if total > 0 else 0.0}
        logger.info(">%s : %d (%.2f%%)", t, n, counts[t]["pct"])

    # Plotting
    output_dir = Path(output_dir)
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(parents=True, exist_ok=True)

    # Histogram — choose log-scale x-axis if distribution is heavily skewed
    q50 = q.get(0.5, 0.0)
    q90 = q.get(0.9, 0.0)
    use_log = False
    # Heuristic: median == 0 and 90th percentile noticeably > small epsilon -> skewed
    if q50 == 0 and q90 > 0.01:
        use_log = True

    plt.figure(figsize=(8, 4))
    if use_log:
        # histogram on log scale: shift by small epsilon to avoid log(0)
        eps = 1e-6
        sns.histplot(np.log10(df[col].clip(lower=eps)), bins=50)
        plt.xlabel(f"log10({col} + {eps})")
        plt.title(f"Histogram of {col} (log10 scale)")
        plt.tight_layout()
        plt.savefig(plot_dir / f"hist_{col}_log.png")
    else:
        sns.histplot(df[col], bins=50)
        plt.xlabel(col)
        plt.title(f"Histogram of {col}")
        plt.tight_layout()
        plt.savefig(plot_dir / f"hist_{col}.png")
    plt.close()

    # Boxplot
    plt.figure(figsize=(8, 3))
    sns.boxplot(x=df[col], orient="h")
    plt.title(f"Boxplot of {col}")
    plt.tight_layout()
    plt.savefig(plot_dir / f"box_{col}.png")
    plt.close()

    return {"quantiles": q, "counts": counts, "use_log": use_log}


def recommend_threshold(df: pd.DataFrame, col: str, target_min: float = 0.10, target_max: float = 0.30) -> float:
    # Candidate thresholds to evaluate (in increasing order)
    candidates = [0.0, 0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1]
    total = len(df)
    best = None
    best_diff = 1.0
    chosen = None
    for t in candidates:
        pct = ((df[col] > t).sum() / total) if total > 0 else 0.0
        # looking for 0.10-0.30
        diff = 0.0
        if pct < target_min:
            diff = target_min - pct
        elif pct > target_max:
            diff = pct - target_max
        else:
            # within desired range, pick this immediately (prefer smaller t for earlier warning)
            chosen = t
            break
        if diff < best_diff:
            best_diff = diff
            best = t
    if chosen is None:
        chosen = best if best is not None else 0.01
    # Add a short justification as a comment string
    justification = (
        f"Chosen threshold {chosen} yields ~{100*((df[col]>chosen).sum()/total if total>0 else 0.0):.2f}% positives; "
        f"aiming for {int(target_min*100)}–{int(target_max*100)}% positives."
    )
    logger.info("Recommendation: %s", justification)
    return chosen


def prepare_ml_dataset(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
    # Drop identifier and date-like columns
    df = df.copy()
    project_col = detect_project_id_column(df)
    drop_cols = []
    if project_col:
        drop_cols.append(project_col)
    # drop columns with 'date', 'start', 'end' tokens (but keep schedule_slippage_pct and durations)
    drop_cols += [c for c in df.columns if any(k in c.lower() for k in ("date", "start", "end")) and c not in ("schedule_slippage_pct", "planned_duration_days", "elapsed_days")]
    drop_cols = list(set(drop_cols))
    X = df.drop(columns=drop_cols + [target_col], errors="ignore")
    y = df[target_col].astype(int)
    return X, y


def create_splits(X: pd.DataFrame, y: pd.Series, random_state: int = 42) -> dict:
    # Stratified splits: test 15%, validation 15%, train 70%
    test_size = 0.15
    X_train_val, X_test, y_train_val, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
    val_frac = 0.15 / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(X_train_val, y_train_val, test_size=val_frac, random_state=random_state, stratify=y_train_val)
    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
    }


def save_splits(splits: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in splits.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        logger.info("Saved %s (%s rows) to %s", name, len(df), path)


def save_class_distribution_summary(splits: dict, output_dir: Path) -> None:
    rows = []
    for split_name in ("y_train", "y_val", "y_test"):
        ser = splits[split_name]
        total = len(ser)
        pos = int((ser == 1).sum())
        neg = int((ser == 0).sum())
        rows.append({"split": split_name, "total": total, "pos": pos, "neg": neg, "pos_pct": 100.0 * pos / total if total > 0 else 0.0})
    out = pd.DataFrame(rows)
    out.to_csv(output_dir / "class_distribution_summary.csv", index=False)
    logger.info("Saved class distribution summary to %s", output_dir / "class_distribution_summary.csv")


def parse_args():
    p = argparse.ArgumentParser(description="Inspect schedule_slippage_pct and create stratified splits")
    p.add_argument("--input-agg", "-i", required=True, help="Aggregated project-level CSV with schedule_slippage_pct")
    p.add_argument("--output-dir", "-o", default="data_splits", help="Directory to save splits and plots")
    p.add_argument("--threshold", "-t", type=float, default=None, help="Optional override threshold for schedule_slippage_pct")
    p.add_argument("--random-state", "-r", type=int, default=42, help="Random seed for splits")
    return p.parse_args()


def main():
    args = parse_args()
    input_path = Path(args.input_agg)
    outdir = Path(args.output_dir)

    df = load_agg(input_path)
    if "schedule_slippage_pct" not in df.columns:
        logger.error("Input file must contain 'schedule_slippage_pct' column")
        raise SystemExit(1)

    # 1) Inspect distribution and create plots
    report = inspect_distribution(df, "schedule_slippage_pct", outdir)

    # 2) Recommend threshold (unless overridden)
    if args.threshold is None:
        chosen = recommend_threshold(df, "schedule_slippage_pct")
    else:
        chosen = args.threshold
        logger.info("Using user-provided threshold: %s", chosen)

    # 3) Redefine target
    df = df.copy()
    df["will_delay"] = (pd.to_numeric(df["schedule_slippage_pct"], errors="coerce").fillna(0.0) > chosen).astype(int)
    counts = df["will_delay"].value_counts()
    logger.info("Post-labeling target counts: %s", counts.to_dict())
    if counts.nunique() == 1:
        logger.error("Target has only one class after thresholding. Abort.")
        raise SystemExit(2)

    # 4) Prepare ML-ready dataset
    X, y = prepare_ml_dataset(df, "will_delay")

    # 5) Create stratified splits
    splits = create_splits(X, y, random_state=args.random_state)

    # 6) Save outputs
    save_splits(splits, outdir)
    save_class_distribution_summary(splits, outdir)

    logger.info("All done. Recommended threshold used: %s", chosen)


if __name__ == "__main__":
    main()
