"""Compute will_delay_rel1pct label, update aggregated CSV, produce diagnostics and splits.

Outputs:
- updates `data_splits/project_level_aggregated_v8_relaxed.csv` (adds `will_delay_rel1pct`)
- diagnostics: `data_splits/v8/diagnostics_rel1pct.txt`
- splits: `data_splits/v8/X_train_rel1pct.csv`, `X_test_rel1pct.csv`, `y_train_rel1pct.csv`, `y_test_rel1pct.csv`
- filtered splits excluding low-confidence: `*_rel1pct_filtered.csv`
- updates `MODEL_CARD_relaxed.md` with label definition
"""
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import json

ROOT = Path('.')
AGG = ROOT / 'data_splits' / 'project_level_aggregated_v8_relaxed.csv'
OUT_DIAG = ROOT / 'data_splits' / 'v8' / 'diagnostics_rel1pct.txt'
OUT_DIR = ROOT / 'data_splits' / 'v8'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    if not AGG.exists():
        raise FileNotFoundError(f'Aggregated file not found: {AGG}')
    df = pd.read_csv(AGG, dtype=str)

    # Ensure numeric fields
    for n in ['planned_duration_days', 'elapsed_days', 'delay_days', 'schedule_slippage_pct']:
        df[n] = pd.to_numeric(df.get(n, pd.Series()), errors='coerce')

    # Cap planned durations > 1825 as NaN
    df.loc[df['planned_duration_days'] > 1825, 'planned_duration_days'] = np.nan

    # Compute will_delay_rel1pct per requirements
    # condition: planned_duration_days > 14
    cond_planned_ok = df['planned_duration_days'] > 14
    # relative slippage = (elapsed - planned)/planned
    rel_slippage = (df['elapsed_days'] - df['planned_duration_days']) / df['planned_duration_days']
    df['will_delay_rel1pct'] = 0
    df.loc[cond_planned_ok & (rel_slippage > 0.01), 'will_delay_rel1pct'] = 1

    # Preserve flags
    if 'actual_start_imputed' not in df.columns:
        df['actual_start_imputed'] = False
    if 'imputation_rule' not in df.columns:
        df['imputation_rule'] = 'none'
    if 'label_confidence' not in df.columns:
        df['label_confidence'] = 'low'

    # Save updated aggregated CSV (overwrite)
    df.to_csv(AGG, index=False)

    # Diagnostics
    total = len(df)
    positives = int(df['will_delay_rel1pct'].sum())
    negatives = total - positives
    counts_by_rule = df['imputation_rule'].fillna('none').value_counts().to_dict()
    counts_by_conf = df['label_confidence'].fillna('low').value_counts().to_dict()

    diag = {
        'total_projects': total,
        'will_delay_rel1pct_positives': int(positives),
        'will_delay_rel1pct_negatives': int(negatives),
        'counts_by_imputation_rule': counts_by_rule,
        'counts_by_label_confidence': counts_by_conf,
    }
    with open(OUT_DIAG, 'w', encoding='utf-8') as f:
        f.write(json.dumps(diag, indent=2))

    # Prepare splits for training
    computable = df[df['delay_days'].notna()].copy()
    # Use will_delay_rel1pct as label
    y = computable['will_delay_rel1pct'].astype(int)
    X = computable.drop(columns=['will_delay_rel1pct', 'will_delay', 'will_delay_abs30'], errors=True)

    # Drop deny-list columns if present
    DENY = set([c.lower() for c in ['will_delay', 'schedule_slippage_pct', 'award', 'bbl', 'bin', 'cost', 'cost_estimated']])
    for c in list(X.columns):
        if c.lower() in DENY:
            X.drop(columns=[c], inplace=True, errors=True)

    # Split (stratify if possible)
    stratify = y if y.nunique() > 1 and y.sum() > 0 else None
    if len(X) < 2:
        X_train = X.copy(); X_test = X.iloc[0:0].copy(); y_train = y.copy(); y_test = y.iloc[0:0].copy()
    else:
        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Save splits
    X_train.to_csv(OUT_DIR / 'X_train_rel1pct.csv', index=False)
    X_test.to_csv(OUT_DIR / 'X_test_rel1pct.csv', index=False)
    y_train.to_frame('will_delay_rel1pct').to_csv(OUT_DIR / 'y_train_rel1pct.csv', index=False)
    y_test.to_frame('will_delay_rel1pct').to_csv(OUT_DIR / 'y_test_rel1pct.csv', index=False)

    # Filtered splits excluding extremely low-confidence rows
    filtered = computable[computable['label_confidence'].isin(['high', 'medium'])].copy()
    if len(filtered) > 0:
        yf = filtered['will_delay_rel1pct'].astype(int)
        Xf = filtered.drop(columns=['will_delay_rel1pct', 'will_delay', 'will_delay_abs30'], errors=True)
        # drop deny list
        for c in list(Xf.columns):
            if c.lower() in DENY:
                Xf.drop(columns=[c], inplace=True, errors=True)
        if len(Xf) < 2:
            Xf_train = Xf.copy(); Xf_test = Xf.iloc[0:0].copy(); yf_train = yf.copy(); yf_test = yf.iloc[0:0].copy()
        else:
            try:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(Xf, yf, test_size=0.2, random_state=42, stratify=(yf if yf.nunique()>1 and yf.sum()>0 else None))
            except Exception:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(Xf, yf, test_size=0.2, random_state=42)
        Xf_train.to_csv(OUT_DIR / 'X_train_rel1pct_filtered.csv', index=False)
        Xf_test.to_csv(OUT_DIR / 'X_test_rel1pct_filtered.csv', index=False)
        yf_train.to_frame('will_delay_rel1pct').to_csv(OUT_DIR / 'y_train_rel1pct_filtered.csv', index=False)
        yf_test.to_frame('will_delay_rel1pct').to_csv(OUT_DIR / 'y_test_rel1pct_filtered.csv', index=False)

    # Update MODEL_CARD_relaxed.md
    model_card = ROOT / 'MODEL_CARD_relaxed.md'
    add_text = '\n## New label: `will_delay_rel1pct`\n- Definition: relative schedule slippage > 1%: (elapsed_days - planned_duration_days) / planned_duration_days > 0.01\n- Only computed when planned_duration_days > 14 days.\n- Planned durations > 1825 days are capped as invalid (NaN).\n- Label values: 0/1 numeric.\n- Confidence: `label_confidence` retained (high/medium/low) for downstream weighting.\n'
    if model_card.exists():
        with model_card.open('a', encoding='utf-8') as f:
            f.write(add_text)
    else:
        with model_card.open('w', encoding='utf-8') as f:
            f.write('# Model Card - v8 relaxed baseline\n')
            f.write(add_text)

    print('Updated aggregated CSV with will_delay_rel1pct and wrote diagnostics/splits.')


if __name__ == '__main__':
    main()
