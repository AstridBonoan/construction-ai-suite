import re
import pandas as pd

df = pd.read_csv("data_splits/project_dataset_v7_cleaned.csv", dtype=str)
date_re = re.compile(r"^\s*\d{1,2}/\d{1,2}/\d{4}\s*$")
res = []
for c in df.columns:
    col = df[c].astype(str)
    match_count = col.apply(lambda x: 1 if date_re.match(x) else 0).sum()
    if match_count > 0:
        res.append((c, int(match_count)))

res_sorted = sorted(res, key=lambda x: -x[1])
print("Columns with date-like strings (top 30):")
for c, n in res_sorted[:30]:
    print(f"{c}: {n}")
