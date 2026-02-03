import pandas as pd

df = pd.read_csv("data_splits/project_level_aggregated_v7.csv", dtype=str)
cols = ["planned_duration_days", "elapsed_days", "schedule_slippage_pct", "delay_days"]
for c in cols:
    if c in df:
        nonempty = (
            df[c].apply(lambda x: 1 if x not in (None, "", "nan", "NaN") else 0).sum()
        )
        print(f"{c}: present=True non-empty-string-count={nonempty}")
    else:
        print(f"{c}: present=False")

for c in ["planned_duration_days", "elapsed_days", "delay_days"]:
    if c in df:
        num = pd.to_numeric(df[c], errors="coerce")
        print(f"{c} numeric non-NaN: {int(num.notna().sum())}")
    else:
        print(f"{c} missing")
