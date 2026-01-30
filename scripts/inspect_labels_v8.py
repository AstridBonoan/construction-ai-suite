import pandas as pd
import numpy as np
p='data_splits/project_level_aggregated_v8.csv'
# parse possible date cols as strings then to_datetime for robustness
df=pd.read_csv(p)
for c in ['planned_start','planned_end','actual_start','actual_end']:
    if c in df.columns:
        df[c]=pd.to_datetime(df[c], errors='coerce')
cols=['planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct']
print('rows',len(df))
for c in cols:
    nonna=df[c].notna().sum()
    print(f'{c}_non_na={nonna}')
# counts of positive delays
pos_delay=(pd.to_numeric(df['delay_days'], errors='coerce')>0).sum()
pos_slip=(pd.to_numeric(df['schedule_slippage_pct'], errors='coerce')>0.05).sum()
print('delay_days>0 positives=',int(pos_delay))
print('schedule_slippage_pct>0.05 positives=',int(pos_slip))
# ranges
for c in cols:
    ser=pd.to_numeric(df[c], errors='coerce')
    print(c, 'min', ser.min(), 'median', ser.median(), 'max', ser.max())
# show sample rows where delay_days>0 or schedule_slippage_pct>0.05
mask=(pd.to_numeric(df['delay_days'], errors='coerce')>0) | (pd.to_numeric(df['schedule_slippage_pct'], errors='coerce')>0.05)
s=df.loc[mask, ['project_id','planned_start','planned_end','actual_start','actual_end','actual_start_imputed','planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct','will_delay']]
print('\nPositive mask rows count',len(s))
if len(s)>0:
    print(s.head(10).to_string(index=False))
else:
    print('No positive rows by these criteria')
# show some examples where actual_start_imputed is True
if 'actual_start_imputed' in df.columns:
    imp=df[df['actual_start_imputed'].astype(str).str.lower().isin(['true','1','yes'])][['project_id','planned_start','planned_end','actual_start','actual_end','planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct']]
    print('\nImputed count',len(imp))
    print(imp.head(10).to_string(index=False))
else:
    print('\nNo actual_start_imputed column')

# show will_delay distribution
if 'will_delay' in df.columns:
    print('\nwill_delay counts:')
    print(df['will_delay'].value_counts(dropna=False).to_string())
else:
    print('\nwill_delay not present')
