"""Select a small sample of RuleA-imputed projects and write CSV + summary.

Outputs:
- data_splits/project_level_ruleA_sample_v8.csv
- data_splits/v8/project_level_ruleA_sample_v8_summary.txt
"""
from pathlib import Path
import pandas as pd

ROOT = Path('.')
IN = ROOT / 'data_splits' / 'project_level_per_project_diagnostics_v8.csv'
OUT_CSV = ROOT / 'data_splits' / 'project_level_ruleA_sample_v8.csv'
OUT_SUM = ROOT / 'data_splits' / 'v8' / 'project_level_ruleA_sample_v8_summary.txt'


def main():
    df = pd.read_csv(IN, dtype=str)
    # filter RuleA
    df['imputation_rule'] = df.get('imputation_rule', '').fillna('')
    ruleA = df.loc[df['imputation_rule'] == 'RuleA'].copy()
    sample = ruleA.head(10).copy()

    cols = ['project_id', 'planned_start', 'planned_end', 'actual_start', 'actual_end',
            'actual_start_imputed', 'planned_duration_days', 'elapsed_days', 'delay_days']
    for c in cols:
        if c not in sample.columns:
            sample[c] = ''

    # Detect issues
    issues = []
    for _, r in sample.iterrows():
        iss = []
        ps = str(r.get('planned_start') or '')
        pe = str(r.get('planned_end') or '')
        acs = str(r.get('actual_start') or '')
        ace = str(r.get('actual_end') or '')
        if ps == pe or ps.strip() == '' or pe.strip() == '':
            iss.append('planned_collapsed_or_missing')
        if acs.strip() == '' or acs.lower() == 'nan':
            iss.append('actual_start_missing')
        if ace.strip() == '' or ace.lower() == 'nan':
            iss.append('actual_end_missing')
        issues.append(';'.join(iss) if iss else 'ok')

    sample['issues'] = issues
    sample.to_csv(OUT_CSV, index=False)

    # summary
    total_sample = len(sample)
    collapsed = int((sample['planned_start'] == sample['planned_end']).sum())
    missing_actual_start = int(sample['actual_start'].isna().sum() if 'actual_start' in sample.columns else sum(1 for v in sample['actual_start'] if str(v).strip()=='')).__int__()
    missing_actual_end = int(sample['actual_end'].isna().sum() if 'actual_end' in sample.columns else sum(1 for v in sample['actual_end'] if str(v).strip()=='')).__int__()

    with OUT_SUM.open('w', encoding='utf-8') as f:
        f.write(f'total_ruleA_in_sample={total_sample}\n')
        f.write(f'planned_collapsed_in_sample={collapsed}\n')
        f.write(f'missing_actual_start_in_sample={missing_actual_start}\n')
        f.write(f'missing_actual_end_in_sample={missing_actual_end}\n')
        f.write('\nDetailed issues per project in CSV.\n')

    print('Wrote sample CSV to', OUT_CSV)
    print('Wrote summary to', OUT_SUM)


if __name__ == '__main__':
    main()
