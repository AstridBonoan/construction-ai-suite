#!/usr/bin/env python3
import pandas as pd
import os

AGG = 'data_splits/project_level_aggregated_v8.csv'
ROWS = 'data_splits/project_dataset_v7_cleaned.csv'
OUT_CSV = 'data_splits/v8/numeric_project_samples.csv'
OUT_SUM = 'data_splits/v8/numeric_project_samples_summary.txt'

DATE_COL_SUBSTR = ['year','permit','complt','complete','filed','start','end','date']


def main():
    agg = pd.read_csv(AGG, dtype=str)
    # find projects with numeric planned_duration or delay
    agg_num = agg[pd.to_numeric(agg.get('planned_duration_days', pd.Series()), errors='coerce').notna() |
                  pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce').notna()]
    project_ids = agg_num['project_id'].dropna().unique().tolist()

    if len(project_ids) == 0:
        print('No projects with numeric durations found.')
        return

    rows = pd.read_csv(ROWS, dtype=str)
    # filter rows for these projects
    sample_rows = rows[rows['project_id'].isin(project_ids)].copy()

    # select date-like columns plus project_id and a few extras
    extras = [c for c in rows.columns if any(sub in c.lower() for sub in DATE_COL_SUBSTR)]
    select_cols = ['project_id'] + extras
    select_cols = [c for c in select_cols if c in sample_rows.columns]

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    sample_rows.to_csv(OUT_CSV, index=False)

    # write a short summary
    lines = []
    lines.append(f'Projects extracted: {len(project_ids)}')
    lines.append('Project IDs:')
    for pid in project_ids:
        lines.append(f' - {pid}')
    lines.append('')
    lines.append('Date-like columns included:')
    for c in select_cols:
        lines.append(f' - {c}')
    lines.append('')
    lines.append('Head of sample rows (first 20 rows):')
    lines.append(sample_rows[select_cols].head(20).to_string(index=False))

    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('\n'.join(lines))
    print('\nWrote sample CSV to', OUT_CSV)
    print('Wrote summary to', OUT_SUM)


if __name__ == '__main__':
    main()
