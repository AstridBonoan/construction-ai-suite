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
    id_keywords = {
        "project_id",
        "project id",
        "proj_id",
        "id",
        "source_file",
        "source",
        "projectid",
    }
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
    to_drop = [
        c for i, c in enumerate(to_drop) if c in df.columns and to_drop.index(c) == i
    ]
    return to_drop


def redefine_target_and_split(
    input_csv: Path, output_dir: Path, random_state: int = 42
) -> None:
    # Load deduplicated project-level dataset
    df = pd.read_csv(input_csv, low_memory=False)
    logger.info(
        "Loaded deduped project dataset: rows=%d, cols=%d", len(df), df.shape[1]
    )

    # Ensure schedule_slippage_pct exists or compute if possible
    # If schedule_slippage_pct missing, try to compute it from available date columns.
    if "schedule_slippage_pct" not in df.columns:
        logger.info(
            "Column 'schedule_slippage_pct' not found — attempting to compute from date columns."
        )
        # Look for date columns
        import re

        # Prefer columns that explicitly include the word 'date' to avoid numeric/cost fields
        start_candidates = [
            c
            for c in df.columns
            if "start" in c.lower()
            and "date" in c.lower()
            and ("actual" in c.lower() or "phase" in c.lower())
        ]
        planned_candidates = [
            c
            for c in df.columns
            if "planned" in c.lower() and "end" in c.lower() and "date" in c.lower()
        ]
        actual_candidates = [
            c
            for c in df.columns
            if "actual" in c.lower() and "end" in c.lower() and "date" in c.lower()
        ]

        # Fallback: token-based matching but exclude obvious numeric/cost columns
        if not (start_candidates and planned_candidates and actual_candidates):
            start_candidates = start_candidates or []
            planned_candidates = planned_candidates or []
            actual_candidates = actual_candidates or []
            exclude_keywords = {
                "amount",
                "cost",
                "amt",
                "price",
                "budget",
                "value",
                "total",
            }
            for c in df.columns:
                lc = c.lower()
                if any(k in lc for k in exclude_keywords):
                    continue
                tokens = re.findall(r"\w+", lc)
                if "start" in tokens and ("actual" in tokens or "phase" in tokens):
                    if c not in start_candidates:
                        start_candidates.append(c)
                if "planned" in tokens and "end" in tokens:
                    if c not in planned_candidates:
                        planned_candidates.append(c)
                if "actual" in tokens and "end" in tokens:
                    if c not in actual_candidates:
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
            logger.info(
                "Using date columns: start=%s, planned_end=%s, actual_end=%s to compute schedule_slippage_pct",
                start_col,
                planned_col,
                actual_col,
            )
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
            logger.error(
                "Required date columns not found to compute schedule_slippage_pct. Need start/planned_end/actual_end."
            )
            raise SystemExit(1)

    # Coerce to numeric, fill NaN with 0 (assumption: missing implies no slippage)
    df["schedule_slippage_pct"] = pd.to_numeric(
        df["schedule_slippage_pct"], errors="coerce"
    ).fillna(0.0)

    # Redefine target: will_delay = 1 if schedule_slippage_pct > 0.05 else 0
    df["will_delay"] = (df["schedule_slippage_pct"] > 0.05).astype(int)

    # Also compute planned/elapsed/delay numeric fields if we computed schedule_slippage above
    try:
        # If we computed planned_dur and elapsed in the computation block above, assign them back
        if "planned_dur" in locals() and "elapsed" in locals():
            df["planned_duration_days"] = planned_dur
            df["elapsed_days"] = elapsed
            df["delay_days"] = elapsed - planned_dur
    except Exception:
        pass

    # If delay_days not present but numeric columns exist, compute it
    if (
        "delay_days" not in df.columns
        and "planned_duration_days" in df.columns
        and "elapsed_days" in df.columns
    ):
        try:
            df["delay_days"] = pd.to_numeric(
                df["elapsed_days"], errors="coerce"
            ) - pd.to_numeric(df["planned_duration_days"], errors="coerce")
        except Exception:
            df["delay_days"] = pd.Series([pd.NA] * len(df))

    # New label: absolute-delay over 30 days
    df["will_delay_abs30"] = (
        pd.to_numeric(df.get("delay_days", pd.Series()), errors="coerce") > 30
    ).astype(int)

    # Validate main target (will_delay) but don't abort pipeline if no positives — warn only
    counts = df["will_delay"].value_counts(dropna=False).to_dict()
    total = len(df)
    pos = int(counts.get(1, 0))
    neg = int(counts.get(0, 0))
    pos_pct = pos / total * 100 if total > 0 else 0.0
    logger.info(
        "Target distribution: total=%d, will_delay positives=%d (%.2f%%), negatives=%d",
        total,
        pos,
        pos_pct,
        neg,
    )
    if pos == 0:
        logger.warning(
            "No positive samples found for `will_delay`. Continuing — alternative label `will_delay_abs30` has been created."
        )
    if pos_pct < 5.0 and pos > 0:
        logger.warning(
            "Severe class imbalance: only %.2f%% positive samples (<5%%).", pos_pct
        )

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
    # If y is single-class, fall back to unstratified splits
    stratify_arg = y if y.nunique() > 1 else None
    if stratify_arg is None:
        logger.warning(
            "Will perform unstratified splits because `will_delay` is single-class."
        )

    # split out test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify_arg
    )
    # split train/val from remaining
    val_frac = 0.15 / (1.0 - test_size)  # fraction of remaining
    stratify_val = y_train_val if y_train_val.nunique() > 1 else None
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=val_frac,
        random_state=random_state,
        stratify=stratify_val,
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

    # Also save absolute-30-day label files aligned to train/test indices
    y_abs30 = df["will_delay_abs30"]
    # Align by index
    y_train_abs30 = y_abs30.loc[X_train.index]
    y_test_abs30 = y_abs30.loc[X_test.index]
    y_train_abs30.to_csv(
        output_dir / "y_train_abs30.csv", index=False, header=["will_delay_abs30"]
    )
    y_test_abs30.to_csv(
        output_dir / "y_test_abs30.csv", index=False, header=["will_delay_abs30"]
    )

    # Save updated aggregated file copy with labels for record
    agg_out = output_dir / Path(input_csv).name.replace(".csv", "_with_labels.csv")
    df.to_csv(agg_out, index=False)

    # Write diagnostics for abs30 label
    diag_lines = []
    diag_lines.append(f"total_projects={len(df)}")
    diag_lines.append(
        f"planned_duration_days_non_na={int(pd.to_numeric(df.get('planned_duration_days', pd.Series()), errors='coerce').notna().sum())}"
    )
    diag_lines.append(
        f"elapsed_days_non_na={int(pd.to_numeric(df.get('elapsed_days', pd.Series()), errors='coerce').notna().sum())}"
    )
    diag_lines.append(
        f"delay_days_non_na={int(pd.to_numeric(df.get('delay_days', pd.Series()), errors='coerce').notna().sum())}"
    )
    diag_lines.append(
        f"will_delay_abs30_positives={int(pd.to_numeric(df['will_delay_abs30'], errors='coerce').sum())}"
    )
    with open(output_dir / "diagnostics_abs30.txt", "w") as fh:
        fh.write("\n".join(diag_lines))

    logger.info("Saved splits and abs30 diagnostics to %s", output_dir)


def parse_args():
    p = argparse.ArgumentParser(
        description="Redefine will_delay and create stratified splits"
    )
    p.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input deduped project CSV (project_level_deduped_with_target.csv)",
    )
    p.add_argument(
        "--output-dir", "-o", default="data_splits", help="Output directory for splits"
    )
    p.add_argument(
        "--random-state",
        "-r",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    redefine_target_and_split(
        Path(args.input), Path(args.output_dir), random_state=args.random_state
    )
