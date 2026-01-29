#!/usr/bin/env python3
"""Prepare v3 splits with leakage prevention.

Removes features flagged by the leakage audit, enforces project-level split,
and writes CSVs to data_splits/v3/.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path('.')
DATA_SPLITS = ROOT / 'data_splits'
OUT = DATA_SPLITS / 'v3'
OUT.mkdir(parents=True, exist_ok=True)


def load_audit_flags():
    corr_path = ROOT / 'analysis_outputs' / 'leakage_audit' / 'feature_correlations.csv'
    if not corr_path.exists():
        return set()
    df = pd.read_csv(corr_path, low_memory=False)
    # drop constant, id_like, and schedule_slippage_pct and very-high correlations
    dropc = set()
    for _, r in df.iterrows():
        try:
            if r.get('constant') or r.get('id_like'):
                dropc.add(r['feature'])
        except Exception:
            pass
        try:
            if r.get('feature') == 'schedule_slippage_pct':
                dropc.add('schedule_slippage_pct')
        except Exception:
            pass
        try:
            if not pd.isna(r.get('abs_corr_with_will_delay')) and float(r.get('abs_corr_with_will_delay')) >= 0.95:
                dropc.add(r['feature'])
        except Exception:
            pass
        try:
            if not pd.isna(r.get('abs_corr_with_schedule_slippage_pct')) and float(r.get('abs_corr_with_schedule_slippage_pct')) >= 0.95:
                dropc.add(r['feature'])
        except Exception:
            pass
    return dropc


def prepare(random_state: int = 42, test_size: float = 0.2):
    # Load aggregated project-level dataset
    src = DATA_SPLITS / 'project_level_deduped_with_target.csv'
    if not src.exists():
        print('Missing project-level source:', src)
        return 1
    df = pd.read_csv(src, low_memory=False)

    # Ensure project_id exists
    if 'project_id' not in df.columns:
        # try to infer a project id column
        for c in df.columns:
            if 'project' in c.lower() and 'id' in c.lower():
                df = df.rename(columns={c: 'project_id'})
                break
    if 'project_id' not in df.columns:
        # fallback: create a synthetic project id by grouping on descriptive cols
        df['project_id'] = (df['Project Description'].fillna('') + df.get('Project School Name', '').fillna('')).factorize()[0]

    # target: will_delay
    if 'will_delay' not in df.columns:
        print('Missing target column will_delay in', src)
        return 1

    # drop rows without target
    df = df.dropna(subset=['will_delay']).reset_index(drop=True)

    drop_features = load_audit_flags()
    # always drop project_id from features (used for splitting)
    drop_features.add('project_id')

    # Also drop any columns that are unnamed or empty
    for c in list(df.columns):
        if str(c).startswith('Unnamed:') or str(c).strip() == '()' or str(c).strip() == '':
            drop_features.add(c)

    # Build X, y
    y = df['will_delay'].astype(int)
    X = df.drop(columns=[c for c in drop_features if c in df.columns], errors='ignore')

    # Ensure index alignment
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    proj = df['project_id'].reset_index(drop=True)

    # Project-level split
    rng = np.random.default_rng(random_state)
    unique_projects = np.array(pd.Series(proj).unique())

    if len(unique_projects) < 2:
        # fallback to random row-level split if project-level split not possible
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, shuffle=True)
        test_projects = set()
        split_type = 'row'
    else:
        rng.shuffle(unique_projects)
        n_test = max(1, int(len(unique_projects) * test_size))
        test_projects = set(unique_projects[:n_test])

        mask_test = proj.isin(test_projects)
        X_train = X.loc[~mask_test]
        X_test = X.loc[mask_test]
        y_train = y.loc[~mask_test]
        y_test = y.loc[mask_test]
        split_type = 'project'

    # Save
    OUT.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(OUT / 'X_train.csv', index=False)
    y_train.to_csv(OUT / 'y_train.csv', index=False)
    X_test.to_csv(OUT / 'X_test.csv', index=False)
    y_test.to_csv(OUT / 'y_test.csv', index=False)

    # Save metadata
    meta = {
        'n_projects_total': int(len(unique_projects)),
        'n_projects_test': int(len(test_projects)) if isinstance(test_projects, (set, list)) else 0,
        'split_type': split_type,
        'drop_features_count': len(drop_features),
        'drop_features_sample': list(sorted(list(drop_features)))[:200],
    }
    with open(OUT / 'metadata.json', 'w') as fh:
        json.dump(meta, fh, indent=2)

    print('Saved v3 splits to', OUT)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--random-state', type=int, default=42)
    parser.add_argument('--test-size', type=float, default=0.2)
    args = parser.parse_args()
    raise SystemExit(prepare(random_state=args.random_state, test_size=args.test_size))
