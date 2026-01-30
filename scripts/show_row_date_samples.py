import pandas as pd

df = pd.read_csv('data_splits/project_dataset_v7_cleaned.csv', dtype=str)
cols = ['Project Phase Actual Start Date','Project Phase Planned End Date','Project Phase Actual End Date']
for c in cols:
    print('\n==', c)
    vals = df[c].fillna('NULL').astype(str)
    for i,v in enumerate(vals.head(20)):
        print(i, repr(v))
