#!/usr/bin/env python3
"""Validate Baseline v5: recompute metrics, extract importances, check perfect predictors."""
from __future__ import annotations
from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path('.')
MODEL_PATH = ROOT / 'models' / 'v5' / 'baseline_project_delay_model_v5.pkl'
SPLITS = ROOT / 'data_splits' / 'v5'
OUT_DIR = ROOT / 'analysis_outputs' / 'v5'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_read_csv(p: Path):
    return pd.read_csv(p, low_memory=False)


def main():
    X_test = safe_read_csv(SPLITS / 'X_test.csv')
    y_test = safe_read_csv(SPLITS / 'y_test.csv')
    if isinstance(y_test, pd.DataFrame) and y_test.shape[1] == 1:
        y_test = y_test.iloc[:, 0]

    model = joblib.load(MODEL_PATH)

    # Predict with full pipeline if possible
    try:
        preds = model.predict(X_test)
    except Exception:
        # try to use named steps
        try:
            pre = model.named_steps['pre']
            rf = model.named_steps['rf']
            X_test_pre = pre.transform(X_test)
            try:
                if hasattr(X_test_pre, 'toarray'):
                    X_test_pre = X_test_pre.toarray()
            except Exception:
                pass
            preds = rf.predict(X_test_pre)
        except Exception as e:
            raise

    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
    r2 = float(r2_score(y_test, preds))

    report_lines = []
    report_lines.append('Recomputed metrics:')
    report_lines.append(f' - MAE: {mae}')
    report_lines.append(f' - RMSE: {rmse}')
    report_lines.append(f' - R2: {r2}')

    # Feature importances
    fi_path = OUT_DIR / 'feature_importances_v5.csv'
    try:
        rf = model.named_steps['rf']
        pre = model.named_steps['pre']
        importances = rf.feature_importances_
        # try to get feature names
        try:
            feat_names = pre.get_feature_names_out()
        except Exception:
            try:
                feat_names = pre.get_feature_names_out(X_test.columns)
            except Exception:
                # fallback to raw column names (best-effort)
                feat_names = list(X_test.columns)

        # align lengths
        if len(feat_names) != len(importances):
            # align by using indices
            feat_names = [f'ft_{i}' for i in range(len(importances))]

        df_fi = pd.DataFrame({'feature': feat_names, 'importance': importances})
        df_fi = df_fi.sort_values('importance', ascending=False)
        df_fi.to_csv(fi_path, index=False)
        report_lines.append('\nTop feature importances:')
        for _, r in df_fi.head(10).iterrows():
            report_lines.append(f" - {r['feature']}: {float(r['importance']):.6f}")
        if df_fi['importance'].max() >= 0.99:
            report_lines.append('\nWarning: single feature explains >=99% importance (suspicious)')
    except Exception as e:
        report_lines.append('\nCould not extract feature importances: ' + repr(e))

    # Check perfect predictors in X_test
    perfect = []
    for c in X_test.columns:
        try:
            s = X_test[c].fillna('').astype(str)
            y_s = y_test.fillna('').astype(str)
            if len(s) == len(y_s) and (s == y_s).all():
                perfect.append((c, 'string exact'))
                continue
        except Exception:
            pass
        try:
            s_num = pd.to_numeric(X_test[c], errors='coerce')
            y_num = pd.to_numeric(y_test, errors='coerce')
            if s_num.notna().sum() > 0 and y_num.notna().sum() > 0:
                # compare aligned non-nulls
                a = s_num.dropna().reset_index(drop=True)
                b = y_num.dropna().reset_index(drop=True)
                if len(a) == len(b) and a.equals(b):
                    perfect.append((c, 'numeric exact'))
        except Exception:
            pass

    if perfect:
        report_lines.append('\nPerfect predictors found:')
        for c, t in perfect:
            report_lines.append(f' - {c}: {t}')
    else:
        report_lines.append('\nNo single-column perfect predictors found in `X_test`.')

    # Write report
    with open(OUT_DIR / 'validation.txt', 'w', encoding='utf8') as fh:
        fh.write('\n'.join(report_lines))

    print('\n'.join(report_lines))


if __name__ == '__main__':
    main()
