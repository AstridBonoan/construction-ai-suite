#!/usr/bin/env python3
"""Deep leakage scan for v5: exact matches, correlations, mutual information.

Writes:
- analysis_outputs/v5/deep_leakage_candidates.csv
- analysis_outputs/v5/deep_leakage_candidates.txt
- optional plots under analysis_outputs/v5/
"""
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_selection import mutual_info_regression
from scipy.stats import spearmanr

ROOT = Path('.')
SPLITS = ROOT / 'data_splits' / 'v5'
OUT = ROOT / 'analysis_outputs' / 'v5'
OUT.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT / 'deep_leakage_candidates.csv'
TXT_OUT = OUT / 'deep_leakage_candidates.txt'
HEAT = OUT / 'deep_leakage_target_corr_heatmap.png'
MI_BAR = OUT / 'deep_leakage_mutual_info.png'

def safe_read(p: Path):
    return pd.read_csv(p, low_memory=False)

def get_transformed(X, pre):
    """Return (X_trans, feat_names) if possible"""
    X_tr = None
    names = None
    try:
        X_tr = pre.transform(X)
        try:
            names = pre.get_feature_names_out()
        except Exception:
            try:
                names = pre.get_feature_names_out(X.columns)
            except Exception:
                names = None
    except Exception:
        X_tr = None
        names = None
    return X_tr, names

def describe_candidate_row(name, flags):
    return {'feature': name, **flags}

def main():
    X_train = safe_read(SPLITS / 'X_train.csv')
    X_test = safe_read(SPLITS / 'X_test.csv')
    y_train = safe_read(SPLITS / 'y_train.csv')
    y_test = safe_read(SPLITS / 'y_test.csv')
    if isinstance(y_train, pd.DataFrame) and y_train.shape[1] == 1:
        y_train = y_train.iloc[:,0]
    if isinstance(y_test, pd.DataFrame) and y_test.shape[1] == 1:
        y_test = y_test.iloc[:,0]

    model_path = ROOT / 'models' / 'v5' / 'baseline_project_delay_model_v5.pkl'
    pre = None
    rf = None
    try:
        mdl = joblib.load(model_path)
        try:
            pre = mdl.named_steps['pre']
            rf = mdl.named_steps['rf']
        except Exception:
            pre = None
            rf = None
    except Exception:
        mdl = None

    rows = []

    # First, check original columns for exact matches / correlations / MI
    for df_name, X, y in [('train', X_train, y_train), ('test', X_test, y_test)]:
        for c in X.columns:
            flags = {}
            s = X[c]
            # exact string match
            try:
                eq = s.fillna('').astype(str) == y.fillna('').astype(str)
                flags[f'exact_{df_name}'] = bool(eq.all())
            except Exception:
                flags[f'exact_{df_name}'] = False
            # numeric exact match
            try:
                s_num = pd.to_numeric(s, errors='coerce')
                y_num = pd.to_numeric(y, errors='coerce')
                num_eq = False
                if s_num.notna().sum() and y_num.notna().sum():
                    a = s_num.dropna().reset_index(drop=True)
                    b = y_num.dropna().reset_index(drop=True)
                    if len(a) == len(b) and a.equals(b):
                        num_eq = True
                flags[f'exact_num_{df_name}'] = bool(num_eq)
            except Exception:
                flags[f'exact_num_{df_name}'] = False
            # pearson corr (if numeric)
            try:
                s_num = pd.to_numeric(s, errors='coerce')
                if s_num.notna().sum() >= 2:
                    pear = float(s_num.corr(pd.to_numeric(y, errors='coerce')))
                else:
                    pear = np.nan
                flags[f'pearson_{df_name}'] = pear
            except Exception:
                flags[f'pearson_{df_name}'] = np.nan
            # spearman
            try:
                s_num = pd.to_numeric(s, errors='coerce')
                if s_num.notna().sum() >= 2:
                    sp = spearmanr(s_num, pd.to_numeric(y, errors='coerce'), nan_policy='omit').correlation
                else:
                    sp = np.nan
                flags[f'spearman_{df_name}'] = float(sp) if sp is not None else np.nan
            except Exception:
                flags[f'spearman_{df_name}'] = np.nan
            # mutual info (train only to be stable)
            if df_name == 'train':
                try:
                    s_num = pd.to_numeric(s, errors='coerce')
                    if s_num.notna().sum() > 0:
                        # mutual_info_regression needs 2D X
                        mi = float(mutual_info_regression(s_num.fillna(0).values.reshape(-1,1), pd.to_numeric(y, errors='coerce').fillna(0), discrete_features=False)[0])
                    else:
                        # treat as discrete
                        mi = float(mutual_info_regression(pd.factorize(s.fillna(''))[0].reshape(-1,1), pd.to_numeric(y, errors='coerce').fillna(0), discrete_features=True)[0])
                except Exception:
                    mi = np.nan
                flags['mutual_info_train'] = mi

            # append or merge
            # Keep one record per feature; if duplicates due to train/test, merge flags
            existing = next((r for r in rows if r['feature']==c), None)
            if existing:
                existing.update(flags)
            else:
                rows.append(describe_candidate_row(c, flags))

    # Next, check transformed features if preprocessor available
    if pre is not None:
        try:
            Xtr_train, names = get_transformed(X_train, pre)
            Xtr_test, _ = get_transformed(X_test, pre)
            if Xtr_train is not None:
                # convert to dense if sparse
                try:
                    if hasattr(Xtr_train, 'toarray'):
                        Xtr_train = Xtr_train.toarray()
                    if hasattr(Xtr_test, 'toarray'):
                        Xtr_test = Xtr_test.toarray()
                except Exception:
                    pass

                if names is None:
                    names = [f'trans_{i}' for i in range(Xtr_train.shape[1])]

                # for each transformed column compute same stats against y_train/y_test
                for idx, fname in enumerate(names):
                    flags = {}
                    col_tr = pd.Series(Xtr_train[:, idx])
                    # exact
                    try:
                        eq = col_tr.fillna('').astype(str) == y_train.fillna('').astype(str)
                        flags['exact_train_trans'] = bool(eq.all())
                    except Exception:
                        flags['exact_train_trans'] = False
                    # pearson/spearman/mi
                    try:
                        pear = float(col_tr.corr(pd.to_numeric(y_train, errors='coerce')))
                    except Exception:
                        pear = np.nan
                    flags['pearson_train_trans'] = pear
                    try:
                        sp = spearmanr(col_tr, pd.to_numeric(y_train, errors='coerce'), nan_policy='omit').correlation
                        flags['spearman_train_trans'] = float(sp) if sp is not None else np.nan
                    except Exception:
                        flags['spearman_train_trans'] = np.nan
                    try:
                        mi = float(mutual_info_regression(col_tr.fillna(0).values.reshape(-1,1), pd.to_numeric(y_train, errors='coerce').fillna(0), discrete_features=False)[0])
                    except Exception:
                        mi = np.nan
                    flags['mutual_info_train_trans'] = mi

                    existing = next((r for r in rows if r['feature']==fname), None)
                    if existing:
                        existing.update(flags)
                    else:
                        rows.append(describe_candidate_row(fname, flags))
        except Exception:
            pass

    df_out = pd.DataFrame(rows)
    # Fill missing flag cols
    df_out = df_out.fillna(value={k: np.nan for k in df_out.columns})
    df_out.to_csv(CSV_OUT, index=False)

    # Write human summary: highlight candidates where exact match or high corr or high MI
    with open(TXT_OUT, 'w', encoding='utf8') as fh:
        fh.write('Deep leakage candidates summary\n')
        fh.write(f'Total examined features (orig + transformed): {len(df_out)}\n\n')
        suspicious = []
        for _, r in df_out.iterrows():
            note = []
            if r.get('exact_train') or r.get('exact_test') or r.get('exact_num_train') or r.get('exact_num_test'):
                note.append('exact_match')
            try:
                if abs(float(r.get('pearson_train', 0) or 0)) >= 0.95 or abs(float(r.get('pearson_test', 0) or 0)) >= 0.95:
                    note.append('high_pearson')
            except Exception:
                pass
            try:
                if abs(float(r.get('spearman_train', 0) or 0)) >= 0.95 or abs(float(r.get('spearman_test', 0) or 0)) >= 0.95:
                    note.append('high_spearman')
            except Exception:
                pass
            try:
                if float(r.get('mutual_info_train', 0) or 0) >= 0.9:
                    note.append('high_mutual_info')
            except Exception:
                pass
            if note:
                suspicious.append((r['feature'], ';'.join(note)))

        if suspicious:
            fh.write('Suspicious features (flag, reason):\n')
            for f, reason in suspicious:
                fh.write(f' - {f}: {reason}\n')
        else:
            fh.write('No single-column exact matches or extremely high single-column associations found.\n')

    print('Wrote', CSV_OUT, TXT_OUT)


if __name__ == '__main__':
    main()
