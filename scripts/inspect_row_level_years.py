#!/usr/bin/env python3
import pandas as pd
import re
import json
from collections import Counter

INPUT = 'data_splits/project_dataset_v7_cleaned.csv'
OUT = 'data_splits/v8/row_level_year_inspection.txt'

DATE_PATTERNS = [
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"),
    re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"),
    re.compile(r"^\d{4}/\d{1,2}/\d{1,2}$"),
]
FOCUS_SUBSTR = ['year','permit','complt','complete','filed','start','end']
YEAR_RE = re.compile(r'^\d{4}$')


def is_full_date(s: str):
    if not s or pd.isna(s):
        return False
    s = str(s).strip()
    for p in DATE_PATTERNS:
        if p.search(s):
            return True
    return False


def pct(n, total):
    return 0.0 if total == 0 else round(100.0 * n / total, 2)


def main():
    df = pd.read_csv(INPUT, dtype=str)
    total_rows = len(df)

    # find candidate columns
    cols = df.columns.tolist()
    candidate_cols = []
    for c in cols:
        lc = c.lower()
        if any(sub in lc for sub in FOCUS_SUBSTR):
            candidate_cols.append(c)
    # ensure PermitYear/CompltYear included if present
    for special in ['PermitYear', 'CompltYear']:
        if special in df.columns and special not in candidate_cols:
            candidate_cols.append(special)

    report_lines = []
    report_lines.append(f'Input rows: {INPUT}')
    report_lines.append(f'total_rows: {total_rows}')
    report_lines.append('')
    report_lines.append('Identified candidate columns:')
    for c in candidate_cols:
        report_lines.append(f' - {c}')
    report_lines.append('')

    # analyze each column
    col_summaries = {}
    for c in candidate_cols:
        series = df[c].fillna('').astype(str).str.strip()
        non_null_mask = series.str.len() > 0
        non_null_count = int(non_null_mask.sum())
        total = total_rows
        samples = list(series[non_null_mask].unique()[:20])
        year_only_count = int(series.str.match(YEAR_RE).sum())
        full_date_count = int(series.apply(lambda v: is_full_date(v)).sum())
        col_summaries[c] = {
            'dtype': str(df[c].dtype),
            'non_null_count': non_null_count,
            'non_null_pct': pct(non_null_count, total),
            'year_only_count': year_only_count,
            'year_only_pct': pct(year_only_count, total),
            'full_date_count': full_date_count,
            'full_date_pct': pct(full_date_count, total),
            'samples': samples,
        }
        report_lines.append(f'Column: {c}')
        report_lines.append(f'  dtype: {df[c].dtype}')
        report_lines.append(f'  non_null: {non_null_count} ({pct(non_null_count,total)}%)')
        report_lines.append(f'  year_only (####): {year_only_count} ({pct(year_only_count,total)}%)')
        report_lines.append(f'  full_date matches: {full_date_count} ({pct(full_date_count,total)}%)')
        report_lines.append(f'  samples (up to 20 non-null unique): {samples}')
        report_lines.append('')

    # group by project_id counts for PermitYear and CompltYear
    key = 'project_id' if 'project_id' in df.columns else df.columns[0]
    report_lines.append(f'Grouping by project key: {key}')

    grp = df.groupby(key)

    def per_project_counts(colname):
        # count rows per project where col is non-empty
        return grp[colname].apply(lambda s: s.fillna('').astype(str).str.strip().ne('').sum())

    counts = {}
    for special in ['PermitYear','CompltYear']:
        if special in df.columns:
            pc = per_project_counts(special)
            counts[special] = {
                'projects_with_at_least_one': int((pc>0).sum()),
                'projects_with_count_distribution': pc.value_counts().to_dict(),
                'per_project_counts_series': pc
            }
            report_lines.append(f"{special}: projects with >=1: {counts[special]['projects_with_at_least_one']} of {len(pc)}")
        else:
            report_lines.append(f"{special}: NOT PRESENT in dataset")
    report_lines.append('')

    # pick 5 example projects showing all available year/date fields side-by-side
    # choose projects with most non-null candidate fields
    def project_date_score(group):
        s = 0
        for c in candidate_cols:
            s += group[c].fillna('').astype(str).str.strip().ne('').sum()
        return s

    scores = grp.apply(project_date_score)
    top_projects = scores.sort_values(ascending=False).head(5).index.tolist()

    report_lines.append('Top 5 example projects (project_id) with most date-like fields:')
    report_lines.append(str(top_projects))
    report_lines.append('')

    # For each project, show first non-null per candidate col
    for pid in top_projects:
        report_lines.append(f'Project: {pid}')
        sub = grp.get_group(pid)
        for c in candidate_cols:
            vals = sub[c].fillna('').astype(str).str.strip()
            vals = vals[vals!='']
            report_lines.append(f'  {c}: {vals.iloc[0] if len(vals)>0 else "(empty)"}')
        report_lines.append('')

    # write out
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))

    print('\n'.join(report_lines))
    print('\nWrote inspection report to', OUT)


if __name__ == '__main__':
    main()
