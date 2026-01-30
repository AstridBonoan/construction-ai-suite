import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


def safe_float(s):
    try:
        return float(s)
    except Exception:
        return np.nan


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    agg_path = os.path.join(repo_root, 'data_splits', 'project_level_aggregated_v7.csv')
    out_dir = os.path.join(repo_root, 'data_splits', 'v8')
    os.makedirs(out_dir, exist_ok=True)

    print('Reading', agg_path)
    df = pd.read_csv(agg_path, dtype=str)

    # Ensure numeric duration/elapsed/slippage columns exist as floats
    for col in ['planned_duration_days', 'elapsed_days', 'schedule_slippage_pct']:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = df[col].apply(safe_float)

    # Compute absolute delay in days
    df['delay_days'] = df['elapsed_days'] - df['planned_duration_days']

    # Option 1: label by positive delay_days
    df['will_delay_opt1'] = (df['delay_days'] > 0).astype(int)

    # Option 2: label by slippage fraction > 0.05 (5%)
    df['will_delay_opt2'] = (df['schedule_slippage_pct'] > 0.05).astype(int)

    # Save updated aggregated CSV (overwrite)
    backup = agg_path + '.bak'
    if not os.path.exists(backup):
        try:
            os.replace(agg_path, backup)
            print('Backed up original aggregated csv to', backup)
        except Exception:
            pass

    df.to_csv(agg_path, index=False)
    print('Wrote updated aggregated CSV with new labels to', agg_path)

    # Count positives/negatives for each strategy
    counts = {}
    for col in ['will_delay_opt1', 'will_delay_opt2']:
        counts[col] = int(df[col].sum()), int((df[col] == 0).sum())
        print(f"Counts for {col}: positives={counts[col][0]} negatives={counts[col][1]}")

    # Write counts summary
    summary_path = os.path.join(out_dir, 'v7_labeling_counts.txt')
    with open(summary_path, 'w') as f:
        f.write('Labeling counts for project_level_aggregated_v7.csv\n')
        for col, (pos, neg) in counts.items():
            f.write(f"{col}: positives={pos}, negatives={neg}\n")
    print('Wrote counts summary to', summary_path)

    # Function to create stratified splits if possible
    def make_splits(label_col, prefix):
        folder = os.path.join(out_dir, prefix)
        os.makedirs(folder, exist_ok=True)
        y = df[label_col]
        total_pos = int(y.sum())
        total = len(y)
        if total_pos == 0 or total_pos == total:
            print(f"Skipping splits for {label_col}: single-class (pos={total_pos} of {total})")
            return False

        # Use full rows as X (except label column) — downstream code can select features
        X = df.drop(columns=[label_col])

        # First split train vs temp
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )
        # Then split temp into val/test (half/half of 0.3 -> 0.15 each)
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
        )

        # Save CSVs
        X_train.to_csv(os.path.join(folder, 'X_train.csv'), index=False)
        X_val.to_csv(os.path.join(folder, 'X_val.csv'), index=False)
        X_test.to_csv(os.path.join(folder, 'X_test.csv'), index=False)
        y_train.to_csv(os.path.join(folder, 'y_train.csv'), index=False, header=[label_col])
        y_val.to_csv(os.path.join(folder, 'y_val.csv'), index=False, header=[label_col])
        y_test.to_csv(os.path.join(folder, 'y_test.csv'), index=False, header=[label_col])
        print(f'Saved splits for {label_col} under {folder}')
        return True

    # Create splits for both options
    made1 = make_splits('will_delay_opt1', 'option1')
    made2 = make_splits('will_delay_opt2', 'option2')

    print('Done. Splits created:', made1, made2)


if __name__ == '__main__':
    main()
