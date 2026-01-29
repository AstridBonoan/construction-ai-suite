#!/usr/bin/env python3
"""
Discovery-only script to find candidate planned/scheduled end-date columns.

Outputs:
 - data_splits/planned_date_candidate_diagnostics.csv

Strict guardrails: this script does NOT modify targets, aggregate, or create splits.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import logging
from typing import List

import pandas as pd
from pandas.api import types as ptypes

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


EXCLUDE_TOKENS = {"cost", "amount", "budget", "value", "usd", "price", "spend", "expend", "qty"}
PLANNED_TOKENS = ("plan", "planned", "schedule", "scheduled", "target", "due")


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


def find_candidates(df: pd.DataFrame) -> List[str]:
    candidates = []
    for c in df.columns:
        lc = c.lower()
        if any(tok in lc for tok in PLANNED_TOKENS) and not any(ex in lc for ex in EXCLUDE_TOKENS):
            # exclude numeric-only columns
            if ptypes.is_numeric_dtype(df[c].dtype):
                continue
            candidates.append(c)
    return candidates


def analyze_candidate(df: pd.DataFrame, col: str, actual_cols: List[str]) -> dict:
    s = df[col]
    non_null_mask = s.notna() & (s.astype(str).str.strip() != "")
    non_null_count = int(non_null_mask.sum())
    total = len(df)
    non_null_pct = 100.0 * non_null_count / total if total > 0 else 0.0

    inferred_dtype = str(s.dtype)

    # attempt safe datetime parsing
    parsed = pd.to_datetime(s, errors="coerce")
    parsed_count = int(parsed.notna().sum())
    parsed_pct = 100.0 * parsed_count / total if total > 0 else 0.0

    parsed_min = parsed.min() if parsed_count > 0 else pd.NaT
    parsed_max = parsed.max() if parsed_count > 0 else pd.NaT

    # sample first 20 non-null raw values for human inspection
    examples = s[non_null_mask].astype(str).head(20).tolist()

    # cross-check vs actual date columns if any
    precedence_info = {}
    if parsed_count > 0 and actual_cols:
        # pick first actual col that parses as date
        for a in actual_cols:
            a_parsed = pd.to_datetime(df[a], errors="coerce")
            common_mask = parsed.notna() & a_parsed.notna()
            if common_mask.any():
                # fraction where planned <= actual
                precede_frac = float((parsed[common_mask] <= a_parsed[common_mask]).mean())
                # median lead (actual - planned) in days
                lead_days = (a_parsed[common_mask] - parsed[common_mask]).dt.days.median()
                precedence_info[a] = {"precede_frac": precede_frac, "median_lead_days": int(lead_days) if pd.notna(lead_days) else None}

    return {
        "column": col,
        "non_null_count": non_null_count,
        "non_null_pct": non_null_pct,
        "inferred_dtype": inferred_dtype,
        "parsed_count": parsed_count,
        "parsed_pct": parsed_pct,
        "parsed_min": str(parsed_min) if parsed_count > 0 else "",
        "parsed_max": str(parsed_max) if parsed_count > 0 else "",
        "examples": examples,
        "precedence_info": precedence_info,
    }


def find_actual_end_candidates(df: pd.DataFrame) -> List[str]:
    actuals = []
    for c in df.columns:
        lc = c.lower()
        if "actual" in lc and "end" in lc:
            actuals.append(c)
    # fallback: any column containing 'actual' or 'end' that isn't numeric-only cost
    if not actuals:
        for c in df.columns:
            lc = c.lower()
            if ("actual" in lc or "end" in lc) and not any(ex in lc for ex in EXCLUDE_TOKENS):
                if not ptypes.is_numeric_dtype(df[c].dtype):
                    actuals.append(c)
    return actuals


def main():
    p = argparse.ArgumentParser(description="Diagnose planned/scheduled end-date candidate columns")
    p.add_argument("--input", "-i", default="project_dataset_v1_cleaned_with_will_delay.csv", help="Row-level cleaned CSV path")
    p.add_argument("--output-dir", "-o", default="data_splits", help="Directory to save summary CSV")
    args = p.parse_args()

    infile = Path(args.input)
    outdir = Path(args.output_dir)
    if not infile.exists():
        logger.error("Input file not found: %s", infile)
        raise SystemExit(1)

    df = pd.read_csv(infile, low_memory=False)

    proj_col = detect_project_id_column(df)
    logger.info("Detected project id column: %s", proj_col)

    candidates = find_candidates(df)
    logger.info("Found %d planned-date candidate columns", len(candidates))

    actual_candidates = find_actual_end_candidates(df)
    logger.info("Found %d actual-end candidate columns: %s", len(actual_candidates), actual_candidates[:5])

    results = []
    for c in candidates:
        res = analyze_candidate(df, c, actual_candidates)
        results.append(res)
        # print concise info for human
        logger.info("Column: %s — non-null %d (%.2f%%), parsed %d (%.2f%%)\n  parsed range: %s to %s\n  examples: %s\n",
                    res["column"], res["non_null_count"], res["non_null_pct"], res["parsed_count"], res["parsed_pct"],
                    res["parsed_min"], res["parsed_max"], json.dumps(res["examples"]))
        if res["precedence_info"]:
            logger.info("  Precedence vs actuals: %s", json.dumps(res["precedence_info"]))

    # Save CSV summary
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in results:
        rows.append({
            "column": r["column"],
            "non_null_count": r["non_null_count"],
            "non_null_pct": r["non_null_pct"],
            "inferred_dtype": r["inferred_dtype"],
            "parsed_count": r["parsed_count"],
            "parsed_pct": r["parsed_pct"],
            "parsed_min": r["parsed_min"],
            "parsed_max": r["parsed_max"],
            "precedence_info": json.dumps(r["precedence_info"]),
            "examples": json.dumps(r["examples"]),
        })
    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(outdir / "planned_date_candidate_diagnostics.csv", index=False)
    logger.info("Saved diagnostics to %s", outdir / "planned_date_candidate_diagnostics.csv")

    # Ranked recommendation: prefer high parsed_pct and high precede_frac
    ranked = []
    for r in results:
        parsed_score = r["parsed_pct"]
        precede_score = 0.0
        for a, info in r["precedence_info"].items():
            precede_score = max(precede_score, info.get("precede_frac", 0.0))
        ranked.append((r["column"], parsed_score, precede_score))
    ranked.sort(key=lambda x: (x[1], x[2]), reverse=True)

    if ranked:
        logger.info("\nRanked recommended planned-end candidates (column, parsed_pct, max_precede_frac):")
        for col, pscore, frac in ranked:
            logger.info(" - %s : parsed_pct=%.2f%%, max_precede_frac=%.2f", col, pscore, frac)
        best = ranked[0]
        logger.info("\nBest candidate: %s (parsed_pct=%.2f%%, precede_frac=%.2f)", best[0], best[1], best[2])
    else:
        logger.info("No planned-date candidates detected by token heuristics.")


if __name__ == "__main__":
    main()
