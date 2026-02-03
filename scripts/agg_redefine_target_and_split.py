"""
Aggregate row-level project data to project-level schedule metrics, redefine `will_delay`,
and create stratified train/val/test splits.

Input: `project_dataset_v1_cleaned_with_will_delay.csv` (row-level with date columns)
Output: saved splits in `data_splits/`

Definition:
- For each project, compute:
  - actual_start = min(Project Phase Actual Start Date)
  - planned_end = max(Project Phase Planned End Date)
  - actual_end = max(Project Phase Actual End Date)
    - planned_duration = (planned_end - actual_start).days
    - elapsed_days = (actual_end - actual_start).days
    - schedule_slippage_pct = (elapsed_days - planned_duration) / planned_duration
        (i.e., fraction of overrun relative to planned duration; if planned_duration<=0, set 0)
- will_delay = 1 if schedule_slippage_pct > 0.05 else 0

Saves stratified splits to `data_splits/`.
"""

from __future__ import annotations
import argparse
import logging
from pathlib import Path

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


def parse_date_column_candidates(df: pd.DataFrame):
    """Identify start, planned_end, actual_end columns by token and parseability."""
    import re

    candidates = {"start": [], "planned_end": [], "actual_end": []}
    for c in df.columns:
        lc = c.lower()
        tokens = re.findall(r"\w+", lc)
        if "start" in tokens and ("phase" in tokens or "actual" in tokens):
            candidates["start"].append(c)
        if "planned" in tokens and "end" in tokens:
            candidates["planned_end"].append(c)
        if "actual" in tokens and "end" in tokens:
            candidates["actual_end"].append(c)

    # choose best candidate by how many values parse as dates
    def best(cands):
        best_c = None
        best_score = (-1, -1)
        date_regex = r"\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}"
        from pandas.api import types as ptypes

        for c in cands:
            # if column is numeric, skip parsed_count since pd.to_datetime
            # will coerce numeric values to timestamps (epoch-based) producing
            # many false positives; only consider textual/date-like columns.
            if ptypes.is_numeric_dtype(df[c].dtype):
                date_like = 0
                parsed_count = 0
            else:
                series = df[c].astype(str)
                # count strings that look like dates (e.g., 7/31/2025 or 2025-07-31)
                date_like = series.str.contains(date_regex, regex=True, na=False).sum()
                # also check parseable datetimes
                parsed = pd.to_datetime(df[c], errors="coerce")
                parsed_count = parsed.notna().sum()
            # score gives priority to textual date-like matches, then parsed_count
            score = (date_like, parsed_count)
            if score > best_score:
                best_score = score
                best_c = c
        # return None if no candidate had any positive score
        return best_c if best_score != (-1, -1) else None

    return (
        best(candidates["start"]),
        best(candidates["planned_end"]),
        best(candidates["actual_end"]),
    )


def aggregate_project_level(
    df: pd.DataFrame,
    project_col: str,
    start_col: str,
    planned_col: str,
    actual_col: str,
) -> pd.DataFrame:
    # parse dates
    start_dt = pd.to_datetime(df[start_col], errors="coerce")
    planned_dt = pd.to_datetime(df[planned_col], errors="coerce")
    actual_dt = pd.to_datetime(df[actual_col], errors="coerce")

    df2 = df.copy()
    df2["_start_dt"] = start_dt
    df2["_planned_dt"] = planned_dt
    df2["_actual_dt"] = actual_dt

    # aggregate per project
    # Build aggregation dict: date aggregates plus carry-forward for non-date columns
    agg_dict = {
        "actual_start": ("_start_dt", lambda s: s.min()),
        "planned_end": ("_planned_dt", lambda s: s.max()),
        "actual_end": ("_actual_dt", lambda s: s.max()),
    }
    # For non-date, non-project columns, carry forward the first non-null value per project
    non_date_cols = [
        c
        for c in df.columns
        if c not in (project_col, start_col, planned_col, actual_col)
    ]
    for c in non_date_cols:
        # use a lambda that returns first non-null or NaN
        agg_dict[c] = (
            c,
            lambda s: s.dropna().iloc[0] if s.dropna().shape[0] > 0 else pd.NA,
        )

    agg = df2.groupby(project_col).agg(**agg_dict)
    # compute durations
    agg["planned_duration_days"] = (agg["planned_end"] - agg["actual_start"]).dt.days
    agg["elapsed_days"] = (agg["actual_end"] - agg["actual_start"]).dt.days
    # compute schedule_slippage_pct
    # slippage: fraction of delay relative to planned duration
    # (elapsed - planned) / planned  => positive when actual took longer than planned
    agg["schedule_slippage_pct"] = np.where(
        agg["planned_duration_days"] > 0,
        (agg["elapsed_days"] - agg["planned_duration_days"])
        / agg["planned_duration_days"],
        0.0,
    )
    return agg.reset_index()


def build_features_from_row_level(row_csv: Path, output_csv: Path) -> pd.DataFrame:
    # load row-level cleaned dataset
    df = pd.read_csv(row_csv, low_memory=False)
    project_col = detect_project_id_column(df)
    if not project_col:
        logger.error("No project id column found in row-level dataset")
        raise SystemExit(1)
    start_col, planned_col, actual_col = parse_date_column_candidates(df)
    if not (start_col and planned_col and actual_col):
        logger.error(
            "Could not detect suitable date columns for aggregation. start=%s planned=%s actual=%s",
            start_col,
            planned_col,
            actual_col,
        )
        raise SystemExit(1)
    logger.info(
        "Aggregating using columns: start=%s, planned_end=%s, actual_end=%s",
        start_col,
        planned_col,
        actual_col,
    )
    agg = aggregate_project_level(df, project_col, start_col, planned_col, actual_col)

    # Save aggregated project-level dataframe with schedule_slippage_pct
    agg.to_csv(output_csv, index=False)
    logger.info("Saved aggregated project-level file to %s", output_csv)
    return agg


def redefine_target_from_agg(
    agg: pd.DataFrame, threshold: float = 0.05
) -> pd.DataFrame:
    agg = agg.copy()
    agg["schedule_slippage_pct"] = pd.to_numeric(
        agg["schedule_slippage_pct"], errors="coerce"
    ).fillna(0.0)
    agg["will_delay"] = (agg["schedule_slippage_pct"] > threshold).astype(int)
    return agg


def create_splits_and_save(
    df_proj: pd.DataFrame, output_dir: Path, random_state: int = 42
) -> None:
    # Validate target
    counts = df_proj["will_delay"].value_counts(dropna=False).to_dict()
    total = len(df_proj)
    pos = int(counts.get(1, 0))
    pos_pct = pos / total * 100 if total > 0 else 0.0
    logger.info(
        "Project-level target: total=%d positives=%d (%.2f%%)", total, pos, pos_pct
    )
    if pos == 0:
        logger.error("No positive samples in the project-level target. Aborting.")
        raise SystemExit(2)
    if pos_pct < 5.0:
        logger.warning("Severe imbalance: positives = %.2f%% (<5%%)", pos_pct)

    # Features: drop IDs and date columns (keep schedule_slippage_pct and durations)
    project_col = detect_project_id_column(df_proj)
    drop_cols = []
    if project_col:
        drop_cols.append(project_col)
    # drop any columns with 'date' or obvious id tokens
    drop_cols += [
        c
        for c in df_proj.columns
        if any(k in c.lower() for k in ("date", "start", "end"))
        and c not in ("schedule_slippage_pct", "planned_duration_days", "elapsed_days")
    ]
    X = df_proj.drop(columns=drop_cols + ["will_delay"], errors="ignore")
    y = df_proj["will_delay"].astype(int)

    # Stratified splits where possible; fall back to random splits if class counts are too small
    test_size = 0.15
    try:
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        val_frac = 0.15 / (1.0 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val,
            y_train_val,
            test_size=val_frac,
            random_state=random_state,
            stratify=y_train_val,
        )
    except ValueError:
        logger.warning(
            "Stratified split failed due to extreme class imbalance; falling back to random splits without stratification."
        )
        X_train_val, X_test, y_train_val, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, shuffle=True
        )
        val_frac = 0.15 / (1.0 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_val,
            y_train_val,
            test_size=val_frac,
            random_state=random_state,
            shuffle=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(output_dir / "X_train.csv", index=False)
    y_train.to_csv(output_dir / "y_train.csv", index=False)
    X_val.to_csv(output_dir / "X_val.csv", index=False)
    y_val.to_csv(output_dir / "y_val.csv", index=False)
    X_test.to_csv(output_dir / "X_test.csv", index=False)
    y_test.to_csv(output_dir / "y_test.csv", index=False)
    logger.info("Saved stratified splits to %s", output_dir)


def parse_args():
    p = argparse.ArgumentParser(
        description="Aggregate row-level project data, redefine will_delay, and create splits"
    )
    p.add_argument(
        "--input-rows",
        "-i",
        required=True,
        help="Row-level cleaned CSV (project_dataset_v1_cleaned_with_will_delay.csv)",
    )
    p.add_argument(
        "--output-agg",
        "-a",
        default="data_splits/project_level_aggregated.csv",
        help="Path to save aggregated project-level CSV",
    )
    p.add_argument(
        "--output-dir", "-o", default="data_splits", help="Directory to save splits"
    )
    p.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=0.05,
        help="Threshold for schedule_slippage_pct to label will_delay",
    )
    p.add_argument("--random-state", "-r", type=int, default=42, help="Random seed")
    return p.parse_args()


def main():
    args = parse_args()
    input_rows = Path(args.input_rows)
    output_agg = Path(args.output_agg)
    output_dir = Path(args.output_dir)

    agg = build_features_from_row_level(input_rows, output_agg)
    agg_td = redefine_target_from_agg(agg, threshold=args.threshold)
    create_splits_and_save(agg_td, output_dir, random_state=args.random_state)


if __name__ == "__main__":
    main()
