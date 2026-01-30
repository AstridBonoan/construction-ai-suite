#!/usr/bin/env python3
"""Identify top suspicious features for Baseline v3.

- Loads X_train and y_train
- Computes numeric correlations and constant columns
- Flags features with abs(corr) >= 0.9 and constant/near-constant
- Writes CSV and TXT summaries to analysis_outputs/v3/
"""
from __future__ import annotations
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd

ROOT = Path('.')
OUT = ROOT / 'analysis_outputs' / 'v3'
OUT.mkdir(parents=True, exist_ok=True)
X_TRAIN = ROOT / 'data_splits' / 'v3' / 'X_train.csv'
Y_TRAIN = ROOT / 'data_splits' / 'v3' / 'y_train.csv'
CSV_OUT = OUT / 'top_suspicious_features.csv'
TXT_OUT = OUT / 'top_suspicious_features.txt'

if not X_TRAIN.exists() or not Y_TRAIN.exists():
    print('Missing train splits')
    sys.exit(2)

X = pd.read_csv(X_TRAIN, low_memory=False)
y = pd.read_csv(Y_TRAIN, low_memory=False)
if y.shape[1] == 1:
    y_ser = y.iloc[:, 0]
else:
    if 'will_delay' in y.columns:
        y_ser = y['will_delay']
    else:
        y_ser = y.iloc[:, 0]

# Ensure numeric conversion where possible
num_cols = X.select_dtypes(include=[np.number]).columns.tolist()
# If a numeric-like column is stored as object, try to coerce
for c in X.columns:
    if c not in num_cols:
        try:
            coerced = pd.to_numeric(X[c], errors='coerce')
            if coerced.notna().sum() > 0:
                X[c] = coerced
                num_cols.append(c)
        except Exception:
            pass

rows = []
for c in X.columns:
    vals = X[c]
    is_constant = vals.nunique(dropna=False) <= 1
    try:
        if c in num_cols:
            corr = float(vals.astype(float).corr(y_ser.astype(float)))
        else:
            corr = float('nan')
    except Exception:
        corr = float('nan')
    rows.append({'feature': c, 'corr_with_will_delay': corr, 'abs_corr': (abs(corr) if not np.isnan(corr) else np.nan), 'is_constant': is_constant})

df = pd.DataFrame(rows)
# suspicious: abs_corr >= 0.9 or is_constant True or feature name suggests id/date
df['is_id_like'] = df['feature'].str.lower().str.contains('id|project|id\b|version|unnamed|date|time|timestamp')

sus = df[(df['abs_corr'] >= 0.9) | (df['is_constant']) | (df['is_id_like'])]
# sort with abs_corr desc first, then is_constant
sus = sus.sort_values(by=['abs_corr', 'is_constant'], ascending=[False, False])

# Save CSV and TXT
sus.to_csv(CSV_OUT, index=False)
with open(TXT_OUT, 'w') as fh:
    fh.write('Top suspicious features (abs_corr>=0.9 OR constant OR id-like)\n')
    fh.write(df.describe(include='all').to_string())
    fh.write('\n\n-- Suspicious features --\n')
    for _, r in sus.iterrows():
        fh.write(f"{r['feature']}: corr={r['corr_with_will_delay']}, abs_corr={r['abs_corr']}, constant={r['is_constant']}, id_like={r['is_id_like']}\n")

print('Wrote', CSV_OUT, TXT_OUT)
