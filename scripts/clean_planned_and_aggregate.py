#!/usr/bin/env python3
"""
Clean a planned-end column, aggregate project-level schedule metrics,
compute schedule slippage, and save results.

Guardrails:
 - Discovery + aggregation only. Does NOT create ML splits or modify targets.
 - Fails if no positive slippage is found.

Outputs:
 - data_splits/project_level_aggregated_with_slippage.csv
 - data_splits/schedule_slippage_summary.csv

Usage example:
  python scripts/clean_planned_and_aggregate.py \
    --input project_dataset_v1_cleaned_with_will_delay.csv \
    --planned-col "Project Phase Planned End Date" \
    --actual-col "Project Phase Actual End Date" \
    --output data_splits/project_level_aggregated_with_slippage.csv
"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

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


def clean_parse_dates(series: pd.Series) -> pd.Series:
    """
    Attempt to parse a Series to datetimes safely. Non-parseable values become NaT.
    Returned series is of dtype datetime64[ns].
    """
    # Coerce to string first to avoid numeric epoch coercion
    parsed = pd.to_datetime(series.astype(str).str.strip(), errors="coerce")
    return parsed


def aggregate_project_level(df: pd.DataFrame, project_col: str, start_col: str, planned_col: str, actual_col: str) -> pd.DataFrame:
    # Parse date columns (only convert strings that parse; others become NaT)
    logger.info("Parsing dates: start=%s, planned=%s, actual=%s", start_col, planned_col, actual_col)
    start_dt = clean_parse_dates(df[start_col]) if start_col in df.columns else pd.Series(pd.NaT, index=df.index)
    planned_dt = clean_parse_dates(df[planned_col]) if planned_col in df.columns else pd.Series(pd.NaT, index=df.index)
    actual_dt = clean_parse_dates(df[actual_col]) if actual_col in df.columns else pd.Series(pd.NaT, index=df.index)

    df2 = df.copy()
    df2['_start_dt'] = start_dt
    df2['_planned_dt'] = planned_dt
    df2['_actual_dt'] = actual_dt

    # Aggregate per project
    agg = df2.groupby(project_col).agg(
        actual_start=('_start_dt', lambda s: s.min()),
        planned_end=('_planned_dt', lambda s: s.max()),
        actual_end=('_actual_dt', lambda s: s.max()),
    )

    # Compute durations (in days)
    agg['planned_duration_days'] = (agg['planned_end'] - agg['actual_start']).dt.days
    agg['elapsed_days'] = (agg['actual_end'] - agg['actual_start']).dt.days

    # slippage_from_planned = actual_end - planned_end (days)
    agg['slippage_days'] = (agg['actual_end'] - agg['planned_end']).dt.days

    # schedule_slippage_pct: slippage relative to planned duration when planned_duration>0
    agg['schedule_slippage_pct'] = np.where(
        agg['planned_duration_days'] > 0,
        agg['slippage_days'] / agg['planned_duration_days'],
        np.nan,
    )

    # also keep ratio of elapsed to planned (informational)
    agg['elapsed_over_planned'] = np.where(
        agg['planned_duration_days'] > 0,
        agg['elapsed_days'] / agg['planned_duration_days'],
        np.nan,
    )

    return agg.reset_index()


def summarize_and_save(agg: pd.DataFrame, output_csv: Path, summary_csv: Path) -> None:
    # Save aggregated project-level file
    agg.to_csv(output_csv, index=False)
    logger.info("Saved aggregated project-level file to %s", output_csv)

    # Compute summary stats for schedule_slippage_pct
    col = 'schedule_slippage_pct'
    series = pd.to_numeric(agg[col], errors='coerce')
    total = len(series.dropna())
    quantiles = series.quantile([0.0, 0.25, 0.5, 0.75, 0.9, 1.0]).to_dict()
    counts = {
        '>0.0': int((series > 0.0).sum()),
        '>0.01': int((series > 0.01).sum()),
        '>0.02': int((series > 0.02).sum()),
        '>0.05': int((series > 0.05).sum()),
    }
    summary = {
        'total_projects_with_valid_slippage': int(total),
        'quantiles': quantiles,
        'counts': counts,
    }
    # Save human-readable summary CSV
    rows = []
    for k, v in quantiles.items():
        rows.append({'stat': f'quantile_{k}', 'value': v})
    for k, v in counts.items():
        rows.append({'stat': k, 'value': v})
    pd.DataFrame(rows).to_csv(summary_csv, index=False)
    logger.info("Saved schedule slippage summary to %s", summary_csv)

    # Print summary to console
    logger.info("Schedule slippage quantiles: %s", quantiles)
    logger.info("Counts: %s", counts)

    # Fail loudly if no positive slippage found
    if counts['>0.0'] == 0:
        logger.error("No projects with schedule_slippage_pct > 0 found. Aborting for inspection.")
        raise SystemExit(2)


def parse_args():
    p = argparse.ArgumentParser(description='Clean planned dates and aggregate schedule slippage')
    p.add_argument('--input', '-i', required=True, help='Row-level cleaned CSV (with planned candidate column)')
    p.add_argument('--planned-col', default='Project Phase Planned End Date', help='Planned end date candidate column')
    p.add_argument('--actual-col', default='Project Phase Actual End Date', help='Actual end date column')
    p.add_argument('--start-col', default='Project Phase Actual Start Date', help='Actual start date column')
    p.add_argument('--output', '-o', default='data_splits/project_level_aggregated_with_slippage.csv', help='Output CSV for aggregated projects')
    p.add_argument('--summary', default='data_splits/schedule_slippage_summary.csv', help='CSV summary of slippage stats')
    return p.parse_args()


def main():
    args = parse_args()
    infile = Path(args.input)
    out_csv = Path(args.output)
    summary_csv = Path(args.summary)

    if not infile.exists():
        logger.error('Input file not found: %s', infile)
        raise SystemExit(1)

    df = pd.read_csv(infile, low_memory=False)
    proj_col = detect_project_id_column(df)
    if not proj_col:
        logger.error('Could not detect project id column in input')
        raise SystemExit(1)
    logger.info('Using project id column: %s', proj_col)

    # Ensure candidate columns exist
    for c in (args.planned_col, args.actual_col, args.start_col):
        if c not in df.columns:
            logger.warning('Column %s not found in input; proceeding but values will be NaT where missing', c)

    agg = aggregate_project_level(df, proj_col, args.start_col, args.planned_col, args.actual_col)

    # Standardize planned_end to ISO where present
    if 'planned_end' in agg.columns:
        agg['planned_end_iso'] = pd.to_datetime(agg['planned_end'], errors='coerce').dt.date.astype('object')

    summarize_and_save(agg, out_csv, summary_csv)


if __name__ == '__main__':
    main()
