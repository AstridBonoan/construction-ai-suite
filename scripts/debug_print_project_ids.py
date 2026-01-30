import pandas as pd
agg = pd.read_csv('data_splits/project_level_aggregated_v8.csv', low_memory=False)
print('Total rows in agg:', len(agg))
print('First 12 project_id values:')
print(agg['project_id'].astype(str).head(12).tolist())
