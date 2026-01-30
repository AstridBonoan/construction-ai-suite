#!/usr/bin/env python3
"""Leakage diagnostics for Baseline v3.

Loads the saved model and training splits, computes feature importances (if
available) and per-feature correlation with the target, and writes diagnostic
outputs to analysis_outputs/v3/
"""
from __future__ import annotations
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path('.')
OUT = ROOT / 'analysis_outputs' / 'v3'
OUT.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ROOT / 'models' / 'v3' / 'baseline_project_delay_model_v3.pkl'
X_TRAIN_PATH = ROOT / 'data_splits' / 'v3' / 'X_train.csv'
Y_TRAIN_PATH = ROOT / 'data_splits' / 'v3' / 'y_train.csv'

if not MODEL_PATH.exists():
    print('Missing model:', MODEL_PATH)
    sys.exit(2)
if not X_TRAIN_PATH.exists() or not Y_TRAIN_PATH.exists():
    print('Missing training splits:', X_TRAIN_PATH, Y_TRAIN_PATH)
    sys.exit(3)

print('Loading model...')
model = joblib.load(MODEL_PATH)
print('Loading training data...')
X_train = pd.read_csv(X_TRAIN_PATH, low_memory=False)
y_train = pd.read_csv(Y_TRAIN_PATH, low_memory=False)
if y_train.shape[1] == 1:
    y = y_train.iloc[:, 0]
else:
    if 'will_delay' in y_train.columns:
        y = y_train['will_delay']
    else:
        y = y_train.iloc[:, 0]

# Compute per-original-feature Pearson correlation (numeric columns only)
num_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
correlations = []
for c in X_train.columns:
    try:
        if c in num_cols:
            corr = float(X_train[c].corr(y))
        else:
            corr = float('nan')
    except Exception:
        corr = float('nan')
    correlations.append((c, corr))

corr_df = pd.DataFrame(correlations, columns=['feature', 'corr_with_will_delay']).set_index('feature')
corr_df['abs_corr'] = corr_df['corr_with_will_delay'].abs()

# Try to extract feature importances from the model
importances = None
feature_names = None
try:
    if hasattr(model, 'feature_importances_'):
        importances = np.asarray(model.feature_importances_)
        # best-effort feature names: use X_train columns if lengths match
        if len(importances) == X_train.shape[1]:
            feature_names = list(X_train.columns)
    elif hasattr(model, 'named_steps'):
        # Pipeline: find the final estimator
        last_step = list(model.named_steps.items())[-1][1]
        if hasattr(last_step, 'feature_importances_'):
            importances = np.asarray(last_step.feature_importances_)
            # attempt to get feature names from preprocessor
            try:
                preproc = None
                for n, step in model.named_steps.items():
                    from sklearn.compose import ColumnTransformer
                    if isinstance(step, ColumnTransformer):
                        preproc = step
                        break
                    # common name
                    if n.lower() in ('preprocessor', 'transformer', 'columntransformer') and isinstance(step, ColumnTransformer):
                        preproc = step
                        break
                if preproc is not None:
                    # sklearn >=1.0 supports get_feature_names_out
                    try:
                        feature_names = list(preproc.get_feature_names_out(X_train.columns))
                    except Exception:
                        # fallback: use original columns
                        feature_names = list(X_train.columns)
                else:
                    feature_names = list(X_train.columns)
            except Exception:
                feature_names = list(X_train.columns)
    else:
        importances = None
except Exception:
    importances = None

if importances is not None:
    imp_df = pd.DataFrame({'feature_out': feature_names if feature_names is not None else [f'F{i}' for i in range(len(importances))], 'importance': importances})
else:
    imp_df = pd.DataFrame(columns=['feature_out', 'importance'])

# Merge / produce diagnostics
# We will map importances to original features if lengths match; otherwise, keep separate
if not imp_df.empty and list(imp_df['feature_out']) == list(X_train.columns):
    diag = imp_df.set_index('feature_out').join(corr_df, how='outer')
    diag.index.name = 'feature'
else:
    # importances may be on transformed features; keep them separately and merge correlations for original features
    corr_df_reset = corr_df.reset_index()
    imp_df_reset = imp_df.copy()
    # write a CSV with both sections
    corr_df.reset_index().to_csv(OUT / 'leakage_correlations.csv', index=False)
    imp_df.to_csv(OUT / 'leakage_importances_transformed.csv', index=False)
    # produce a combined placeholder
    diag = corr_df.copy()
    diag['importance'] = float('nan')

# Save combined diagnostics
diag_out = OUT / 'leakage_diagnostics.csv'
diag.reset_index().to_csv(diag_out, index=False)
print('Wrote diagnostics CSV to', diag_out)

# Write summary text
summary = []
# top correlations
top_corr = corr_df.sort_values('abs_corr', ascending=False).head(20)
summary.append('Top correlated original features (by abs correlation with will_delay):')
for f, row in top_corr.iterrows():
    summary.append(f" - {f}: corr={row['corr_with_will_delay']:.4f}")

# top importances if available
if not imp_df.empty:
    top_imp = imp_df.sort_values('importance', ascending=False).head(20)
    summary.append('\nTop feature importances (transformed features):')
    for _, row in top_imp.iterrows():
        summary.append(f" - {row['feature_out']}: importance={row['importance']:.6f}")

# suspicious features by threshold
sus_corr = corr_df[corr_df['abs_corr'] >= 0.9].sort_values('abs_corr', ascending=False)
if not sus_corr.empty:
    summary.append('\nSuspiciously highly correlated features (abs corr >= 0.9):')
    for f, r in sus_corr.iterrows():
        summary.append(f" - {f}: corr={r['corr_with_will_delay']:.6f}")
else:
    summary.append('\nNo features exceed abs(corr) >= 0.9 threshold on original features.')

with open(OUT / 'leakage_diagnostics.txt', 'w') as fh:
    fh.write('\n'.join(summary))

print('Wrote summary to', OUT / 'leakage_diagnostics.txt')

# Optional plot: top correlated features bar chart
try:
    top_plot = corr_df.sort_values('abs_corr', ascending=False).head(30).reset_index()
    plt.figure(figsize=(8, 8))
    sns.barplot(data=top_plot, x='abs_corr', y='feature', palette='viridis')
    plt.xlabel('Absolute correlation with will_delay')
    plt.title('Top correlated original features')
    plt.tight_layout()
    pplot = OUT / 'top_correlated_features.png'
    plt.savefig(pplot)
    plt.close()
    print('Saved plot to', pplot)
except Exception as e:
    print('Could not create plot:', e)

print('\nDone')
