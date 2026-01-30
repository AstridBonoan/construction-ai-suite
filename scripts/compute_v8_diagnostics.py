#!/usr/bin/env python3
import pandas as pd
import json
import os

agg_path = 'data_splits/project_level_aggregated_v8.csv'
fallbacks_path = 'data_splits/v8/parse_fallbacks.json'
out_path = 'data_splits/v8/diagnostics.txt'

agg = pd.read_csv(agg_path)
with open(fallbacks_path, 'r') as f:
    fallbacks = json.load(f)

# totals
total_projects = len(agg)
planned_non_na = int(pd.to_numeric(agg.get('planned_duration_days', pd.Series()), errors='coerce').notna().sum())
elapsed_non_na = int(pd.to_numeric(agg.get('elapsed_days', pd.Series()), errors='coerce').notna().sum())
delay_non_na = int(pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce').notna().sum())

# positives
delay_pos = int((pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce') > 0).sum())
slip_pos = int((pd.to_numeric(agg.get('schedule_slippage_pct', pd.Series()), errors='coerce') > 0).sum())

# parse fallbacks summary
projects_using_year = sum(1 for r in fallbacks if r.get('year_only_parse'))
projects_using_any = sum(1 for r in fallbacks if any(len(v) > 0 for v in r.get('used', {}).values()))
projects_failed_all = sum(1 for r in fallbacks if not any(len(v) > 0 for v in r.get('used', {}).values()) and not r.get('year_only_parse'))
imputed_actual_start = sum(1 for r in fallbacks if r.get('actual_start_imputed'))

# sample numeric rows
num_rows = agg[pd.to_numeric(agg.get('delay_days', pd.Series()), errors='coerce').notna()]
sample = num_rows.head(5)

lines = []
lines.append(f'total_projects={total_projects}')
lines.append(f'planned_duration_days_non_na={planned_non_na}')
lines.append(f'elapsed_days_non_na={elapsed_non_na}')
lines.append(f'delay_days_non_na={delay_non_na}')
lines.append('')
lines.append(f'delay_days>0 positives={delay_pos}')
lines.append(f'schedule_slippage_pct>0 positives={slip_pos}')
lines.append('')
lines.append(f'projects_using_year_only={projects_using_year}')
lines.append(f'projects_using_any_parsed_dates={projects_using_any}')
lines.append(f'projects_failed_all_parsing={projects_failed_all}')
lines.append(f'projects_with_imputed_actual_start={imputed_actual_start}')
lines.append('')
lines.append('Sample numeric rows (up to 5):')
if not sample.empty:
    lines.append(sample[['project_id','planned_start','planned_end','actual_start','actual_end','planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct']].to_string(index=False))
else:
    lines.append('  (no numeric duration rows)')

# write out
with open(out_path, 'w') as f:
    f.write('\n'.join(lines))

print('\n'.join(lines))
print('\nWrote diagnostics to', out_path)
