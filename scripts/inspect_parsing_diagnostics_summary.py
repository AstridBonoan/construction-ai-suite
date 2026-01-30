import pandas as pd
import json
import os

AGG_PATH = os.path.join('data_splits', 'project_level_aggregated_v8.csv')
ROWS_PATH = os.path.join('data_splits', 'project_dataset_v7_cleaned.csv')
FALLBACKS_PATH = os.path.join('data_splits', 'v8', 'parse_fallbacks.json')
OUT_PATH = os.path.join('data_splits', 'v8', 'parsing_diagnostics_sample10_summary.txt')

COLS = [
    'planned_start','planned_end','actual_start','actual_end','actual_start_imputed',
    'planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct'
]

RAW_COLS = ['DateFiled','DatePermit','PermitYear','CompltYear']


def short(x, n=60):
    s = '' if pd.isna(x) else str(x)
    return s if len(s) <= n else s[: n-3] + '...'


def main(sample_size=10):
    agg = pd.read_csv(AGG_PATH, low_memory=False)
    rows = pd.read_csv(ROWS_PATH, low_memory=False, dtype=str)
    with open(FALLBACKS_PATH, 'r', encoding='utf-8') as f:
        fallbacks_list = json.load(f)
    if isinstance(fallbacks_list, dict):
        fallbacks_list = list(fallbacks_list.values())

    sample = fallbacks_list[:sample_size]

    lines = []
    header = '\t'.join(['project_id'] + COLS + RAW_COLS + ['parse_fallback_summary'])
    lines.append(header)

    for item in sample:
        pid = str(item.get('project_id'))
        agg_row = agg[agg['project_id'].astype(str) == pid]
        vals = [pid]
        for c in COLS:
            v = agg_row.iloc[0].get(c, '') if len(agg_row) > 0 else ''
            vals.append(short(v, 30))
        subset = rows[rows['project_id'].astype(str) == pid]
        for rc in RAW_COLS:
            vals.append(short(' | '.join(subset[rc].dropna().astype(str).unique()), 40))
        used = item.get('used', {})
        year_only = item.get('year_only_parse', [])
        imputed = item.get('actual_start_imputed', False)
        vals.append(f"used_keys={list(used.keys())}; year_only={year_only}; actual_start_imputed={imputed}")
        lines.append('\t'.join(vals))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Wrote summary to {OUT_PATH}")


if __name__ == '__main__':
    main()
