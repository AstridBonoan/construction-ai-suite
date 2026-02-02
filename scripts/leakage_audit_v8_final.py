import json
from pathlib import Path
import pandas as pd
import numpy as np

DATA_CSV = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORT_DIR / "leakage_audit_v8_final.json"


def choose_target(df: pd.DataFrame):
    for t in ['delay_days', 'Delay_Days', 'delay', 'will_delay_ruleB']:
        if t in df.columns:
            return t
    return None


def basic_target_stats(ser: pd.Series):
    stats = {
        'count': int(ser.count()),
        'unique': int(ser.nunique(dropna=True)),
        'min': None if ser.dropna().empty else float(ser.dropna().min()),
        'max': None if ser.dropna().empty else float(ser.dropna().max()),
        'mean': None if ser.dropna().empty else float(ser.dropna().mean()),
        'std': None if ser.dropna().empty else float(ser.dropna().std())
    }
    return stats


def group_based_split(df: pd.DataFrame, group_col: str, train_frac: float = 0.8):
    groups = df[group_col].dropna().unique().tolist()
    groups = sorted(groups)
    split_idx = int(len(groups) * train_frac)
    train_groups = set(groups[:split_idx])
    train = df[df[group_col].isin(train_groups)].copy()
    test = df[~df[group_col].isin(train_groups)].copy()
    return train, test


def run_audit():
    df = pd.read_csv(DATA_CSV, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]

    target = choose_target(df)
    if target is None:
        raise SystemExit('No target found in cleaned CSV')

    df = df[df[target].notna()].copy()

    # choose grouping column
    group_col = None
    for c in ['project_id', 'Job_Number', 'ID']:
        if c in df.columns:
            group_col = c
            break
    if group_col is None:
        raise SystemExit('No group identifier found to perform group-based split')

    train, test = group_based_split(df, group_col)

    report = {'target': target, 'group_col': group_col, 'n_total': len(df), 'n_train': len(train), 'n_test': len(test)}
    report['target_stats'] = basic_target_stats(df[target])

    merged = pd.merge(train, test, how='inner')
    report['duplicates_between_splits'] = int(len(merged))

    train_ids = set(train[group_col].dropna().astype(str))
    test_ids = set(test[group_col].dropna().astype(str))
    inter = train_ids.intersection(test_ids)
    report['id_overlap'] = {'group_col': group_col, 'train_unique': len(train_ids), 'test_unique': len(test_ids), 'overlap_count': len(inter)}

    num = df.select_dtypes(include=[np.number]).columns.tolist()
    if target in num:
        num.remove(target)
    corrs = {}
    high_corr = {}
    for c in num:
        try:
            corr = float(df[[c, target]].dropna().corr().iloc[0,1])
        except Exception:
            corr = None
        corrs[c] = corr
        if corr is not None and abs(corr) > 0.95:
            high_corr[c] = corr
    report['high_correlation_features'] = high_corr

    with open(OUT_PATH, 'w') as fh:
        json.dump(report, fh, indent=2, default=str)

    print('Final leakage audit saved to', OUT_PATH)
    print('Total rows:', report['n_total'], 'Train:', report['n_train'], 'Test:', report['n_test'])
    print('Duplicates between splits:', report['duplicates_between_splits'])
    print('ID overlap:', report['id_overlap'])
    if report['high_correlation_features']:
        print('High-correlation features (>0.95):', list(report['high_correlation_features'].keys()))
    else:
        print('No features with |corr| > 0.95 found')

    return report


if __name__ == '__main__':
    run_audit()
