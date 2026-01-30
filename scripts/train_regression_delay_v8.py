import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import joblib


def safe_float(s):
    try:
        return float(s)
    except Exception:
        return np.nan


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    agg_path = os.path.join(repo_root, 'data_splits', 'project_level_aggregated_v7.csv')

    print('Loading', agg_path)
    df = pd.read_csv(agg_path, dtype=str)

    # Ensure key numeric columns
    for col in ['planned_duration_days', 'elapsed_days', 'schedule_slippage_pct']:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = df[col].apply(safe_float)

    # Compute regression target: delay_days
    df['delay_days'] = df['elapsed_days'] - df['planned_duration_days']
    df['slippage_norm'] = df['delay_days'] / df['planned_duration_days']

    # Drop rows with NaN target
    df = df[~df['delay_days'].isna()].copy()

    # Build feature matrix from available numeric columns
    numeric = df.select_dtypes(include=[np.number]).copy()
    # Remove target columns from features
    for drop in ['delay_days', 'will_delay_opt1', 'will_delay_opt2']:
        if drop in numeric.columns:
            numeric = numeric.drop(columns=[drop])

    if numeric.shape[1] == 0:
        raise RuntimeError('No numeric features available for regression')

    # Impute missing numeric values with median
    X = numeric.fillna(numeric.median())
    y = df['delay_days'].values

    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )

    # Train RandomForestRegressor
    print('Training RandomForestRegressor on', X_train.shape[0], 'rows and', X_train.shape[1], 'features')
    model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    # Metrics
    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(mean_squared_error(y_test, y_pred, squared=False))
    r2 = float(r2_score(y_test, y_pred))

    metrics = {'MAE': mae, 'RMSE': rmse, 'R2': r2, 'n_train': int(X_train.shape[0]), 'n_test': int(X_test.shape[0])}
    print('Metrics:', metrics)

    # Save artifacts
    models_dir = os.path.join(repo_root, 'models', 'v8')
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, 'baseline_project_delay_model_v8.pkl')
    joblib.dump(model, model_path)
    print('Saved model to', model_path)

    metrics_path = os.path.join(models_dir, 'metrics_v8.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print('Saved metrics to', metrics_path)

    # Save splits for reproducibility
    splits_dir = os.path.join(repo_root, 'data_splits', 'v8', 'regression')
    os.makedirs(splits_dir, exist_ok=True)
    X_train.to_csv(os.path.join(splits_dir, 'X_train.csv'), index=False)
    X_test.to_csv(os.path.join(splits_dir, 'X_test.csv'), index=False)
    pd.Series(y_train).to_csv(os.path.join(splits_dir, 'y_train.csv'), index=False, header=['delay_days'])
    pd.Series(y_test).to_csv(os.path.join(splits_dir, 'y_test.csv'), index=False, header=['delay_days'])
    print('Saved train/test splits to', splits_dir)

    # Plots
    plots_dir = os.path.join(models_dir, 'plots')
    os.makedirs(plots_dir, exist_ok=True)

    # Predicted vs actual
    plt.figure(figsize=(6,6))
    plt.scatter(y_test, y_pred, alpha=0.4)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.xlabel('Actual delay_days')
    plt.ylabel('Predicted delay_days')
    plt.title('Predicted vs Actual')
    plt.tight_layout()
    p1 = os.path.join(plots_dir, 'predicted_vs_actual.png')
    plt.savefig(p1)
    plt.close()

    # Residuals
    residuals = y_test - y_pred
    plt.figure(figsize=(6,4))
    plt.scatter(y_pred, residuals, alpha=0.4)
    plt.axhline(0, color='r', linestyle='--')
    plt.xlabel('Predicted')
    plt.ylabel('Residual (actual - pred)')
    plt.title('Residuals vs Predicted')
    plt.tight_layout()
    p2 = os.path.join(plots_dir, 'residuals_vs_predicted.png')
    plt.savefig(p2)
    plt.close()

    # Histogram of errors
    plt.figure(figsize=(6,4))
    plt.hist(residuals, bins=50)
    plt.xlabel('Residual (days)')
    plt.title('Error Distribution')
    plt.tight_layout()
    p3 = os.path.join(plots_dir, 'residuals_histogram.png')
    plt.savefig(p3)
    plt.close()

    print('Saved plots to', plots_dir)


if __name__ == '__main__':
    main()
