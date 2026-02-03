from pathlib import Path
import pandas as pd
import numpy as np

RELAXED = Path(".") / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
if not RELAXED.exists():
    raise FileNotFoundError(RELAXED)

df = pd.read_csv(RELAXED, dtype=str)
df["planned_duration_days"] = pd.to_numeric(
    df.get("planned_duration_days"), errors="coerce"
)
vals = df["planned_duration_days"].dropna()
vals = vals[vals > 0]
print("Total rows with planned_duration_days > 0:", len(vals))
if len(vals) > 0:
    med = float(vals.median())
    print("Median:", med)
    pct = np.percentile(vals, [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100])
    print(
        "Percentiles (0,1,5,10,25,50,75,90,95,99,100):",
        ", ".join([f"{p:.2f}" for p in pct]),
    )
    print("\nTop value counts:")
    print(vals.value_counts().head(20).to_string())
else:
    print("No valid planned_duration_days > 0 found in relaxed file.")
