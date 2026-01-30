#!/usr/bin/env python3
import os
import json
import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib

# Paths
SPLIT_DIR = 'data_splits/v8'
MODEL_DIR = 'models/v8'
MODEL_PATH = os.path.join(MODEL_DIR, 'model.joblib')
METRICS_PATH = os.path.join(MODEL_DIR, 'metrics.json')
MODEL_CARD = 'MODEL_CARD.md'

os.makedirs(MODEL_DIR, exist_ok=True)

# CLI
parser = argparse.ArgumentParser(description='Train exploratory baseline (v8)')
parser.add_argument('--include-imputed', action='store_true', help='Include rows with actual_start_imputed=True in training')
parser.add_argument('--label', type=str, default='will_delay', help='Label to use (will_delay or will_delay_abs30)')
args = parser.parse_args()
INCLUDE_IMPUTED = bool(args.include_imputed)
LABEL_NAME = args.label

# Load splits
X_train = pd.read_csv(os.path.join(SPLIT_DIR, 'X_train.csv'))
X_test = pd.read_csv(os.path.join(SPLIT_DIR, 'X_test.csv'))
# load label files depending on requested label
if LABEL_NAME == 'will_delay_abs30':
    y_train = pd.read_csv(os.path.join(SPLIT_DIR, 'y_train_abs30.csv'))
    y_test = pd.read_csv(os.path.join(SPLIT_DIR, 'y_test_abs30.csv'))
else:
    y_train = pd.read_csv(os.path.join(SPLIT_DIR, 'y_train.csv'))
    y_test = pd.read_csv(os.path.join(SPLIT_DIR, 'y_test.csv'))

# Ensure label column name
if 'will_delay' in y_train.columns:
    y_train = y_train['will_delay']
else:
    y_train = y_train.iloc[:,0]
if 'will_delay' in y_test.columns:
    y_test = y_test['will_delay']
else:
    y_test = y_test.iloc[:,0]

# Convert to numeric
y_train = pd.to_numeric(y_train, errors='coerce')
y_test = pd.to_numeric(y_test, errors='coerce')

# Exclude imputed rows if present (unless user requested inclusion)
imputed_col = 'actual_start_imputed'
if not INCLUDE_IMPUTED:
    exclude_mask_train = pd.Series([False]*len(X_train))
    exclude_mask_test = pd.Series([False]*len(X_test))
    if imputed_col in X_train.columns:
        exclude_mask_train = X_train[imputed_col].astype(str).str.lower().isin(['true','1','yes'])
    if imputed_col in X_test.columns:
        exclude_mask_test = X_test[imputed_col].astype(str).str.lower().isin(['true','1','yes'])

    # Filter out imputed rows
    X_train_filtered = X_train.loc[~exclude_mask_train].copy()
    X_test_filtered = X_test.loc[~exclude_mask_test].copy()
    y_train_filtered = y_train.loc[X_train_filtered.index].copy()
    y_test_filtered = y_test.loc[X_test_filtered.index].copy()
else:
    # Keep all rows
    X_train_filtered = X_train.copy()
    X_test_filtered = X_test.copy()
    y_train_filtered = y_train.copy()
    y_test_filtered = y_test.copy()

# Drop deny-list columns just in case
DENY_LIST = set([c.lower() for c in (
    ['will_delay', 'schedule_slippage_pct', 'award', 'bbl', 'bin', 'cost', 'cost_estimated']
 )])
for df in (X_train_filtered, X_test_filtered):
    for c in list(df.columns):
        if c.lower() in DENY_LIST:
            df.drop(columns=[c], inplace=True)

# Basic preprocessing: drop non-numeric columns
numeric_cols = X_train_filtered.select_dtypes(include=[np.number]).columns.tolist()
X_train_num = X_train_filtered[numeric_cols].fillna(0)
X_test_num = X_test_filtered[numeric_cols].fillna(0)

# Check label classes
train_counts = y_train_filtered.value_counts(dropna=False).to_dict()
test_counts = y_test_filtered.value_counts(dropna=False).to_dict()

metrics = {
    'train_counts': train_counts,
    'test_counts': test_counts,
}

# If single-class in train, warn and write model card without training
if len(train_counts) <= 1 or sum(v for k,v in train_counts.items() if str(k) in ('1','True')) == 0:
    warning = 'Single-class or no positive examples in training set; skipping model training.'
    metrics['warning'] = warning
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    # Write MODEL_CARD
    with open(MODEL_CARD, 'w') as f:
        f.write('# Model Card - v8 exploratory baseline\n')
        f.write('\n')
        f.write('Dataset: data_splits/v8 (project_level_aggregated_v8.csv)\n')
        if INCLUDE_IMPUTED:
            f.write('Note: actual_start_imputed rows WERE INCLUDED in training (flag present as a feature if available).\n')
        else:
            f.write('Note: actual_start_imputed rows were excluded from training.\n')
        f.write('\n')
        f.write('WARNING: ' + warning + '\n')
    print(warning)
else:
    # Train RandomForest classifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train_num, y_train_filtered)

    # Predict
    y_pred = clf.predict(X_test_num)

    # Metrics
    acc = float(accuracy_score(y_test_filtered, y_pred))
    prec = float(precision_score(y_test_filtered, y_pred, zero_division=0))
    rec = float(recall_score(y_test_filtered, y_pred, zero_division=0))
    f1 = float(f1_score(y_test_filtered, y_pred, zero_division=0))

    metrics.update({'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1})

    # Save model and metrics
    joblib.dump(clf, MODEL_PATH)
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)

    # Write MODEL_CARD
    with open(MODEL_CARD, 'w') as f:
        f.write('# Model Card - v8 exploratory baseline\n')
        f.write('\n')
        f.write('Dataset: data_splits/v8 (project_level_aggregated_v8.csv)\n')
        if INCLUDE_IMPUTED:
            f.write('Imputation: projects with `actual_start_imputed=True` WERE INCLUDED in training and the flag was retained as a feature where present.\n')
        else:
            f.write('Imputation: projects with `actual_start_imputed=True` were excluded from training.\n')
        f.write('\n')
        f.write('Training counts:\n')
        f.write(json.dumps(train_counts) + '\n')
        f.write('Test counts:\n')
        f.write(json.dumps(test_counts) + '\n')
        f.write('\n')
        f.write('Metrics:\n')
        f.write(json.dumps({'accuracy': acc, 'precision': prec, 'recall': rec, 'f1': f1}, indent=2) + '\n')

    print('Trained model saved to', MODEL_PATH)
    print('Metrics:', metrics)

print('Wrote metrics to', METRICS_PATH)
print('Wrote model card to', MODEL_CARD)
