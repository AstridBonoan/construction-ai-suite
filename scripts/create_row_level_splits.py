#!/usr/bin/env python3
"""
Create stratified row-level train/val/test splits on `will_delay`.

Behavior:
- Reads `project_dataset_v1_cleaned_with_will_delay.csv` (row-level file)
- Splits stratified on `will_delay`: 70% train, 15% val, 15% test
- Saves CSVs: `data_splits/X_train.csv`, `data_splits/y_train.csv`, etc.
- Writes `data_splits/row_level_split_summary.csv` with counts and positive % per split

Guardrails:
- Does NOT train any model.
- Fails loudly if `will_delay` is missing or stratification not possible.

Usage:
  python scripts/create_row_level_splits.py --input project_dataset_v1_cleaned_with_will_delay.csv --output-dir data_splits --random-state 42
"""

from __future__ import annotations
import argparse
from pathlib import Path
import logging

import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def parse_args():
    p = argparse.ArgumentParser(
        description="Create stratified row-level splits on will_delay"
    )
    p.add_argument(
        "--input",
        "-i",
        default="project_dataset_v1_cleaned_with_will_delay.csv",
        help="Row-level cleaned CSV with will_delay column",
    )
    p.add_argument(
        "--output-dir", "-o", default="data_splits", help="Directory to save splits"
    )
    p.add_argument("--random-state", "-r", type=int, default=42)
    return p.parse_args()


def main():
    args = parse_args()
    infile = Path(args.input)
    outdir = Path(args.output_dir)
    if not infile.exists():
        logger.error("Input file not found: %s", infile)
        raise SystemExit(1)

    df = pd.read_csv(infile, low_memory=False)

    if "will_delay" not in df.columns:
        logger.error("Column 'will_delay' not found in %s", infile)
        raise SystemExit(1)

    # Basic sanity counts
    total = len(df)
    pos_total = int((df["will_delay"] == 1).sum())
    logger.info(
        "Total rows: %d, positives (will_delay=1): %d (%.2f%%)",
        total,
        pos_total,
        100.0 * pos_total / total if total > 0 else 0.0,
    )

    # Features X: all columns except the target
    X = df.drop(columns=["will_delay"], errors="ignore")
    y = df["will_delay"].astype(int)

    # First split: hold out test set (15%) stratified on y
    test_size = 0.15
    try:
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=args.random_state, stratify=y
        )
    except ValueError as exc:
        logger.error("Stratified split failed: %s", exc)
        raise

    # Second split: split train_val into train (70%) and val (15%).
    # val fraction relative to train_val is val_frac = 0.15 / (1 - test_size)
    val_frac = 0.15 / (1.0 - test_size)
    try:
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val,
            y_train_val,
            test_size=val_frac,
            random_state=args.random_state,
            stratify=y_train_val,
        )
    except ValueError as exc:
        logger.error("Stratified train/val split failed: %s", exc)
        raise

    # Ensure output dir
    outdir.mkdir(parents=True, exist_ok=True)

    # Save splits
    X_train.to_csv(outdir / "X_train.csv", index=False)
    y_train.to_csv(outdir / "y_train.csv", index=False)
    X_val.to_csv(outdir / "X_val.csv", index=False)
    y_val.to_csv(outdir / "y_val.csv", index=False)
    X_test.to_csv(outdir / "X_test.csv", index=False)
    y_test.to_csv(outdir / "y_test.csv", index=False)

    # Summary report
    def summarize(ser):
        total = len(ser)
        pos = int((ser == 1).sum())
        pct = 100.0 * pos / total if total > 0 else 0.0
        return total, pos, pct

    rows = []
    for name, ser in [("train", y_train), ("val", y_val), ("test", y_test)]:
        total_n, pos_n, pos_pct = summarize(ser)
        rows.append({"split": name, "total": total_n, "pos": pos_n, "pos_pct": pos_pct})
        logger.info(
            "Split %s: total=%d, positives=%d (%.2f%%)", name, total_n, pos_n, pos_pct
        )

    pd.DataFrame(rows).to_csv(outdir / "row_level_split_summary.csv", index=False)
    logger.info("Saved split CSVs and summary to %s", outdir)

    # Sanity check: confirm positives exist in each split
    for r in rows:
        if r["pos"] == 0:
            logger.error(
                "No positive samples in split %s — stratification failed or dataset too imbalanced",
                r["split"],
            )
            raise SystemExit(2)


if __name__ == "__main__":
    main()
