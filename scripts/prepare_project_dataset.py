"""
prepare_project_dataset.py

Modular, production-ready data preparation script for construction project datasets.
Features:
- Load multiple CSV/JSON files into a single DataFrame
- Standardize numeric units (days, dollars, counts, percentages)
- Normalize categorical columns
- Handle missing values (mean/median for numeric, 'Unknown' for categorical)
- Track synthetic rows via filename keywords
- Compute derived variables
- Validate dataset (duplicates, outliers)
- Save cleaned dataset to CSV

Usage (example):
python scripts/prepare_project_dataset.py --input-dir ./construction_datasets --output project_dataset_v1_cleaned.csv

"""

from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

# ----------------------------- Configuration ---------------------------------
DEFAULT_SYNTHETIC_KEYWORDS = ["synthetic"]
NUMERIC_COLUMNS_EXCLUDE = []  # can be extended by user
CATEGORICAL_NORMALIZE_MAP: Dict[str, Dict[str, str]] = {}
# -----------------------------------------------------------------------------


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def discover_data_files(input_paths: Iterable[str]) -> List[Path]:
    """Return list of csv/json file Paths from input paths or directories."""
    files: List[Path] = []
    for p in input_paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.csv")))
            files.extend(sorted(path.glob("*.json")))
        elif path.is_file():
            files.append(path)
        else:
            logger.warning("Path not found: %s", p)
    return files


def read_file(path: Path) -> pd.DataFrame:
    """Read a CSV or JSON into a DataFrame with robust defaults."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() in (".json", ".ndjson"):
        return pd.read_json(path, lines=True)
    raise ValueError(f"Unsupported file type: {path}")


def load_datasets(
    files: Iterable[Path], synthetic_keywords: Iterable[str]
) -> pd.DataFrame:
    """Load files and append `source_file` and `synthetic_flag`.

    Parameters
    - files: iterable of Path objects
    - synthetic_keywords: keywords to mark files as synthetic (case-insensitive)
    """
    frames = []
    keywords = [k.lower() for k in synthetic_keywords]
    for f in files:
        try:
            df = read_file(f)
        except Exception as e:
            logger.error("Failed to read %s: %s", f, e)
            continue
        df = df.copy()
        df["source_file"] = str(f.name)
        is_synth = any(k in f.name.lower() for k in keywords)
        df["synthetic_flag"] = bool(is_synth)
        frames.append(df)
        logger.info("Loaded %s rows from %s (synthetic=%s)", len(df), f.name, is_synth)
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    return combined


# ----------------------------- Standardization -------------------------------


def _coerce_numeric_strings(series: pd.Series) -> pd.Series:
    """Coerce strings like '$1,234' or '1,234' to numeric floats."""
    # Be defensive: convert to string first to avoid AttributeError when the
    # series contains mixed types (ints, floats, None) but has object dtype.
    try:
        s = (
            series.astype("string")
            .str.replace("$", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        # treat obvious null-like strings as NaN
        s = s.replace({"nan": pd.NA, "none": pd.NA, "": pd.NA})
        return pd.to_numeric(s, errors="coerce")
    except Exception:
        return pd.to_numeric(series, errors="coerce")


def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Attempt to standardize common units based on column names.

    This function mutates dataframe numeric columns to proper floats and normalizes
    percentage columns to 0-1 where applicable.
    """
    df = df.copy()

    for col in df.columns:
        if col in ("source_file", "synthetic_flag"):
            continue
        ser = df[col]
        # If pandas thinks it's numeric but contains currency-like strings, coerce anyway
        if ser.dtype == object:
            # try to coerce strings with $ and commas
            coerced = _coerce_numeric_strings(ser)
            if coerced.notna().sum() > 0:  # some values were numeric-like
                df[col] = coerced
                ser = df[col]
        # Now handle known unit types by name heuristics
        name = col.lower()
        try:
            if any(k in name for k in ("cost", "price", "usd", "dollar", "$")):
                df[col] = pd.to_numeric(ser, errors="coerce").astype("float")
            elif any(k in name for k in ("day", "duration", "elapsed", "lead_time")):
                df[col] = pd.to_numeric(ser, errors="coerce").astype("float")
            elif any(
                k in name for k in ("count", "qty", "quantity", "number", "units")
            ):
                df[col] = pd.to_numeric(ser, errors="coerce").astype("float")
            elif any(k in name for k in ("pct", "percent", "percentage", "ratio")):
                # normalize percentages: if values appear 0-100 -> convert to 0-1
                numeric = pd.to_numeric(ser, errors="coerce")
                maxv = numeric.max(skipna=True)
                if pd.notna(maxv) and maxv > 1.01:
                    df[col] = numeric / 100.0
                else:
                    df[col] = numeric.astype("float")
            else:
                # leave as-is; conversion for other numeric columns will be handled later
                pass
        except Exception:
            # be resilient to bad casts
            df[col] = pd.to_numeric(ser, errors="coerce")

    return df


def normalize_categoricals(
    df: pd.DataFrame,
    mapping: Optional[Dict[str, Dict[str, str]]] = None,
    categorical_cols: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Normalize categorical values: strip, lower, map synonyms.

    mapping: optional dict where keys are column names and values are dicts mapping
             variant -> canonical value, case-insensitive.
    categorical_cols: explicit list of columns to treat as categorical. If None,
                      infer object columns.
    """
    df = df.copy()
    mapping = mapping or {}
    if categorical_cols is None:
        categorical_cols = [c for c, t in df.dtypes.items() if t == object]
    for col in categorical_cols:
        if col not in df.columns:
            continue
        s = df[col].astype("string").str.strip()
        s_norm = s.str.replace(r"\s+", " ", regex=True).str.lower()
        if col in mapping:
            map_dict = {k.lower(): v for k, v in mapping[col].items()}
            s_mapped = s_norm.map(lambda x: map_dict.get(x, x) if pd.notna(x) else x)
            df[col] = s_mapped.fillna("Unknown").astype("string")
        else:
            df[col] = s_norm.fillna("Unknown").astype("string")
    return df


# ----------------------------- Missing values -------------------------------


def impute_missing_numeric(
    df: pd.DataFrame, exclude: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Impute numeric missing values using mean or median based on skewness.

    Returns modified df and a dict log of strategies used per column.
    """
    df = df.copy()
    exclude = exclude or []
    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude
    ]
    strategy_log: Dict[str, str] = {}
    for col in numeric_cols:
        ser = df[col]
        na_count = ser.isna().sum()
        if na_count == 0:
            continue
        # Choose median if skew is large or there are extreme outliers
        try:
            skew = ser.dropna().skew()
        except Exception:
            skew = 0.0
        if pd.isna(skew):
            skew = 0.0
        if abs(skew) > 1.0:
            fill = ser.median()
            strategy = "median"
        else:
            fill = ser.mean()
            strategy = "mean"
        # Coerce to numeric float before filling to avoid pandas nullable-int dtype errors
        numeric_ser = pd.to_numeric(ser, errors="coerce").astype(float)
        df[col] = numeric_ser.fillna(float(fill) if pd.notna(fill) else fill)
        strategy_log[col] = strategy
        logger.info(
            "Imputed %d missing in %s using %s (value=%s)",
            na_count,
            col,
            strategy,
            float(fill) if pd.notna(fill) else None,
        )
    return df, strategy_log


def impute_missing_categorical(
    df: pd.DataFrame, placeholder: str = "Unknown"
) -> pd.DataFrame:
    df = df.copy()
    obj_cols = [
        c for c, t in df.dtypes.items() if str(t).startswith("string") or t == object
    ]
    for col in obj_cols:
        df[col] = df[col].fillna(placeholder).astype("string")
    return df


# ----------------------------- Derived features -----------------------------


def compute_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute derived variables, being robust to missing columns and divide-by-zero."""
    df = df.copy()

    # schedule_slippage_pct = elapsed_days / planned_duration_days
    if "elapsed_days" in df.columns and "planned_duration_days" in df.columns:
        df["schedule_slippage_pct"] = np.where(
            pd.to_numeric(df["planned_duration_days"], errors="coerce") > 0,
            df["elapsed_days"] / df["planned_duration_days"].astype(float),
            np.nan,
        )

    # labor_overrun_ratio = labor_hours_actual / labor_hours_planned
    if "labor_hours_actual" in df.columns and "labor_hours_planned" in df.columns:
        df["labor_overrun_ratio"] = np.where(
            pd.to_numeric(df["labor_hours_planned"], errors="coerce") > 0,
            df["labor_hours_actual"] / df["labor_hours_planned"].astype(float),
            np.nan,
        )

    # material_cost_variance = material_cost_actual - material_cost_planned
    if "material_cost_actual" in df.columns and "material_cost_planned" in df.columns:
        df["material_cost_variance"] = pd.to_numeric(
            df["material_cost_actual"], errors="coerce"
        ) - pd.to_numeric(df["material_cost_planned"], errors="coerce")

    # equipment_idle_ratio = equipment_idle_days / equipment_count
    if "equipment_idle_days" in df.columns and "equipment_count" in df.columns:
        df["equipment_idle_ratio"] = np.where(
            pd.to_numeric(df["equipment_count"], errors="coerce") > 0,
            df["equipment_idle_days"] / df["equipment_count"].astype(float),
            np.nan,
        )

    return df


# -------------------------------- Validation --------------------------------


def find_project_id_column(df: pd.DataFrame) -> Optional[str]:
    candidates = [
        c
        for c in df.columns
        if c.lower() in ("project_id", "id", "proj_id")
        or "project" in c.lower()
        and "id" in c.lower()
    ]
    return candidates[0] if candidates else None


def validate_dataset(df: pd.DataFrame) -> None:
    """Run validations and print summary reports to logger/stdout."""
    logger.info("--- Dataset Validation Report ---")
    pid_col = find_project_id_column(df)
    if pid_col:
        dup = df[pid_col].duplicated().sum()
        logger.info("Project ID column detected: %s", pid_col)
        if dup > 0:
            logger.warning("Duplicate project IDs found: %d", int(dup))
        else:
            logger.info("No duplicate project IDs detected.")
    else:
        logger.warning("No obvious project ID column found.")

    # Obvious numeric outliers: negative values where not expected
    numeric = df.select_dtypes(include=[np.number])
    neg_cols = [
        (c, numeric[c].min(skipna=True))
        for c in numeric.columns
        if numeric[c].min(skipna=True) < 0
    ]
    if neg_cols:
        for c, v in neg_cols:
            logger.warning("Column %s has negative minimum: %s", c, v)
    else:
        logger.info("No negative values detected in numeric columns.")

    # Extreme ratio checks
    for ratio_col in (
        "schedule_slippage_pct",
        "labor_overrun_ratio",
        "equipment_idle_ratio",
    ):
        if ratio_col in df.columns:
            s = df[ratio_col]
            # flag values NaN or extreme
            extreme = s[(s < 0) | (s > 10)].dropna()
            if not extreme.empty:
                logger.warning(
                    "Extreme values in %s: count=%d, sample=%s",
                    ratio_col,
                    len(extreme),
                    extreme.head(3).tolist(),
                )

    # Summary statistics numeric
    if not numeric.empty:
        desc = numeric.agg(["mean", "median", "min", "max"]).T
        logger.info(
            "Numeric summary statistics (mean/median/min/max):\n%s", desc.to_string()
        )

    # Value counts for categorical (show top 10)
    obj_cols = [
        c
        for c in df.columns
        if df[c].dtype == object or str(df[c].dtype).startswith("string")
    ]
    for col in obj_cols:
        logger.info(
            "Top value counts for %s:\n%s",
            col,
            df[col].value_counts(dropna=False).head(10).to_string(),
        )

    logger.info("--- End Validation ---")


# --------------------------------- Main -------------------------------------


def process_datasets(
    input_paths: Iterable[str],
    output_file: str,
    synthetic_keywords: Iterable[str],
    categorical_map: Optional[Dict[str, Dict[str, str]]] = None,
) -> None:
    files = discover_data_files(input_paths)
    if not files:
        raise SystemExit("No input files found.")

    combined = load_datasets(files, synthetic_keywords)
    # ------------------ Deny-list enforcement (INGESTION GUARD) ------------------
    # Purpose: Prevent any target or post-outcome fields from entering the pipeline.
    # Rationale: Leak-proof at the earliest point by dropping known label-derived
    # and post-outcome columns immediately after reading raw inputs. Downstream
    # scripts MUST NOT re-add these columns; assertions below will fail if they do.

    # Exact column names that must be removed if present (from join_aggregation_audit.md)
    DENY_LIST_EXACT = {
        "will_delay",
        "schedule_slippage_pct",
        "slippage_days",
        "elapsed_days",
        "planned_duration_days",
        # common cost/summary fields that are post-outcome
        "Final Estimate of Actual Costs Through End of Phase Amount",
        "Final Estimate of Actual Costs Through End of Phase Amount ",
        "Final Estimate of Actual Costs Through End of Phase Amount",
        "Total Phase Actual Spending Amount",
        # examples from audit
        "Award",
        "BBL",
        "BIN",
        "Borough",
        "Budget_Line",
    }

    # Column name regex patterns to drop (case-insensitive)
    DENY_LIST_PATTERNS = [
        r"(?i)^budget_line",  # Budget_Line, Budget_Line_*
        r"(?i)final.*cost",  # final cost related columns
        r"(?i)actual.*cost",
        r"(?i)actual.*spend",
        r"(?i)actual.*amount",
        r"(?i)total.*actual.*spend",
        # Date-like columns (actual/planned start/end) are intentionally not
        # pattern-matched here because they are required for target derivation
        # during project-level aggregation. Be cautious when adding new patterns.
        r"(?i)elapsed_?days",
        r"(?i)slippage",
        r"(?i)will_?delay",
    ]

    def _drop_deny_list(df: pd.DataFrame) -> tuple[pd.DataFrame, list]:
        import re

        cols = list(df.columns)
        to_drop_exact = set()
        to_drop_pattern = set()

        # helper: normalized column name -> original
        def _normalize_name(s: str) -> str:
            return re.sub(r"\s+", " ", s.strip()).lower()

        norm_map = {_normalize_name(c): c for c in cols}

        # exact matches (case-insensitive, normalized)
        for en in DENY_LIST_EXACT:
            en_norm = _normalize_name(en)
            if en in df.columns:
                to_drop_exact.add(en)
            if en_norm in norm_map:
                to_drop_exact.add(norm_map[en_norm])

        # pattern matches against normalized names
        for pat in DENY_LIST_PATTERNS:
            rx = re.compile(pat)
            for norm_name, orig in norm_map.items():
                if rx.search(norm_name):
                    to_drop_pattern.add(orig)

        # ensure we only drop columns that actually exist in df
        dropped_exact = sorted([c for c in to_drop_exact if c in df.columns])
        dropped_pattern = sorted(
            [c for c in to_drop_pattern if c in df.columns and c not in dropped_exact]
        )

        if dropped_exact:
            logger.info(
                "Deny-list drop (exact): removing %d columns at ingestion: %s",
                len(dropped_exact),
                dropped_exact,
            )
        if dropped_pattern:
            logger.info(
                "Deny-list drop (pattern): removing %d columns at ingestion: %s",
                len(dropped_pattern),
                dropped_pattern,
            )
        if not dropped_exact and not dropped_pattern:
            logger.info("Deny-list drop: no deny-list columns present at ingestion")

        dropped_all = dropped_exact + dropped_pattern
        if dropped_all:
            df = df.drop(columns=dropped_all, errors="ignore")
        return df, dropped_all

    combined, dropped_now = _drop_deny_list(combined)
    # ----------------------------------------------------------------------------
    if combined.empty:
        raise SystemExit("No data loaded from input files.")

    combined = standardize_units(combined)

    # pick categorical columns heuristically or pass mapping
    cat_cols = list(categorical_map.keys()) if categorical_map else None
    combined = normalize_categoricals(
        combined, mapping=categorical_map or {}, categorical_cols=cat_cols
    )

    combined, impute_log = impute_missing_numeric(
        combined, exclude=["synthetic_flag"]
    )  # exclude flags
    combined = impute_missing_categorical(combined)

    # Re-assert deny-list before computing derived features (safety in case
    # standardization or normalization reintroduced name variants).
    combined, dropped_pre_features = _drop_deny_list(combined)

    combined = compute_derived_features(combined)

    # Ensure synthetic_flag exists and is boolean
    if "synthetic_flag" not in combined.columns:
        combined["synthetic_flag"] = False
    combined["synthetic_flag"] = combined["synthetic_flag"].astype(bool)

    validate_dataset(combined)

    # Final safeguard: assert that deny-list columns are not present in final dataframe.
    # This enforces causal correctness: if any downstream code (or an earlier file)
    # reintroduces these columns, fail loudly so the training pipeline cannot proceed.
    present = [
        c
        for c in combined.columns
        if any(c == ex or c.lower().startswith(ex.lower()) for ex in DENY_LIST_EXACT)
        or any(__import__("re").search(pat, c) for pat in DENY_LIST_PATTERNS)
    ]
    if present:
        logger.error(
            "Deny-list violation: found forbidden columns in final dataset: %s", present
        )
        raise SystemExit(
            "Deny-list violation: post-outcome columns present after ingestion. Aborting."
        )

    out_path = Path(output_file)
    combined.to_csv(out_path, index=False)
    logger.info(
        "Saved cleaned dataset to %s (rows=%d, cols=%d)",
        out_path,
        combined.shape[0],
        combined.shape[1],
    )

    # Optionally save imputation log next to output file
    log_path = out_path.with_suffix(".imputation_log.json")
    with open(log_path, "w") as fh:
        json.dump(impute_log, fh, indent=2)
    logger.info("Saved imputation log to %s", log_path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Prepare and clean project datasets for modeling"
    )
    p.add_argument(
        "--input-dir",
        "-i",
        nargs="+",
        required=True,
        help="Input file(s) or directories containing CSV/JSON files",
    )
    p.add_argument(
        "--output",
        "-o",
        default="project_dataset_v1_cleaned.csv",
        help="Output CSV filename",
    )
    p.add_argument(
        "--synthetic-keywords",
        "-s",
        nargs="*",
        default=DEFAULT_SYNTHETIC_KEYWORDS,
        help="Keywords to mark files as synthetic (default: %(default)s)",
    )
    p.add_argument(
        "--categorical-map",
        "-c",
        type=str,
        help="Optional JSON file specifying categorical normalization map",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cat_map = None
    if args.categorical_map:
        try:
            with open(args.categorical_map, "r") as fh:
                cat_map = json.load(fh)
        except Exception as e:
            logger.error("Failed loading categorical map: %s", e)
            raise
    process_datasets(
        args.input_dir, args.output, args.synthetic_keywords, categorical_map=cat_map
    )


if __name__ == "__main__":
    main()
