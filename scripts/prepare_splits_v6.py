#!/usr/bin/env python3
"""Prepare v6 splits: drop original columns flagged as leaking (from transformed mapping).

Reads `analysis_outputs/v5/transformed_feature_mapping.csv` to collect original columns
to exclude, then writes splits to `data_splits/v6/`.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path('.')
DATA_SPLITS = ROOT / 'data_splits'
MAPPING = ROOT / 'analysis_outputs' / 'v5' / 'transformed_feature_mapping.csv'


def load_flagged_originals():
    if not MAPPING.exists():
        return set()
    df = pd.read_csv(MAPPING, low_memory=False)
    if 'original_column' in df.columns and 'flagged_reason' in df.columns:
        return set(df.loc[df['flagged_reason']!='', 'original_column'].dropna().astype(str).tolist())
    return set()


def prepare(random_state: int = 42, test_size: float = 0.2):
    src = DATA_SPLITS / 'project_level_deduped_with_target.csv'
    if not src.exists():
        print('Missing project-level source:', src)
        return 1
    df = pd.read_csv(src, low_memory=False)

    # ensure project_id
    if 'project_id' not in df.columns:
        for c in df.columns:
            if 'project' in c.lower() and 'id' in c.lower():
                df = df.rename(columns={c: 'project_id'})
                break
    if 'project_id' not in df.columns:
        df['project_id'] = (df.get('Project Description', '').fillna('') + df.get('Project School Name', '').fillna('')).factorize()[0]

    if 'will_delay' not in df.columns:
        print('Missing target column will_delay in', src)
        return 1

    df = df.dropna(subset=['will_delay']).reset_index(drop=True)

    drop_features = set()
    # add flagged originals from mapping
    drop_features.update(load_flagged_originals())
    # always drop direct label if present
    drop_features.add('will_delay')
    drop_features.add('schedule_slippage_pct')
    drop_features.add('project_id')

    # drop any remaining ID/date-like columns
    id_date_patterns = ['id', 'date', 'time', 'timestamp', 'start', 'end', 'planned', 'actual', 'year', 'month', 'day']
    for c in df.columns:
        low = str(c).lower()
        for p in id_date_patterns:
            if p in low:
                drop_features.add(c)
                break

    # unnamed
    for c in list(df.columns):
        if str(c).startswith('Unnamed:') or str(c).strip() == '' or str(c).strip() == '()':
            drop_features.add(c)

    # Build X, y
    y = df['will_delay'].astype(int)
    X = df.drop(columns=[c for c in drop_features if c in df.columns], errors='ignore')

    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)
    proj = df['project_id'].reset_index(drop=True)

    rng = np.random.default_rng(random_state)
    unique_projects = np.array(pd.Series(proj).unique())

    if len(unique_projects) < 2:
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

    out_dir = DATA_SPLITS / 'v6'
    out_dir.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(out_dir / 'X_train.csv', index=False)
    y_train.to_csv(out_dir / 'y_train.csv', index=False)
    X_test.to_csv(out_dir / 'X_test.csv', index=False)
    y_test.to_csv(out_dir / 'y_test.csv', index=False)

    meta = {
        'n_projects_total': int(len(unique_projects)),
        'n_projects_test': int(len(test_projects)) if isinstance(test_projects, (set, list)) else 0,
        'split_type': split_type,
        'drop_features_count': len(drop_features),
        'drop_features_sample': list(sorted(list(drop_features)))[:200],
    }
    with open(out_dir / 'metadata.json', 'w') as fh:
        json.dump(meta, fh, indent=2)

    print('Saved v6 splits to', out_dir)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--random-state', type=int, default=42)
    parser.add_argument('--test-size', type=float, default=0.2)
    args = parser.parse_args()
    raise SystemExit(prepare(random_state=args.random_state, test_size=args.test_size))
