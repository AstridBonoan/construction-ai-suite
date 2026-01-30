import pandas as pd

df = pd.read_csv('data_splits/project_level_aggregated_v7.csv', dtype=str)
for col in ['planned_duration_days','elapsed_days','schedule_slippage_pct','delay_days']:
    print('\n==', col)
    if col in df:
        vals = df[col].fillna('NULL').astype(str)
        unique = vals.unique()[:30]
        for i,v in enumerate(unique[:30]):
            print(i, repr(v))
    else:
        print('missing')
