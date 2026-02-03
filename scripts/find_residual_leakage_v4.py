#!/usr/bin/env python3
"""Find residual leakage candidates in v4 training data.

Writes:
- analysis_outputs/v4/residual_leakage_candidates.csv
- analysis_outputs/v4/residual_leakage_candidates.txt
- analysis_outputs/v4/residual_leakage_heatmap.png (optional)
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import json

# Optional plotting dependencies
try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    HAVE_PLOT = True
except Exception:
    HAVE_PLOT = False

ROOT = Path(".")
OUT = ROOT / "analysis_outputs" / "v4"
OUT.mkdir(parents=True, exist_ok=True)
X_PATH = ROOT / "data_splits" / "v4" / "X_train.csv"
Y_PATH = ROOT / "data_splits" / "v4" / "y_train.csv"
CSV_OUT = OUT / "residual_leakage_candidates.csv"
TXT_OUT = OUT / "residual_leakage_candidates.txt"
HEATMAP = OUT / "residual_leakage_heatmap.png"

if not X_PATH.exists() or not Y_PATH.exists():
    print("Missing v4 splits:", X_PATH, Y_PATH)
    raise SystemExit(2)

print("Loading X_train and y_train...")
X = pd.read_csv(X_PATH, low_memory=False)
y = pd.read_csv(Y_PATH, low_memory=False)
if isinstance(y, pd.DataFrame) and y.shape[1] == 1:
    y_ser = y.iloc[:, 0]
else:
    if "will_delay" in y.columns:
        y_ser = y["will_delay"]
    else:
        y_ser = y.iloc[:, 0]

patterns = [
    "slippage",
    "schedule",
    "target",
    "date",
    "start",
    "end",
    "actual",
    "planned",
    "id",
    "project",
    "phase",
]
pattern_matches = []
for c in X.columns:
    low = c.lower()
    matched = [p for p in patterns if p in low]
    if matched:
        pattern_matches.append((c, matched))

rows = []
print("Scanning columns...")
for c in X.columns:
    info = {
        "feature": c,
        "matches": "",
        "dtype": str(X[c].dtype),
        "n_unique": int(X[c].nunique(dropna=False)),
    }
    low = c.lower()
    matched = [p for p in patterns if p in low]
    info["matches"] = ";".join(matched)
    # try numeric correlation
    corr = np.nan
    try:
        series = X[c]
        # coerce numeric if possible
        if pd.api.types.is_numeric_dtype(series):
            corr = float(series.corr(y_ser))
        else:
            coerced = pd.to_numeric(series, errors="coerce")
            if coerced.notna().sum() > 0:
                corr = float(coerced.corr(y_ser))
    except Exception:
        corr = np.nan
    info["corr_with_target"] = corr
    info["abs_corr"] = abs(corr) if not np.isnan(corr) else np.nan
    # check perfect equality (after coercion)
    is_perfect = False
    try:
        s = X[c]
        # compare as strings for exact match
        if len(s) == len(y_ser):
            # align shapes
            cmp = s.fillna("").astype(str) == y_ser.fillna("").astype(str)
            if cmp.all():
                is_perfect = True
        # numeric exact match
        try:
            s_num = pd.to_numeric(s, errors="coerce")
            y_num = pd.to_numeric(y_ser, errors="coerce")
            if not s_num.isna().all() and not y_num.isna().all():
                if (
                    s_num.dropna()
                    .reset_index(drop=True)
                    .equals(y_num.dropna().reset_index(drop=True))
                ):
                    is_perfect = True
        except Exception:
            pass
    except Exception:
        is_perfect = False
    info["perfect_predictor"] = bool(is_perfect)
    rows.append(info)

res_df = pd.DataFrame(rows)
# candidates: pattern match OR perfect predictor OR abs_corr >= 0.9
candidates = res_df[
    (res_df["matches"] != "")
    | (res_df["perfect_predictor"])
    | (res_df["abs_corr"] >= 0.9)
].copy()

candidates.to_csv(CSV_OUT, index=False)

with open(TXT_OUT, "w", encoding="utf8") as fh:
    fh.write("Residual leakage candidates scan\n")
    fh.write(f"Total columns scanned: {len(res_df)}\n")
    fh.write("\nCandidates (pattern match OR perfect predictor OR abs_corr>=0.9):\n")
    for _, r in candidates.iterrows():
        fh.write(
            f"- {r['feature']}: matches={r['matches']}, dtype={r['dtype']}, n_unique={r['n_unique']}, abs_corr={r['abs_corr']}, perfect={r['perfect_predictor']}\n"
        )
    fh.write("\nSummary stats:\n")
    fh.write(res_df.describe(include="all").to_string())

if HAVE_PLOT:
    try:
        num_candidates = [
            f
            for f in candidates["feature"].tolist()
            if pd.api.types.is_numeric_dtype(X[f])
        ]
        if num_candidates:
            corr_mat = X[num_candidates].apply(pd.to_numeric, errors="coerce").corr()
            plt.figure(figsize=(8, max(4, len(num_candidates) * 0.25)))
            sns.heatmap(corr_mat, cmap="vlag", center=0)
            plt.title("Correlation matrix among numeric candidate features")
            plt.tight_layout()
            plt.savefig(HEATMAP)
            plt.close()
    except Exception:
        pass

print("Wrote", CSV_OUT, TXT_OUT)
print("Done")
