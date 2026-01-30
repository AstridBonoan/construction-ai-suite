"""Generate per-project diagnostics CSV from aggregated v8 Rule A output.

Writes:
- data_splits/project_level_per_project_diagnostics_v8.csv
- data_splits/v8/project_level_per_project_diagnostics_v8_summary.txt

Preserves parse-fallback logging (does not modify it).
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path('.')
IN_AGG = ROOT / 'data_splits' / 'project_level_aggregated_v8_ruleA.csv'
OUT_CSV = ROOT / 'data_splits' / 'project_level_per_project_diagnostics_v8.csv'
OUT_SUM = ROOT / 'data_splits' / 'v8' / 'project_level_per_project_diagnostics_v8_summary.txt'


def main():
    if not IN_AGG.exists():
        raise FileNotFoundError(f"Aggregated input not found: {IN_AGG}")

    agg = pd.read_csv(IN_AGG, dtype=str)

    cols = [
        'project_id', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
        'actual_start_imputed', 'imputation_rule', 'planned_duration_days',
        'elapsed_days', 'delay_days', 'schedule_slippage_pct'
    ]

    # Ensure columns present
    for c in cols:
        if c not in agg.columns:
            agg[c] = np.nan

    # Convert numeric columns
    for ncol in ['planned_duration_days', 'elapsed_days', 'delay_days', 'schedule_slippage_pct']:
        agg[ncol] = pd.to_numeric(agg.get(ncol, pd.Series([])), errors='coerce')

    # Normalize imputed flag
    agg['actual_start_imputed'] = agg['actual_start_imputed'].astype(str).fillna('False')

    out = agg[cols].copy()

    # write diagnostics CSV
    out.to_csv(OUT_CSV, index=False)

    # summary
    total = len(out)
    by_rule = out['imputation_rule'].fillna('none').value_counts(dropna=False).to_dict()
    computable = int(out['delay_days'].notna().sum())
    not_computable = total - computable

    with OUT_SUM.open('w', encoding='utf-8') as f:
        f.write(f'total_projects={total}\n')
        f.write('counts_by_imputation_rule:\n')
        for k, v in by_rule.items():
            f.write(f'  {k}={v}\n')
        f.write(f'projects_with_numeric_delay={computable}\n')
        f.write(f'projects_with_missing_delay={not_computable}\n')

    print('Wrote diagnostics CSV to', OUT_CSV)
    print('Wrote summary to', OUT_SUM)


if __name__ == '__main__':
    main()
