"""Generate per-project parsing/blocker diagnostics for v8 aggregated relaxed CSV.

Outputs:
- data_splits/v8/parsing_blockers_diagnostics_v8.csv
- data_splits/v8/parsing_blockers_diagnostics_v8_summary.txt

Includes flags and placeholder numeric columns as requested.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path('.')
IN_CSV = ROOT / 'data_splits' / 'project_level_aggregated_v8_relaxed.csv'
OUT_CSV = ROOT / 'data_splits' / 'v8' / 'parsing_blockers_diagnostics_v8.csv'
OUT_SUM = ROOT / 'data_splits' / 'v8' / 'parsing_blockers_diagnostics_v8_summary.txt'


def to_dt(val):
    try:
        return pd.to_datetime(val, errors='coerce')
    except Exception:
        return pd.NaT


def is_year_only_marker(s: str) -> bool:
    if s is None:
        return False
    s = str(s)
    return len(s) >= 10 and s.endswith('-07-01') and s[:4].isdigit()


def main():
    df = pd.read_csv(IN_CSV, dtype=str)
    out_rows = []

    for _, r in df.iterrows():
        pid = r.get('project_id') or r.get('project') or ''
        ps_raw = r.get('planned_start')
        pe_raw = r.get('planned_end')
        acs_raw = r.get('actual_start')
        ace_raw = r.get('actual_end')

        ps_dt = to_dt(ps_raw)
        pe_dt = to_dt(pe_raw)
        acs_dt = to_dt(acs_raw)
        ace_dt = to_dt(ace_raw)

        planned_window_valid = False
        if (not pd.isna(ps_dt)) and (not pd.isna(pe_dt)) and (ps_dt != pe_dt):
            planned_window_valid = True

        actual_start_present = not (pd.isna(acs_dt) or str(acs_raw).strip() == '' or str(acs_raw).lower()=='nan')
        actual_end_present = not (pd.isna(ace_dt) and (str(ace_raw).strip() == '' or str(ace_raw).lower()=='nan'))

        # detect year-only vs full-date for actual_end
        actual_end_is_year_only = is_year_only_marker(ace_raw)
        actual_end_is_full_date = (not pd.isna(ace_dt)) and (not actual_end_is_year_only)

        # can_compute_delay: use existing column if present, otherwise evaluate relaxed rule
        if 'can_compute_delay' in r.index:
            try:
                can_compute = bool(str(r['can_compute_delay']).strip().lower() in ('1','true','t','yes'))
            except Exception:
                can_compute = False
        else:
            can_compute = planned_window_valid and actual_start_present and (actual_end_is_full_date or actual_end_is_year_only)

        # compute placeholders
        planned_duration_days = np.nan
        elapsed_days = np.nan
        delay_days = np.nan
        if planned_window_valid:
            planned_duration_days = (pe_dt - ps_dt).days
        if actual_start_present and actual_end_present and (not pd.isna(acs_dt)) and (not pd.isna(ace_dt)):
            elapsed_days = (ace_dt - acs_dt).days
        if not np.isnan(planned_duration_days) and not np.isnan(elapsed_days):
            delay_days = elapsed_days - planned_duration_days

        out_rows.append({
            'project_id': pid,
            'planned_start': ps_raw,
            'planned_end': pe_raw,
            'actual_start': acs_raw,
            'actual_end': ace_raw,
            'planned_window_valid': planned_window_valid,
            'actual_start_present': actual_start_present,
            'actual_end_present': actual_end_present,
            'actual_end_is_year_only': actual_end_is_year_only,
            'actual_end_is_full_date': actual_end_is_full_date,
            'can_compute_delay': can_compute,
            'planned_duration_days': planned_duration_days,
            'elapsed_days': elapsed_days,
            'delay_days': delay_days,
        })

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(OUT_CSV, index=False)

    # summary counts
    total = len(out_df)
    planned_invalid = int((~out_df['planned_window_valid']).sum())
    missing_actual_start = int((~out_df['actual_start_present']).sum())
    missing_actual_end = int((~out_df['actual_end_present']).sum())
    cannot_compute = int((~out_df['can_compute_delay']).sum())

    with OUT_SUM.open('w', encoding='utf-8') as f:
        f.write(f"Total projects: {total}\n")
        f.write(f"Planned window invalid (start==end or missing): {planned_invalid}\n")
        f.write(f"Missing actual_start: {missing_actual_start}\n")
        f.write(f"Missing actual_end: {missing_actual_end}\n")
        f.write(f"Projects that cannot compute delay: {cannot_compute}\n")

    print(f"Wrote diagnostics CSV to {OUT_CSV}")
    print(f"Wrote summary to {OUT_SUM}")


if __name__ == '__main__':
    main()
