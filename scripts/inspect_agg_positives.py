import pandas as pd

df = pd.read_csv("data_splits/project_level_aggregated_v7.csv", low_memory=False)
sel = df[pd.to_numeric(df["schedule_slippage_pct"], errors="coerce") > 0.05]
print("positives =", len(sel))
if len(sel) > 0:
    pd.set_option("display.max_columns", None)
    print(sel.head().to_string())
