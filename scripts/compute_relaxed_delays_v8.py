"""Compute relaxed per-project delays for v8 aggregated projects.

Rules:
- planned_start and planned_end: require full-date parses (ignore year-only mid-year)
- actual_start: require full-date parse
- actual_end: allow full-date parse OR normalized year-only (YYYY-07-01)

Reads:
- data_splits/project_level_aggregated_v8.csv
- data_splits/v8/parse_fallbacks.json

Writes:
- data_splits/project_level_aggregated_v8_relaxed.csv
- data_splits/v8/project_level_aggregated_v8_relaxed_summary.txt
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(".")
AGG_IN = ROOT / "data_splits" / "project_level_aggregated_v8.csv"
FALLBACKS = ROOT / "data_splits" / "v8" / "parse_fallbacks.json"
OUT_CSV = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT_SUM = ROOT / "data_splits" / "v8" / "project_level_aggregated_v8_relaxed_summary.txt"


def load_fallbacks(path: Path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # parse_fallbacks.json may be list of records or mapping
    if isinstance(data, list):
        return {rec.get("project_id") or rec.get("project") or str(i): rec for i, rec in enumerate(data)}
    return data


def main():
    df = pd.read_csv(AGG_IN, dtype=str)
    # ensure numeric columns parsed later
    fallbacks = load_fallbacks(FALLBACKS)

    # prepare columns
    df = df.copy()
    df['can_compute_delay'] = False
    df['relaxed_planned_duration_days'] = np.nan
    df['relaxed_elapsed_days'] = np.nan
    df['relaxed_delay_days'] = np.nan
    df['relaxed_schedule_slippage_pct'] = np.nan

    # helper to parse dates from aggregated CSV; aggregated likely has iso format or empty
    def to_dt(val):
        try:
            return pd.to_datetime(val, errors='coerce')
        except Exception:
            return pd.NaT

    # iterate projects
    for ix, row in df.iterrows():
        pid = row.get('project_id') or row.get('project') or str(ix)
        fb = fallbacks.get(pid, {})

        # Determine provenance flags for required fields.
        # We'll look for keys that indicate whether the parsed value was 'year_only' for a field.
        planned_start_full = True
        planned_end_full = True
        actual_start_full = True
        actual_end_full_or_year = False

        # Detect explicit year-only markers
        for fk in ['planned_start', 'planned_end', 'actual_start', 'actual_end']:
            yy_key = fk + '_year_only'
            if isinstance(fb, dict) and fb.get(yy_key) is True:
                if fk == 'actual_end':
                    actual_end_full_or_year = True
                else:
                    if fk == 'planned_start':
                        planned_start_full = False
                    elif fk == 'planned_end':
                        planned_end_full = False
                    elif fk == 'actual_start':
                        actual_start_full = False
        # If no explicit year_only flags present, use provenance heuristics
        if 'planned_start_year_only' not in fb and 'planned_start_provenance' in fb:
            scheduled = fb.get('planned_start_provenance')
            if isinstance(scheduled, str) and 'year_only' in scheduled:
                planned_start_full = False
        if 'planned_end_year_only' not in fb and 'planned_end_provenance' in fb:
            scheduled = fb.get('planned_end_provenance')
            if isinstance(scheduled, str) and 'year_only' in scheduled:
                planned_end_full = False
        if 'actual_start_year_only' not in fb and 'actual_start_provenance' in fb:
            scheduled = fb.get('actual_start_provenance')
            if isinstance(scheduled, str) and 'year_only' in scheduled:
                actual_start_full = False
        if 'actual_end_year_only' not in fb and 'actual_end_provenance' in fb:
            scheduled = fb.get('actual_end_provenance')
            if isinstance(scheduled, str) and 'year_only' in scheduled:
                actual_end_full_or_year = True

        # Also, if aggregated has normalized year-only strings like 'YYYY-07-01', detect them
        for fld, colname in [('planned_start', 'planned_start'), ('planned_end', 'planned_end'),
                              ('actual_start', 'actual_start'), ('actual_end', 'actual_end')]:
            val = row.get(colname)
            if pd.isna(val) or val == '' or str(val).lower() == 'nan':
                continue
            s = str(val)
            if len(s) >= 10 and s.endswith('-07-01') and s[:4].isdigit():
                if fld == 'actual_end':
                    actual_end_full_or_year = True
                else:
                    if fld == 'planned_start':
                        planned_start_full = False
                    elif fld == 'planned_end':
                        planned_end_full = False
                    elif fld == 'actual_start':
                        actual_start_full = False

        # Apply relaxed rule
        can_compute = bool(planned_start_full and planned_end_full and actual_start_full and (actual_end_full_or_year or (not pd.isna(row.get('actual_end')) and row.get('actual_end') != '')))

        if not can_compute:
            df.at[ix, 'can_compute_delay'] = False
            continue

        # parse dates
        ps = to_dt(row.get('planned_start'))
        pe = to_dt(row.get('planned_end'))
        acs = to_dt(row.get('actual_start'))
        ace = to_dt(row.get('actual_end'))

        if pd.isna(ps) or pd.isna(pe) or pd.isna(acs) or pd.isna(ace):
            df.at[ix, 'can_compute_delay'] = False
            continue

        planned_duration = (pe - ps).days
        elapsed = (ace - acs).days
        delay = elapsed - planned_duration
        slippage = None
        if planned_duration != 0:
            slippage = delay / planned_duration

        df.at[ix, 'can_compute_delay'] = True
        df.at[ix, 'relaxed_planned_duration_days'] = planned_duration
        df.at[ix, 'relaxed_elapsed_days'] = elapsed
        df.at[ix, 'relaxed_delay_days'] = delay
        df.at[ix, 'relaxed_schedule_slippage_pct'] = slippage

    # write outputs
    df.to_csv(OUT_CSV, index=False)

    total = len(df)
    computable = int(df['can_compute_delay'].sum())
    with OUT_SUM.open('w', encoding='utf-8') as f:
        f.write(f"Input aggregated projects: {total}\n")
        f.write(f"Projects with computable delay (relaxed rule): {computable}\n")
        f.write(f"Projects without computable delay: {total - computable}\n")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote summary to {OUT_SUM}")


if __name__ == '__main__':
    main()
