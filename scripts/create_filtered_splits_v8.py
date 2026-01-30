"""Create train/test splits from annotated Rule A aggregated CSV, keeping only high/original label_confidence.

Writes splits to data_splits/v8: X_train.csv, X_test.csv, y_train.csv, y_test.csv, and label variants.
"""
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

ROOT = Path('.')
IN = ROOT / 'data_splits' / 'project_level_aggregated_v8_ruleA_annotated.csv'
OUT_DIR = ROOT / 'data_splits' / 'v8'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    df = pd.read_csv(IN, dtype=str)
    # Count low-confidence rows
    total = len(df)
    low_count = int((df['label_confidence'].fillna('low') == 'low').sum()) if 'label_confidence' in df.columns else 0

    # Filter to high or original
    keep = df['label_confidence'].fillna('low').isin(['high', 'original'])
    dff = df.loc[keep].reset_index(drop=True)

    # Prepare X and y
    # Use will_delay as primary label if present
    if 'will_delay' not in dff.columns:
        raise RuntimeError('will_delay column missing from annotated CSV')

    y = dff['will_delay'].astype(int)
    X = dff.drop(columns=['will_delay', 'will_delay_abs30', 'will_delay_rel5pct'], errors=True)

    # Handle very small sample sizes
    if len(dff) < 2:
        # Not enough samples to split; put all in train
        X_train = X.copy()
        X_test = X.iloc[0:0].copy()
        y_train = y.copy()
        y_test = y.iloc[0:0].copy()
    else:
        # Attempt stratified split if possible
        stratify = y if y.nunique() > 1 and y.sum() > 0 else None
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=stratify
            )
        except ValueError:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

    # Save splits
    X_train.to_csv(OUT_DIR / 'X_train.csv', index=False)
    X_test.to_csv(OUT_DIR / 'X_test.csv', index=False)
    y_train.to_frame('will_delay').to_csv(OUT_DIR / 'y_train.csv', index=False)
    y_test.to_frame('will_delay').to_csv(OUT_DIR / 'y_test.csv', index=False)

    # Also save abs30 variants if present in original annotated
    if 'will_delay_abs30' in dff.columns:
        y_train_abs30 = dff.loc[X_train.index, 'will_delay_abs30']
        y_test_abs30 = dff.loc[X_test.index, 'will_delay_abs30']
        y_train_abs30.to_frame('will_delay_abs30').to_csv(OUT_DIR / 'y_train_abs30.csv', index=False)
        y_test_abs30.to_frame('will_delay_abs30').to_csv(OUT_DIR / 'y_test_abs30.csv', index=False)

    # Write summary
    with open(OUT_DIR / 'filtered_splits_summary.txt', 'w', encoding='utf-8') as f:
        f.write(f'total_input_projects={total}\n')
        f.write(f'low_confidence_skipped={low_count}\n')
        f.write(f'projects_after_filter={len(dff)}\n')
        f.write(f'train_size={len(X_train)}\n')
        f.write(f'test_size={len(X_test)}\n')
        f.write('train_label_counts=' + str(y_train.value_counts().to_dict()) + '\n')
        f.write('test_label_counts=' + str(y_test.value_counts().to_dict()) + '\n')

    print('Wrote splits to', OUT_DIR)
    print('Wrote summary to', OUT_DIR / 'filtered_splits_summary.txt')


if __name__ == '__main__':
    main()
