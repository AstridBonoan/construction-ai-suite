"""
Redefine `will_delay` by risk threshold and create stratified train/val/test splits.

- Loads `project_level_deduped_with_target.csv` from working directory.
- Redefines `will_delay = 1` where `schedule_slippage_pct > 0.05`, else 0.
- Validates class distribution and warns if positives < 5%.
- Drops ID and date columns from features and creates stratified splits (70/15/15).
- Saves: X_train.csv, y_train.csv, X_val.csv, y_val.csv, X_test.csv, y_test.csv in `data_splits/`.

Run:
/your/python/path python scripts/redefine_target_and_split.py --input data_splits/project_level_deduped_with_target.csv --output-dir data_splits --random-state 42

"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def detect_project_id_column(df: pd.DataFrame) -> str | None:
    for c in df.columns:
        lc = c.lower()
        if lc in ("project_id", "project id", "proj_id", "id"):
            return c
    for c in df.columns:
        lc = c.lower()
        if "project" in lc and "id" in lc:
            return c
    return None


def drop_id_and_date_columns(df: pd.DataFrame, project_id_col: str | None) -> List[str]:
    """Return list of columns to drop (IDs and date-like columns)."""
    to_drop = []
    # project id and common id names
    id_keywords = {"project_id", "project id", "proj_id", "id", "source_file", "source", "projectid"}
    for c in df.columns:
        lc = c.lower()
        if project_id_col and c == project_id_col:
            to_drop.append(c)
            continue
        if lc in id_keywords:
            to_drop.append(c)
            continue
        # date-like
        if any(k in lc for k in ("date", "planned", "actual", "start", "end")):
            to_drop.append(c)
    # make unique and keep only existing
    to_drop = [c for i, c in enumerate(to_drop) if c in df.columns and to_drop.index(c) == i]
    return to_drop


def redefine_target_and_split(input_csv: Path, output_dir: Path, random_state: int = 42) -> None:
    # Load deduplicated project-level dataset
    df = pd.read_csv(input_csv, low_memory=False)
    logger.info("Loaded deduped project dataset: rows=%d, cols=%d", len(df), df.shape[1])

    # Ensure schedule_slippage_pct exists or compute if possible
    # If schedule_slippage_pct missing, try to compute it from available date columns.
    if "schedule_slippage_pct" not in df.columns:
        logger.info("Column 'schedule_slippage_pct' not found — attempting to compute from date columns.")
        # Look for date columns
        import re
        start_candidates = []
        planned_candidates = []
        actual_candidates = []
        for c in df.columns:
            lc = c.lower()
            tokens = re.findall(r"\w+", lc)
            if "start" in tokens and ("actual" in tokens or "phase" in tokens):
                start_candidates.append(c)
            if "planned" in tokens and "end" in tokens:
                planned_candidates.append(c)
            if "actual" in tokens and "end" in tokens:
                actual_candidates.append(c)

        # From candidates, choose the column that parses best as dates (max non-null datetime values)
        def best_date_candidate(candidates):
            best = None
            best_count = -1
            for c in candidates:
                parsed = pd.to_datetime(df[c], errors="coerce")
                cnt = parsed.notna().sum()
                if cnt > best_count:
                    best_count = cnt
                    best = c
            return best if best_count > 0 else None

        start_col = best_date_candidate(start_candidates)
        planned_col = best_date_candidate(planned_candidates)
        actual_col = best_date_candidate(actual_candidates)

        if start_col and planned_col and actual_col:
            logger.info("Using date columns: start=%s, planned_end=%s, actual_end=%s to compute schedule_slippage_pct", start_col, planned_col, actual_col)
            # Parse dates
            s = pd.to_datetime(df[start_col], errors="coerce")
            p = pd.to_datetime(df[planned_col], errors="coerce")
            a = pd.to_datetime(df[actual_col], errors="coerce")
            # planned duration: planned_end - start (days)
            planned_dur = (p - s).dt.days
            # elapsed: actual_end - start (days)
            elapsed = (a - s).dt.days
            # Avoid division by zero: replace non-positive planned durations with NaN
            planned_dur_safe = planned_dur.where(planned_dur > 0)
            schedule_slip = elapsed / planned_dur_safe
            # where computation not possible, set 0
            df["schedule_slippage_pct"] = schedule_slip.fillna(0.0)
        else:
            logger.error("Required date columns not found to compute schedule_slippage_pct. Need start/planned_end/actual_end.")
            raise SystemExit(1)

    # Coerce to numeric, fill NaN with 0 (assumption: missing implies no slippage)
    df["schedule_slippage_pct"] = pd.to_numeric(df["schedule_slippage_pct"], errors="coerce").fillna(0.0)

    # Redefine target: will_delay = 1 if schedule_slippage_pct > 0.05 else 0
    df["will_delay"] = (df["schedule_slippage_pct"] > 0.05).astype(int)

    # Validate target
    counts = df["will_delay"].value_counts(dropna=False).to_dict()
    total = len(df)
    pos = int(counts.get(1, 0))
    neg = int(counts.get(0, 0))
    pos_pct = pos / total * 100 if total > 0 else 0.0
    logger.info("Target distribution: total=%d, positives=%d (%.2f%%), negatives=%d", total, pos, pos_pct, neg)
    if pos == 0:
        logger.error("No positive samples found after redefining target. Aborting.")
        raise SystemExit(2)
    if pos_pct < 5.0:
        logger.warning("Severe class imbalance: only %.2f%% positive samples (<5%%).", pos_pct)

    # Prepare features: drop target, IDs, and date-like columns
    project_id_col = detect_project_id_column(df)
    drop_cols = drop_id_and_date_columns(df, project_id_col)
    if "will_delay" in drop_cols:
        drop_cols = [c for c in drop_cols if c != "will_delay"]
    logger.info("Dropping %d columns (IDs/dates) from features", len(drop_cols))

    X = df.drop(columns=drop_cols + ["will_delay"], errors="ignore")
    y = df["will_delay"].astype(int)

    # Ensure no missing values in target
    if y.isna().any():
        logger.error("Missing values found in target after processing. Aborting.")
        raise SystemExit(3)

    # Stratified splits: test 15%, val 15%, train 70%
    test_size = 0.15
    # split out test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    # split train/val from remaining
    val_frac = 0.15 / (1.0 - test_size)  # fraction of remaining
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=val_frac, random_state=random_state, stratify=y_train_val
    )

    # Output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save splits
    X_train.to_csv(output_dir / "X_train.csv", index=False)
    y_train.to_csv(output_dir / "y_train.csv", index=False)
    X_val.to_csv(output_dir / "X_val.csv", index=False)
    y_val.to_csv(output_dir / "y_val.csv", index=False)
    X_test.to_csv(output_dir / "X_test.csv", index=False)
    y_test.to_csv(output_dir / "y_test.csv", index=False)

    logger.info("Saved splits to %s", output_dir)


def parse_args():
    p = argparse.ArgumentParser(description="Redefine will_delay and create stratified splits")
    p.add_argument("--input", "-i", required=True, help="Input deduped project CSV (project_level_deduped_with_target.csv)")
    p.add_argument("--output-dir", "-o", default="data_splits", help="Output directory for splits")
    p.add_argument("--random-state", "-r", type=int, default=42, help="Random seed for reproducibility")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    redefine_target_and_split(Path(args.input), Path(args.output_dir), random_state=args.random_state)
