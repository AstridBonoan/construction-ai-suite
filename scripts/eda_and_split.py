"""
EDA and dataset splitting script for `project_dataset_v1_cleaned.csv`.

Features:
- Deduplicate on `project_id`, keeping the most complete row per project
- Produce numeric summary stats, missingness report, correlation matrix
- Save visualizations (missingness heatmap, correlation heatmap, boxplots)
- Create train/val/test splits and save `X_...` and `y_...` CSVs

Usage:
python scripts/eda_and_split.py --input project_dataset_v1_cleaned.csv --out-dir data_splits --random-state 42

"""
from __future__ import annotations
import argparse
import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def find_project_id_column(df: pd.DataFrame) -> Optional[str]:
    """Heuristic to find project id column name."""
    for c in df.columns:
        if c.lower() in ("project_id", "project id", "id", "proj_id", "projectid"):
            return c
    # fallback: look for column containing both 'project' and 'id'
    for c in df.columns:
        lc = c.lower()
        if "project" in lc and "id" in lc:
            return c
    return None


def deduplicate_keep_most_complete(df: pd.DataFrame, project_col: str) -> pd.DataFrame:
    """Deduplicate rows by `project_col`, keeping the most complete row (max non-null count).

    If there are ties, the first occurrence is kept.
    """
    df = df.copy()
    completeness = df.notna().sum(axis=1)
    df["__completeness_score"] = completeness
    # sort so the best-complete rows come first for each project
    df = df.sort_values([project_col, "__completeness_score"], ascending=[True, False])
    deduped = df.drop_duplicates(subset=[project_col], keep="first").drop(columns=["__completeness_score"])
    logger.info("Deduplicated: from %d rows to %d unique projects", len(df), len(deduped))
    return deduped


def numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    nums = df.select_dtypes(include=[np.number])
    desc = nums.agg(["mean", "median", "std", "min", "max"]).T
    return desc


def missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    miss = df.isna().sum().sort_values(ascending=False)
    pct = (miss / len(df) * 100).round(2)
    report = pd.concat([miss, pct], axis=1)
    report.columns = ["missing_count", "missing_pct"]
    return report


def plot_missingness(df: pd.DataFrame, out_path: Path) -> None:
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.isna(), cbar=False)
    plt.title("Missingness heatmap (rows x columns)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved missingness plot to %s", out_path)


def plot_correlation_heatmap(df: pd.DataFrame, out_path: Path) -> None:
    nums = df.select_dtypes(include=[np.number])
    if nums.shape[1] == 0:
        logger.warning("No numeric columns for correlation heatmap")
        return
    corr = nums.corr()
    plt.figure(figsize=(12, 10))
    sns.heatmap(corr, annot=False, cmap="coolwarm", center=0)
    plt.title("Correlation matrix (numeric features)")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved correlation heatmap to %s", out_path)


def plot_boxplots(df: pd.DataFrame, features: list[str], out_dir: Path) -> None:
    for feat in features:
        if feat not in df.columns:
            logger.debug("Skipping missing boxplot feature: %s", feat)
            continue
        plt.figure(figsize=(8, 4))
        sns.boxplot(x=df[feat].dropna())
        plt.title(f"Boxplot: {feat}")
        plt.tight_layout()
        p = out_dir / f"boxplot_{feat}.png"
        plt.savefig(p)
        plt.close()
        logger.info("Saved boxplot for %s to %s", feat, p)


def categorical_value_counts(df: pd.DataFrame, top_n: int = 20) -> dict:
    obj_cols = [c for c in df.columns if df[c].dtype == object or str(df[c].dtype).startswith("string")]
    counts = {}
    for c in obj_cols:
        counts[c] = df[c].value_counts(dropna=False).head(top_n)
    return counts


def train_val_test_split_and_save(df: pd.DataFrame, target_col: str, out_dir: Path, random_state: int = 42) -> None:
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in dataframe")
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # First split out test (15%) and remaining (85%)
    test_size = 0.15
    val_size = 0.15 / (1.0 - test_size)  # fraction of the remaining to use as val

    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y if y.nunique() > 1 else None
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=val_size, random_state=random_state, stratify=y_train_val if y_train_val.nunique() > 1 else None
    )

    # Save CSVs
    out_dir.mkdir(parents=True, exist_ok=True)
    X_train.to_csv(out_dir / "X_train.csv", index=False)
    y_train.to_csv(out_dir / "y_train.csv", index=False)
    X_val.to_csv(out_dir / "X_val.csv", index=False)
    y_val.to_csv(out_dir / "y_val.csv", index=False)
    X_test.to_csv(out_dir / "X_test.csv", index=False)
    y_test.to_csv(out_dir / "y_test.csv", index=False)
    logger.info("Saved train/val/test splits to %s", out_dir)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="EDA and splitting for project dataset")
    p.add_argument("--input", "-i", required=True, help="Input cleaned CSV file")
    p.add_argument("--out-dir", "-o", default="data_splits", help="Output directory for splits and plots")
    p.add_argument("--target", "-t", default="will_delay", help="Target column name")
    p.add_argument("--random-state", "-r", default=42, type=int, help="Random seed for splits")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(in_path, low_memory=False)
    logger.info("Loaded %d rows, %d columns from %s", len(df), df.shape[1], in_path)

    # Deduplicate
    project_col = find_project_id_column(df)
    if not project_col:
        logger.warning("No project_id-like column found; skipping deduplication")
    else:
        df = deduplicate_keep_most_complete(df, project_col)

    # EDA: numeric summary
    num_summary = numeric_summary(df)
    num_summary.to_csv(out_dir / "numeric_summary.csv")
    logger.info("Saved numeric summary to %s", out_dir / "numeric_summary.csv")

    # Missingness
    miss = missingness_report(df)
    miss.to_csv(out_dir / "missingness_report.csv")
    logger.info("Saved missingness report to %s", out_dir / "missingness_report.csv")
    plot_missingness(df, out_dir / "missingness_heatmap.png")

    # Correlation
    plot_correlation_heatmap(df, out_dir / "correlation_heatmap.png")

    # Boxplots for key features
    key_features = ["labor_hours_actual", "material_cost_actual", "equipment_idle_days", "schedule_slippage_pct"]
    plot_boxplots(df, key_features, out_dir)

    # Categorical value counts
    cat_counts = categorical_value_counts(df)
    # Save each as csv for inspection
    for col, vc in cat_counts.items():
        vc.to_csv(out_dir / f"value_counts__{col}.csv")
    logger.info("Saved categorical value counts to %s", out_dir)

    # Splitting
    train_val_test_split_and_save(df, args.target, out_dir, random_state=args.random_state)

    logger.info("EDA and splitting complete. Outputs in %s", out_dir)


if __name__ == "__main__":
    main()
