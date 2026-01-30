import pandas as pd

path = 'data_splits/project_dataset_v7_cleaned.csv'
df = pd.read_csv(path, dtype=str)
cols = ['Project Phase Actual Start Date','Project Phase Planned End Date','Project Phase Actual End Date']
for c in cols:
    if c in df:
        nonempty = df[c].apply(lambda x: 1 if x not in (None,'','nan','NaN') else 0).sum()
        print(f"{c}: non-empty rows = {nonempty} of {len(df)}")
    else:
        print(f"{c}: missing in cleaned rows")
