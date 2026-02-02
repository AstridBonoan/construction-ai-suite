import os
import argparse
import json
import joblib
from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# Use the cleaned, nodistrict no-leak CSV by default
DATA_CSV = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv")
OUT_DIR = Path("analysis")
MODEL_DIR = Path("models")
RANDOM_STATE = 42
BLACKLIST_PATH = Path("config/feature_blacklist_v8.json")


def safe_strip_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_date_column(df: pd.DataFrame):
    candidates = [
        'planned_start_dt_parsed', 'planned_start_dt', 'planned_start',
        'planned_start_dt_parsed', 'planned_start_dt', 'planned_end_dt_parsed',
        'planned_start'
    ]
    for c in candidates:
        if c in df.columns:
            try:
                ser = pd.to_datetime(df[c], errors='coerce')
                if ser.notna().sum() > 0:
                    return c
            except Exception:
                continue
    return None


def prepare_features(df: pd.DataFrame, target_col: str):
    # Select numeric features and a few useful categoricals if present
    num = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_col in num:
        num.remove(target_col)

    # blacklist columns that are obviously identifiers or geo
    blacklist = set(['project_id', 'ID', 'source_file'])
    num = [c for c in num if c not in blacklist]

    # choose a small set of categorical features if present
    cats = []
    for cand in ['Project Type', 'Project Status Name', 'Project Geographic District', 'Project Phase Name']:
        if cand in df.columns:
            cats.append(cand)

    feats = num + cats
    X = df[feats].copy()

    # drop numeric columns that are entirely missing (no signal)
    nums = X.select_dtypes(include=[np.number]).columns.tolist()
    drop_nums = []
    for c in nums:
        try:
            cnt = int(X[c].notna().sum())
        except Exception:
            # skip columns we can't evaluate
            continue
        if cnt == 0:
            drop_nums.append(c)
    if drop_nums:
        X = X.drop(columns=drop_nums)

    # numeric fill (use 0 if median is NaN)
    for c in X.select_dtypes(include=[np.number]).columns:
        try:
            med = pd.to_numeric(X[c], errors='coerce').median()
        except Exception:
            med = 0.0
        if pd.isna(med):
            med = 0.0
        X[c] = X[c].fillna(med)

    # categorical handling: fillna and one-hot (limited)
    if cats:
        X = pd.get_dummies(X, columns=cats, dummy_na=False)

    return X


def train_and_evaluate(X_train, y_train, X_test, y_test):
    results = {}
    models = {
        'LinearRegression': LinearRegression(),
        'Ridge': Ridge(random_state=RANDOM_STATE),
        'Lasso': Lasso(random_state=RANDOM_STATE, max_iter=5000),
        'RandomForest': RandomForestRegressor(n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1)
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        rmse = float(np.sqrt(mse))
        results[name] = {'model': model, 'mae': float(mae), 'rmse': float(rmse)}

    return results


def feature_importances(model, feature_names):
    if hasattr(model, 'coef_'):
        coefs = np.array(model.coef_).flatten()
        return pd.DataFrame({'feature': feature_names, 'importance': coefs}).sort_values('importance', key=abs, ascending=False)
    elif hasattr(model, 'feature_importances_'):
        imps = np.array(model.feature_importances_).flatten()
        return pd.DataFrame({'feature': feature_names, 'importance': imps}).sort_values('importance', ascending=False)
    else:
        return pd.DataFrame({'feature': feature_names, 'importance': 0})


def main(dry_run: bool = False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading:", DATA_CSV)
    df = pd.read_csv(DATA_CSV, low_memory=False)
    df = safe_strip_cols(df)

    # load feature blacklist (if present)
    blacklist_cfg = {'columns': [], 'prefixes': []}
    try:
        if BLACKLIST_PATH.exists():
            with open(BLACKLIST_PATH, 'r') as fh:
                cfg = json.load(fh)
                blacklist_cfg['columns'] = [str(c).strip() for c in cfg.get('columns', [])]
                blacklist_cfg['prefixes'] = [str(p) for p in cfg.get('prefixes', [])]
                print('Loaded feature blacklist from', BLACKLIST_PATH)
        else:
            print('No feature blacklist found at', BLACKLIST_PATH)
    except Exception as e:
        print('Failed to load blacklist:', e)

    # identify target
    target_col = None
    for t in ['delay_days', 'Delay_Days', 'delay', 'will_delay_ruleB']:
        if t in df.columns:
            target_col = t
            break
    if target_col is None:
        raise SystemExit('No target column found (expected delay_days)')
    print('Target:', target_col)

    # enforce blacklist: drop blacklisted columns/prefixes but never drop the target
    to_drop = []
    for c in df.columns:
        if c == target_col:
            continue
        if c in blacklist_cfg['columns']:
            to_drop.append(c)
            continue
        for p in blacklist_cfg['prefixes']:
            if c.startswith(p):
                to_drop.append(c)
                break
    # dedupe
    to_drop = sorted(set(to_drop))
    # report what would be dropped
    print(f"Feature blacklist would drop {len(to_drop)} columns (sample):", to_drop[:50])
    if dry_run:
        print('Dry-run mode: exiting before training. No models or reports written.')
        return

    if to_drop:
        df = df.drop(columns=[c for c in to_drop if c in df.columns])
    print(f"Enforced feature blacklist: dropped {len(to_drop)} columns")
    if len(to_drop) > 0:
        print('Dropped columns (sample):', to_drop[:50])

    # identify date column
    date_col = find_date_column(df)
    print('Date column chosen for time split:', date_col)

    # drop rows with missing target
    df = df[df[target_col].notna()].copy()

    # time-aware split if date found
    if date_col is not None:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.sort_values(by=date_col)
        n = len(df)
        split = int(n * 0.8)
        train_df = df.iloc[:split]
        test_df = df.iloc[split:]
    else:
        # deterministic random split
        df = df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
        split = int(len(df) * 0.8)
        train_df = df.iloc[:split]
        test_df = df.iloc[split:]

    print('Train/test sizes:', len(train_df), len(test_df))

    X_train = prepare_features(train_df, target_col)
    X_test = prepare_features(test_df, target_col)
    y_train = train_df[target_col].astype(float)
    y_test = test_df[target_col].astype(float)

    # align columns
    X_train, X_test = X_train.align(X_test, join='left', axis=1, fill_value=0)

    results = train_and_evaluate(X_train, y_train, X_test, y_test)

    # summarize
    summary = {}
    for name, res in results.items():
        summary[name] = {'mae': res['mae'], 'rmse': res['rmse']}

    # pick best by MAE
    best_name = min(summary.keys(), key=lambda k: summary[k]['mae'])
    best_model = results[best_name]['model']
    print('\nMetrics summary:')
    print(json.dumps(summary, indent=2))
    print('\nBest model:', best_name)

    # feature importances
    feat_imp = feature_importances(best_model, X_train.columns.tolist())
    feat_imp_path = OUT_DIR / 'feature_importances_v8.csv'
    feat_imp.to_csv(feat_imp_path, index=False)

    # save model and report
    model_path = MODEL_DIR / f'baseline_best_v8_{best_name}.pkl'
    joblib.dump(best_model, model_path)

    report = {'summary': summary, 'best_model': best_name, 'model_path': str(model_path), 'feature_importances': str(feat_imp_path)}
    report_path = OUT_DIR / 'baseline_v8_report.json'
    with open(report_path, 'w') as fh:
        json.dump(report, fh, indent=2)

    print('\nSaved model to', model_path)
    print('Saved report to', report_path)
    print('Saved feature importances to', feat_imp_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry-run: show blacklist drops and quit before training')
    args = parser.parse_args()
    main(dry_run=args.dry_run)
