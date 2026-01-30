import pandas as pd

df = pd.read_csv('data_splits/project_level_aggregated_v8.csv', dtype=str)
cols = ['Project Phase Planned End Date','Project Phase Actual Start Date','Project Phase Actual End Date','DateFiled','DatePermit','DateComplt','PermitYear','CompltYear']
for c in cols:
    if c in df.columns:
        cnt = df[c].dropna().astype(str).map(lambda s: s.strip()!='').sum()
        print(c, cnt)
    else:
        print(c, 'MISSING')

planned_candidates = ['PermitYear','DatePermit','Project Phase Planned End Date']
actual_candidates = ['Project Phase Actual Start Date','DateFiled','Project Phase Actual End Date','DateComplt','CompltYear']
planned_any = df[planned_candidates].fillna('').apply(lambda row: any([str(x).strip()!='' for x in row]), axis=1).sum()
actual_any = df[actual_candidates].fillna('').apply(lambda row: any([str(x).strip()!='' for x in row]), axis=1).sum()
print('projects_with_any_planned_candidate=', planned_any)
print('projects_with_any_actual_candidate=', actual_any)
