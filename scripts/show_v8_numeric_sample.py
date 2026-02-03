import pandas as pd

df = pd.read_csv("data_splits/project_level_aggregated_v8.csv", dtype=str)
for col in [
    "planned_duration_days",
    "elapsed_days",
    "delay_days",
    "schedule_slippage_pct",
]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

numeric = df[df["planned_duration_days"].notna()]
if len(numeric) == 0:
    print("No numeric planned_duration_days rows")
else:
    cols = [
        "project_id",
        "planned_start",
        "planned_end",
        "actual_start",
        "actual_end",
        "planned_duration_days",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
    ]
    print(numeric[cols].head(5).to_string(index=False))
