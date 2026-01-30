#!/usr/bin/env python3
"""
Robust project-level aggregation v8

Parses multiple candidate date columns, computes project-level planned/elapsed durations,
calculates delay and slippage, and produces train/test splits for v8.

Usage: python scripts/agg_redefine_target_and_split_v8.py \
    --input-rows data_splits/project_dataset_v7_cleaned.csv \
    --output-agg data_splits/project_level_aggregated_v8.csv \
    --output-dir data_splits/v8 --test-size 0.2 --random-state 42

This script avoids using any deny-list columns and logs parsing fallbacks.
"""

import argparse
import os
import json
import re
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import math


DENY_LIST = set([c.lower() for c in (
    ['will_delay', 'schedule_slippage_pct', 'award', 'bbl', 'bin', 'cost', 'cost_estimated']
 )])


DATE_PATTERNS = [
    re.compile(r"\d{4}-\d{1,2}-\d{1,2}"),
    re.compile(r"\d{1,2}/\d{1,2}/\d{4}"),
    re.compile(r"\d{1,2}-\d{1,2}-\d{4}"),
    re.compile(r"\d{4}/\d{1,2}/\d{1,2}"),
]


def is_full_date_value(s: str) -> bool:
    if pd.isna(s):
        return False
    s = str(s).strip()
    if not s:
        return False
    for pat in DATE_PATTERNS:
        if pat.search(s):
            return True
    # ISO exact match
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return True
    return False


def clean_token(s: str) -> str:
    if pd.isna(s):
        return ''
    s = str(s).strip()
    if not s:
        return ''
    s_low = s.strip().lower()
    # common non-date tokens in raw data
    if s_low in ('unknown', 'na', 'n/a', 'none', 'ieh', 'doer', 'pns', 'ftk', 'does'):
        return ''
    # remove obvious prefixes/suffixes like 'issued:' or labels
    s = re.sub(r"^[A-Za-z:._\-\s]+", '', s)
    s = s.strip()
    return s


def parse_date_str(s: str):
    s = clean_token(s)
    if not s:
        return pd.NaT

    # First look for explicit date-like substrings (fast)
    for pat in DATE_PATTERNS:
        m = pat.search(s)
        if m:
            sub = m.group(0)
            try:
                dt = pd.to_datetime(sub, errors='coerce', dayfirst=False)
                if not pd.isna(dt):
                    return dt
                dt = pd.to_datetime(sub, errors='coerce', dayfirst=True)
                if not pd.isna(dt):
                    return dt
            except Exception:
                continue

    # Year-only fallback: interpret 4-digit year as mid-year anchor (YYYY-07-01)
    if re.fullmatch(r"\d{4}$", s):
        try:
            y = int(s)
            return pd.Timestamp(datetime(y, 7, 1))
        except Exception:
            pass

    # Excel serial number fallback (pure integers)
    if re.fullmatch(r"\d+", s):
        try:
            serial = int(s)
            if serial > 20000:
                return datetime(1899, 12, 30) + timedelta(days=serial)
        except Exception:
            pass

    # As a last resort, attempt a lightweight parse for ISO-like strings
    iso_match = re.match(r"^(\d{4}-\d{2}-\d{2})$", s)
    if iso_match:
        try:
            return pd.to_datetime(iso_match.group(1), errors='coerce')
        except Exception:
            pass

    return pd.NaT


def normalize_year_column(df: pd.DataFrame, col: str):
    """Normalize year-like values in `col` into mid-year date strings YYYY-07-01.

    - Converts numeric-like strings to numbers
    - Floors to integer year
    - Validates range 1900-2100
    - Writes back as 'YYYY-07-01' for valid years
    """
    if col not in df.columns:
        return df
    # coerce to numeric
    nums = pd.to_numeric(df[col], errors='coerce')
    valid_mask = nums.notna() & (nums >= 1900) & (nums <= 2100)
    if valid_mask.any():
        # floor fractional years to avoid over-estimation
        yrs = nums[valid_mask].apply(lambda x: int(math.floor(float(x))))
        yrs = yrs.clip(lower=1900, upper=2100)
        df.loc[valid_mask, col] = yrs.astype(int).astype(str) + '-07-01'
    return df


def find_candidate_columns(cols):
    # heuristics for candidate columns
    lc = [c.lower() for c in cols]
    candidates = {
        'planned_start': [],
        'planned_end': [],
        'actual_start': [],
        'actual_end': []
    }

    for c in cols:
        cl = c.lower()
        if 'planned' in cl and 'start' in cl:
            candidates['planned_start'].append(c)
        if 'planned' in cl and 'end' in cl:
            candidates['planned_end'].append(c)
        if 'actual' in cl and 'start' in cl:
            candidates['actual_start'].append(c)
        if 'actual' in cl and 'end' in cl:
            candidates['actual_end'].append(c)
        # permit/permityear/filed/completion are useful fallbacks
        if 'datefiled' in cl or 'filed' in cl:
            candidates['actual_start'].append(c)
        if 'datepermit' in cl or 'permit' in cl:
            candidates['planned_end'].append(c)
        if 'datecomplt' in cl or 'complt' in cl or 'datecomplt' in cl:
            candidates['actual_end'].append(c)
    return candidates


def coerce_and_parse_dates(df, candidate_map):
    parsed_map = {}
    yearonly_map = {}
    # mapping from parsed column name to original
    parsed_orig = {}
    for role, cols in candidate_map.items():
        parsed_cols = []
        yearonly_cols = []
        for c in cols:
            parsed_name = f"_parsed__{c}"
            yearonly_name = f"_yearonly__{c}"
            fullparsed_name = f"_fullparsed__{c}"
            # parse column into datetime
            df[parsed_name] = df[c].apply(parse_date_str)
            # detect year-only tokens (exact 4-digit year)
            df[yearonly_name] = df[c].fillna('').astype(str).str.fullmatch(r'^\d{4}$')
            # detect whether original value looked like a full date
            df[fullparsed_name] = df[c].apply(is_full_date_value)
            parsed_cols.append(parsed_name)
            yearonly_cols.append(yearonly_name)
            parsed_orig[parsed_name] = c
        parsed_map[role] = parsed_cols
        yearonly_map[role] = yearonly_cols
    return df, parsed_map, yearonly_map, parsed_orig


def aggregate_to_project(df, parsed_map, yearonly_map, group_key='project_id'):
    # We'll build an aggregated dataframe
    projects = []
    parse_fallbacks = []

    grp = df.groupby(group_key)

    # First pass: collect parsed dates and non-date first values per project
    temp = []
    for project_id, sub in grp:
        entry = {group_key: project_id}
        # Keep first non-empty values for non-date columns (excluding deny-list)
        for col in sub.columns:
            if col.startswith('_parsed__'):
                continue
            if col.lower() in DENY_LIST:
                continue
            if col in (group_key,):
                continue
            vals = sub[col].dropna().astype(str)
            vals = vals[~vals.str.strip().isin(['', 'nan', 'NaN', 'Unknown'])]
            entry[col] = vals.iloc[0] if len(vals) > 0 else None

        # helper functions to extract per-project parsed series
        def collect_series(parsed_cols, require_full=False, allow_year=False):
            parts = []
            for pc in parsed_cols:
                if pc in sub:
                    orig = pc.replace('_parsed__', '')
                    full_flag = f"_fullparsed__{orig}"
                    year_flag = f"_yearonly__{orig}"
                    if require_full and full_flag in sub:
                        mask = sub[full_flag].astype(bool)
                        series = pd.to_datetime(sub.loc[mask, pc].dropna(), errors='coerce')
                    else:
                        if allow_year and year_flag in sub and sub[year_flag].astype(bool).any():
                            mask = sub[year_flag].astype(bool)
                            series = pd.to_datetime(sub.loc[mask, pc].dropna(), errors='coerce')
                        else:
                            series = pd.to_datetime(sub[pc].dropna(), errors='coerce')
                    if not series.empty:
                        parts.append(series)
            if not parts:
                return None
            dates = pd.concat(parts)
            if dates.empty:
                return None
            return dates

        # planned candidates: earliest and latest across planned_start and planned_end
        planned_candidates = list(parsed_map.get('planned_start', [])) + list(parsed_map.get('planned_end', []))
        planned_dates = collect_series(planned_candidates, require_full=True, allow_year=False)
        if planned_dates is not None:
            entry['_planned_start'] = planned_dates.min()
            entry['_planned_end'] = planned_dates.max()
        else:
            entry['_planned_start'] = pd.NaT
            entry['_planned_end'] = pd.NaT

        # actual candidates: collect both full and any/year-only for fallback
        actual_start_full = collect_series(parsed_map.get('actual_start', []), require_full=True, allow_year=False)
        actual_start_any = collect_series(parsed_map.get('actual_start', []), require_full=False, allow_year=True)
        actual_end_full = collect_series(parsed_map.get('actual_end', []), require_full=True, allow_year=False)
        actual_end_any = collect_series(parsed_map.get('actual_end', []), require_full=False, allow_year=True)

        entry['_actual_start_full'] = actual_start_full.min() if actual_start_full is not None else pd.NaT
        entry['_actual_start_any'] = actual_start_any.min() if actual_start_any is not None else pd.NaT
        entry['_actual_end_full'] = actual_end_full.max() if actual_end_full is not None else pd.NaT
        entry['_actual_end_any'] = actual_end_any.max() if actual_end_any is not None else pd.NaT

        # record which parsed cols had values
        used = {}
        year_only_used = []
        for role, pcs in parsed_map.items():
            used[role] = [pc for pc in pcs if pc in sub and sub[pc].notna().any()]
        for role, ycols in yearonly_map.items():
            for yc in ycols:
                orig = yc.replace('_yearonly__', '')
                if yc in sub and sub[yc].astype(bool).any():
                    year_only_used.append(orig)

        entry['_used'] = used
        entry['_year_only_used'] = sorted(list(set(year_only_used)))

        temp.append(entry)

    # compute median planned duration across projects (in days) for imputation
    planned_durations = []
    for e in temp:
        a = e.get('_planned_start')
        b = e.get('_planned_end')
        if pd.isna(a) or pd.isna(b):
            continue
        days = float((pd.Timestamp(b) - pd.Timestamp(a)).days)
        if days <= 1825 and days >= 0:
            planned_durations.append(days)
    median_planned = float(np.median(planned_durations)) if len(planned_durations) > 0 else 365.0

    # Second pass: compute final aggregated fields using imputation rules
    for entry in temp:
        out = {}
        project_id = entry[group_key]
        out[group_key] = project_id
        # copy first non-date values
        for k, v in entry.items():
            if k.startswith('_'):
                continue
            if k.lower() in DENY_LIST:
                continue
            out[k] = v

        ps = entry.get('_planned_start')
        pe = entry.get('_planned_end')
        out['planned_start'] = pd.NaT if pd.isna(ps) else pd.Timestamp(ps)
        out['planned_end'] = pd.NaT if pd.isna(pe) else pd.Timestamp(pe)

        # compute planned_duration and apply cap
        def days_between(a, b):
            if pd.isna(a) or pd.isna(b):
                return np.nan
            return float((pd.Timestamp(b) - pd.Timestamp(a)).days)

        planned_duration = days_between(out['planned_start'], out['planned_end'])
        # detect whether planned_end was derived from year-only source for this project
        planned_end_year_only = False
        try:
            planned_end_orig_cols = [pc.replace('_parsed__', '') for pc in parsed_map.get('planned_end', [])]
            y_used = entry.get('_year_only_used', []) or []
            if any(orig in y_used for orig in planned_end_orig_cols):
                planned_end_year_only = True
        except Exception:
            planned_end_year_only = False

        # cap excessively long planned durations
        if not (pd.isna(planned_duration)) and planned_duration > 1825:
            planned_duration = np.nan
        # allow zero-duration planned windows if planned_end was year-only or within 1 day epsilon
        if not pd.isna(planned_duration) and planned_duration == 0:
            if not planned_end_year_only:
                # allow small epsilon: if planned_end and planned_start differ by <=1 day, keep as-is (0 or 1)
                # nothing to change here; keep 0 (we will compute delay but schedule_slippage remains NaN)
                pass

        # determine actual_end and actual_start with fallbacks
        actual_end = entry.get('_actual_end_full')
        if pd.isna(actual_end):
            actual_end = entry.get('_actual_end_any')
        actual_start = entry.get('_actual_start_full')
        if pd.isna(actual_start):
            if not pd.isna(entry.get('_actual_start_any')):
                actual_start = entry.get('_actual_start_any')

        # impute actual_start when appropriate
        actual_start_imputed = False
        has_planned_full = (not pd.isna(entry.get('_planned_start'))) and (not pd.isna(entry.get('_planned_end')))
        # Rule A: If planned window is full (both planned_start and planned_end full dates)
        # and actual_start is missing but actual_end is present, impute actual_start = actual_end - planned_duration
        # only when planned_duration is plausible (<= 1825 days)
        imputation_rule = 'none'
        # Detect whether actual_end was derived from a year-only source for this project
        actual_end_year_only = False
        try:
            # parsed_map is in scope for this function; determine original actual_end candidate names
            actual_end_orig_cols = [pc.replace('_parsed__', '') for pc in parsed_map.get('actual_end', [])]
            # if any of those originals were recorded as year-only in this entry, flag
            y_used = entry.get('_year_only_used', []) or []
            if any(orig in y_used for orig in actual_end_orig_cols):
                actual_end_year_only = True
        except Exception:
            actual_end_year_only = False

        if pd.isna(actual_start) and not pd.isna(actual_end) and has_planned_full:
            pdur = days_between(entry.get('_planned_start'), entry.get('_planned_end'))
            if not pd.isna(pdur) and pdur <= 1825:
                actual_start = pd.Timestamp(actual_end) - pd.Timedelta(days=pdur)
                actual_start_imputed = True
                # choose RuleA vs RuleC depending on whether actual_end is year-only
                imputation_rule = 'RuleC' if actual_end_year_only else 'RuleA'
        # Fallback (existing behavior): if planned window not full but actual_end present,
        # impute using median planned duration across projects
        elif pd.isna(actual_start) and not pd.isna(actual_end) and (not has_planned_full):
            actual_start = pd.Timestamp(actual_end) - pd.Timedelta(days=median_planned)
            actual_start_imputed = True
            imputation_rule = 'median_fallback'

        out['actual_start'] = pd.NaT if pd.isna(actual_start) else pd.Timestamp(actual_start)
        out['actual_end'] = pd.NaT if pd.isna(actual_end) else pd.Timestamp(actual_end)
        out['actual_start_imputed'] = bool(actual_start_imputed)
        out['imputation_rule'] = imputation_rule

        # compute elapsed/planned/delay
        elapsed_days = days_between(out['actual_start'], out['actual_end'])

        # Ensure planned_duration_days numeric and plausible
        out['planned_duration_days'] = (float(planned_duration) if not pd.isna(planned_duration) else np.nan)
        out['elapsed_days'] = (float(elapsed_days) if not pd.isna(elapsed_days) else np.nan)

        # compute delay/slippage robustly
        if pd.isna(out['planned_duration_days']):
            out['delay_days'] = np.nan
            out['schedule_slippage_pct'] = np.nan
        else:
            if pd.isna(out['elapsed_days']):
                out['delay_days'] = np.nan
                out['schedule_slippage_pct'] = np.nan
            else:
                out['delay_days'] = out['elapsed_days'] - out['planned_duration_days']
                # compute schedule_slippage_pct only when planned duration > 0
                if out['planned_duration_days'] > 0:
                    out['schedule_slippage_pct'] = out['delay_days'] / out['planned_duration_days']
                else:
                    out['schedule_slippage_pct'] = np.nan

        # parse fallback info
        parse_fallbacks.append({'project_id': project_id, 'used': entry.get('_used', {}), 'year_only_parse': entry.get('_year_only_used', []), 'actual_start_imputed': bool(actual_start_imputed)})

        projects.append(out)

    agg = pd.DataFrame(projects)
    return agg, parse_fallbacks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-rows', required=True)
    parser.add_argument('--output-agg', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--test-size', type=float, default=0.2)
    parser.add_argument('--random-state', type=int, default=42)
    parser.add_argument('--slippage-threshold', type=float, default=0.0,
                        help='Threshold on schedule_slippage_pct to label delay (default 0.0)')
    parser.add_argument('--stratify', action='store_true', help='Attempt stratified split if positives exist')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_agg), exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)

    print('Loading rows from', args.input_rows)
    df = pd.read_csv(args.input_rows, dtype=str)

    # Normalize year-like fields so they can act as year-only fallbacks
    if 'PermitYear' in df.columns:
        df = normalize_year_column(df, 'PermitYear')
    if 'CompltYear' in df.columns:
        df = normalize_year_column(df, 'CompltYear')

    # Identify candidate columns
    candidate_map = find_candidate_columns(df.columns.tolist())
    # Ensure DateFiled and DatePermit are considered as planned_start (priority order)
    if 'DateFiled' in df.columns:
        candidate_map.setdefault('planned_start', [])
        if 'DateFiled' not in candidate_map['planned_start']:
            # highest priority
            candidate_map['planned_start'].insert(0, 'DateFiled')
    if 'DatePermit' in df.columns:
        candidate_map.setdefault('planned_start', [])
        if 'DatePermit' not in candidate_map['planned_start']:
            candidate_map['planned_start'].insert(1, 'DatePermit')
    print('Candidate date columns:', candidate_map)

    # Only consider candidate columns that exist
    candidate_map = {k: [c for c in v if c in df.columns] for k, v in candidate_map.items()}

    # Parse date candidates and create parsed columns
    df_parsed, parsed_map, yearonly_map, parsed_orig = coerce_and_parse_dates(df, candidate_map)

    # Aggregate
    agg, parse_fallbacks = aggregate_to_project(df_parsed, parsed_map, yearonly_map, group_key='project_id')

    # Clean numeric columns
    for col in ['planned_duration_days', 'elapsed_days', 'delay_days', 'schedule_slippage_pct']:
        if col in agg.columns:
            agg[col] = pd.to_numeric(agg[col], errors='coerce').astype(float)

    # Compute additional labels
    threshold = args.slippage_threshold
    agg['will_delay'] = ((agg['schedule_slippage_pct'] > threshold) | (agg['delay_days'] > 0)).fillna(False).astype(int)
    # absolute 30-day delay
    agg['will_delay_abs30'] = (pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce') > 30).fillna(False).astype(int)
    # relative 5% slippage over planned, only when planned_duration_days > 14
    planned_pos = pd.to_numeric(agg.get('planned_duration_days', pd.Series()), errors='coerce')
    delay_num = pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce')
    agg['will_delay_rel5pct'] = ((delay_num / planned_pos) > 0.05) & (planned_pos > 14)
    agg['will_delay_rel5pct'] = agg['will_delay_rel5pct'].fillna(False).astype(int)

    # Validate counts
    total = len(agg)
    positives = int(agg['will_delay'].sum())
    negatives = total - positives
    abs30_pos = int(agg['will_delay_abs30'].sum())
    rel5_pos = int(agg['will_delay_rel5pct'].sum())
    print(f'Project-level target: total={total} will_delay_pos={positives} will_delay_abs30_pos={abs30_pos} will_delay_rel5pct_pos={rel5_pos} negatives={negatives}')

    # Save aggregated CSV
    agg.to_csv(args.output_agg, index=False)
    print('Saved aggregated project-level file to', args.output_agg)

    # Save parse fallback log
    fallback_path = os.path.join(args.output_dir, 'parse_fallbacks.json')
    with open(fallback_path, 'w') as f:
        json.dump(parse_fallbacks, f, default=str, indent=2)
    print('Wrote parse fallback log to', fallback_path)

    # Save counts
    counts_path = os.path.join(args.output_dir, 'v8_label_counts.txt')
    with open(counts_path, 'w') as f:
        f.write(f'total={total}\nwill_delay_positives={positives}\nwill_delay_abs30_positives={abs30_pos}\nwill_delay_rel5pct_positives={rel5_pos}\nnegatives={negatives}\n')
    print('Wrote label counts to', counts_path)

    # Additionally, write a Rule A specific aggregated CSV and diagnostics
    ruleA_path = os.path.join(os.path.dirname(args.output_agg), 'project_level_aggregated_v8_ruleA.csv')
    agg.to_csv(ruleA_path, index=False)
    print('Wrote Rule A aggregated CSV to', ruleA_path)

    diagnostics_ruleA = os.path.join(args.output_dir, 'diagnostics_ruleA.txt')
    imputed_count = int(pd.to_numeric(agg.get('actual_start_imputed', pd.Series(0)), errors='coerce').fillna(0).sum())
    # counts by imputation rule
    try:
        counts_by_rule = agg['imputation_rule'].value_counts(dropna=False).to_dict()
    except Exception:
        counts_by_rule = {}
    computable_count = int(agg['delay_days'].notna().sum()) if 'delay_days' in agg.columns else 0
    with open(diagnostics_ruleA, 'w') as f:
        f.write(f'total_projects={total}\n')
        f.write(f'actual_start_imputed_count={imputed_count}\n')
        f.write('counts_by_imputation_rule=' + str(counts_by_rule) + '\n')
        f.write(f'computed_delay_count={computable_count}\n')
        f.write(f'will_delay_positives={positives}\n')
        f.write(f'will_delay_abs30_positives={abs30_pos}\n')
        f.write(f'will_delay_rel5pct_positives={rel5_pos}\n')
    print('Wrote Rule A diagnostics to', diagnostics_ruleA)

    # Create train/test split
    X = agg.drop(columns=['will_delay', 'will_delay_abs30', 'will_delay_rel5pct'], errors='ignore')
    y = agg['will_delay']

    stratify = None
    if args.stratify and positives > 1 and positives < total:
        stratify = y

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=args.random_state, stratify=stratify
        )
    except ValueError as e:
        print('Stratified split failed or not possible, falling back to random split:', e)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=args.test_size, random_state=args.random_state
        )

    splits_dir = args.output_dir
    X_train.to_csv(os.path.join(splits_dir, 'X_train.csv'), index=False)
    X_test.to_csv(os.path.join(splits_dir, 'X_test.csv'), index=False)
    y_train.to_csv(os.path.join(splits_dir, 'y_train.csv'), index=False, header=['will_delay'])
    y_test.to_csv(os.path.join(splits_dir, 'y_test.csv'), index=False, header=['will_delay'])

    # Save label-specific y files for new labels
    y_train_abs30 = agg['will_delay_abs30'].loc[X_train.index]
    y_test_abs30 = agg['will_delay_abs30'].loc[X_test.index]
    y_train_abs30.to_csv(os.path.join(splits_dir, 'y_train_abs30.csv'), index=False, header=['will_delay_abs30'])
    y_test_abs30.to_csv(os.path.join(splits_dir, 'y_test_abs30.csv'), index=False, header=['will_delay_abs30'])

    y_train_rel5 = agg['will_delay_rel5pct'].loc[X_train.index]
    y_test_rel5 = agg['will_delay_rel5pct'].loc[X_test.index]
    y_train_rel5.to_csv(os.path.join(splits_dir, 'y_train_rel5pct.csv'), index=False, header=['will_delay_rel5pct'])
    y_test_rel5.to_csv(os.path.join(splits_dir, 'y_test_rel5pct.csv'), index=False, header=['will_delay_rel5pct'])

    print('Saved splits to', splits_dir)

    # metadata
    meta = {
        'total_projects': total,
        'positives': positives,
        'negatives': negatives,
        'slippage_threshold': threshold,
        'test_size': args.test_size,
        'random_state': args.random_state,
        'candidate_map': candidate_map,
    }
    with open(os.path.join(splits_dir, 'metadata.json'), 'w') as f:
        json.dump(meta, f, indent=2, default=str)
    print('Wrote metadata.json')

    # Also write a relaxed aggregated CSV and diagnostics
    relaxed_path = os.path.join(os.path.dirname(args.output_agg), 'project_level_aggregated_v8_relaxed.csv')
    agg.to_csv(relaxed_path, index=False)
    diagnostics_relaxed = os.path.join(args.output_dir, 'diagnostics_relaxed.txt')
    computable_count_relaxed = int(agg['delay_days'].notna().sum()) if 'delay_days' in agg.columns else 0
    with open(diagnostics_relaxed, 'w') as f:
        f.write(f'total_projects={total}\n')
        f.write(f'computable_delay_count_relaxed={computable_count_relaxed}\n')
        f.write('counts_by_imputation_rule=' + str(counts_by_rule) + '\n')
    print('Wrote relaxed aggregated CSV to', relaxed_path)
    print('Wrote diagnostics to', diagnostics_relaxed)


if __name__ == '__main__':
    main()
