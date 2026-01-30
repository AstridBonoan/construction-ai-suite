#!/usr/bin/env python3
import pandas as pd
import re
import os
from datetime import datetime

INPUT_AGG = 'data_splits/project_level_aggregated_v8.csv'
INPUT_ROWS = 'data_splits/project_dataset_v7_cleaned.csv'
OUT_CSV = 'data_splits/v8/numeric_project_imputed_samples.csv'
OUT_SUM = 'data_splits/v8/numeric_project_imputed_samples_summary.txt'

DATE_PATTERNS = [
    re.compile(r"\d{4}-\d{1,2}-\d{1,2}"),
    re.compile(r"\d{1,2}/\d{1,2}/\d{4}"),
    re.compile(r"\d{1,2}-\d{1,2}-\d{4}"),
    re.compile(r"\d{4}/\d{1,2}/\d{1,2}"),
]

NON_DATE_TOKENS = set(['unknown','na','n/a','none','ieh','doer','pns','ftk','does'])


def clean_token(s: str) -> str:
    if pd.isna(s):
        return ''
    s = str(s).strip()
    if not s:
        return ''
    s_low = s.strip().lower()
    if s_low in NON_DATE_TOKENS:
        return ''
    s = re.sub(r"^[A-Za-z:._\-\s]+", '', s)
    return s.strip()


def parse_date_str(s: str):
    s = clean_token(s)
    if not s:
        return None
    for pat in DATE_PATTERNS:
        m = pat.search(s)
        if m:
            sub = m.group(0)
            try:
                dt = pd.to_datetime(sub, errors='coerce', dayfirst=False)
                if not pd.isna(dt):
                    return pd.Timestamp(dt).normalize()
                dt = pd.to_datetime(sub, errors='coerce', dayfirst=True)
                if not pd.isna(dt):
                    return pd.Timestamp(dt).normalize()
            except Exception:
                continue
    # ISO exact
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        try:
            return pd.to_datetime(s, errors='coerce')
        except Exception:
            return None
    # year-only
    if re.fullmatch(r"\d{4}$", s):
        try:
            y = int(s)
            return pd.Timestamp(datetime(y,7,1))
        except Exception:
            return None
    # numeric
    if re.fullmatch(r"\d+\.\d+|\d+", s):
        try:
            n = float(s)
            if 1900 <= n <= 2100:
                y = int(n)
                return pd.Timestamp(datetime(y,7,1))
        except Exception:
            pass
    return None


def find_actual_start_columns(cols):
    candidates = []
    for c in cols:
        cl = c.lower()
        if 'actual' in cl and 'start' in cl:
            candidates.append(c)
        if 'filed' in cl:
            candidates.append(c)
    return list(dict.fromkeys(candidates))


def main():
    agg = pd.read_csv(INPUT_AGG, dtype=str)
    rows = pd.read_csv(INPUT_ROWS, dtype=str)

    # normalize aggregated actual_start to Timestamp
    agg['actual_start_ts'] = pd.to_datetime(agg['actual_start'], errors='coerce')
    agg['actual_end_ts'] = pd.to_datetime(agg['actual_end'], errors='coerce')
    agg['planned_start_ts'] = pd.to_datetime(agg['planned_start'], errors='coerce')
    agg['planned_end_ts'] = pd.to_datetime(agg['planned_end'], errors='coerce')

    actual_start_cols = find_actual_start_columns(rows.columns.tolist())
    # ensure DateFiled included
    if 'DateFiled' in rows.columns and 'DateFiled' not in actual_start_cols:
        actual_start_cols.append('DateFiled')

    imputed_projects = []
    details = []

    for _, prow in agg.iterrows():
        pid = prow['project_id']
        a_start = prow['actual_start_ts']
        a_end = prow['actual_end_ts']
        # collect parsed actual_start candidates from row-level
        proj_rows = rows[rows['project_id'] == pid]
        parsed_starts = set()
        for col in actual_start_cols:
            if col in proj_rows.columns:
                for v in proj_rows[col].dropna().astype(str).unique():
                    dt = parse_date_str(v)
                    if dt is not None:
                        parsed_starts.add(pd.Timestamp(dt))
        # if aggregated actual_start not in parsed_starts, mark as imputed
        is_imputed = False
        if pd.isna(a_start):
            is_imputed = False
        else:
            # compare as dates
            match_found = any((pd.Timestamp(a_start).normalize() == ds.normalize()) for ds in parsed_starts)
            if not match_found:
                is_imputed = True
        if is_imputed:
            imputed_projects.append(pid)
            # compute plausibility metrics
            planned_start = prow['planned_start_ts']
            planned_end = prow['planned_end_ts']
            planned_dur = float(prow['planned_duration_days']) if prow['planned_duration_days'] not in (None, '', 'nan') else None
            elapsed_days = float(prow['elapsed_days']) if prow['elapsed_days'] not in (None, '', 'nan') else None
            delay_days = float(prow['delay_days']) if prow['delay_days'] not in (None, '', 'nan') else None
            # differences
            diff_actualstart_plannedstart = None
            diff_actualstart_plannedend = None
            if not pd.isna(a_start) and not pd.isna(planned_start):
                diff_actualstart_plannedstart = (pd.Timestamp(a_start) - pd.Timestamp(planned_start)).days
            if not pd.isna(a_start) and not pd.isna(planned_end):
                diff_actualstart_plannedend = (pd.Timestamp(a_start) - pd.Timestamp(planned_end)).days
            details.append({
                'project_id': pid,
                'actual_start': str(a_start),
                'actual_end': str(a_end),
                'planned_start': str(planned_start),
                'planned_end': str(planned_end),
                'planned_duration_days': prow.get('planned_duration_days'),
                'elapsed_days': prow.get('elapsed_days'),
                'delay_days': prow.get('delay_days'),
                'diff_actualstart_plannedstart_days': diff_actualstart_plannedstart,
                'diff_actualstart_plannedend_days': diff_actualstart_plannedend,
                'parsed_actual_start_candidates_count': len(parsed_starts)
            })

    # extract row-level rows for imputed projects
    sample_rows = rows[rows['project_id'].isin(imputed_projects)].copy()
    # merge aggregated fields
    sample_rows = sample_rows.merge(agg[['project_id','planned_start','planned_end','actual_start','actual_end','planned_duration_days','elapsed_days','delay_days']], on='project_id', how='left')

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    sample_rows.to_csv(OUT_CSV, index=False)

    # write summary
    lines = []
    lines.append(f'imputed_projects_count: {len(imputed_projects)}')
    lines.append('project_id, parsed_actual_start_candidates_count, actual_start, actual_end, planned_start, planned_end, planned_duration_days, elapsed_days, delay_days, diff_actualstart_plannedstart_days, diff_actualstart_plannedend_days')
    for d in details:
        lines.append(','.join([str(d[k]) for k in ['project_id','parsed_actual_start_candidates_count','actual_start','actual_end','planned_start','planned_end','planned_duration_days','elapsed_days','delay_days','diff_actualstart_plannedstart_days','diff_actualstart_plannedend_days']]))

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('\n'.join(lines[:20]))
    print('\nWrote sample CSV to', OUT_CSV)
    print('Wrote summary to', OUT_SUM)


if __name__ == '__main__':
    main()
