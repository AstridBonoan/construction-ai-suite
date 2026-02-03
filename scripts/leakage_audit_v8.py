import json
from pathlib import Path
import pandas as pd
import numpy as np

DATA_CSV = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded.csv")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORT_DIR / "leakage_audit_v8.json"


def find_date_column(df: pd.DataFrame):
    candidates = [
        "planned_start_dt_parsed",
        "planned_start_dt",
        "planned_start",
        "planned_end_dt_parsed",
        "planned_end_dt",
    ]
    for c in candidates:
        if c in df.columns:
            ser = pd.to_datetime(df[c], errors="coerce")
            if ser.notna().sum() > 0:
                return c
    return None


def choose_target(df: pd.DataFrame):
    for t in ["delay_days", "Delay_Days", "delay", "will_delay_ruleB"]:
        if t in df.columns:
            return t
    return None


def basic_target_stats(ser: pd.Series):
    stats = {
        "count": int(ser.count()),
        "unique": int(ser.nunique(dropna=True)),
        "min": None if ser.dropna().empty else float(ser.dropna().min()),
        "max": None if ser.dropna().empty else float(ser.dropna().max()),
        "mean": None if ser.dropna().empty else float(ser.dropna().mean()),
        "std": None if ser.dropna().empty else float(ser.dropna().std()),
    }
    return stats


def leakage_audit():
    df = pd.read_csv(DATA_CSV, low_memory=False)
    df.columns = [str(c).strip() for c in df.columns]

    target = choose_target(df)
    if target is None:
        raise SystemExit("No target found in CSV")

    date_col = find_date_column(df)

    # drop missing target rows
    df = df[df[target].notna()].copy()

    # reproduce split logic (time-based if date present)
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(by=date_col)
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx].copy()
        test = df.iloc[split_idx:].copy()
        split_type = "time"
    else:
        df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx].copy()
        test = df.iloc[split_idx:].copy()
        split_type = "random"

    report = {
        "target": target,
        "date_col": date_col,
        "split_type": split_type,
        "n_total": len(df),
        "n_train": len(train),
        "n_test": len(test),
    }

    # Target distribution
    report["target_stats"] = basic_target_stats(df[target])
    # value counts (binned)
    try:
        vc = df[target].value_counts(dropna=True).head(20).to_dict()
        report["target_value_counts_top20"] = {str(k): int(v) for k, v in vc.items()}
    except Exception:
        report["target_value_counts_top20"] = {}

    # Flag low variance or repeated values
    vals = df[target].dropna()
    report["target_flags"] = {}
    if vals.empty:
        report["target_flags"]["empty"] = True
    else:
        report["target_flags"]["std_too_small"] = float(vals.std()) < 1e-6
        report["target_flags"]["too_few_unique"] = int(vals.nunique()) < max(
            3, 0.01 * len(vals)
        )

    # Train/Test overlap checks
    # exact duplicate rows
    merged = pd.merge(train, test, how="inner")
    report["duplicates_between_splits"] = int(len(merged))

    # identifier overlap
    id_cols = [
        c
        for c in ["project_id", "ID", "Job_Number", "Job_Number_x", "Job_Number.y"]
        if c in df.columns
    ]
    id_overlap = {}
    for c in id_cols:
        train_ids = set(train[c].dropna().astype(str))
        test_ids = set(test[c].dropna().astype(str))
        inter = train_ids.intersection(test_ids)
        id_overlap[c] = {
            "train_unique": len(train_ids),
            "test_unique": len(test_ids),
            "overlap_count": len(inter),
        }
    report["id_overlap"] = id_overlap

    # Target leakage via features
    # suspicious column name scan
    suspicious = []
    leak_keywords = [
        "delay",
        "elapsed",
        "slippage",
        "actual_end",
        "actual_start",
        "planned_end",
        "planned_start",
        "imputed",
    ]
    for c in df.columns:
        lc = c.lower()
        for kw in leak_keywords:
            if kw in lc and c != target:
                suspicious.append(c)
                break
    report["suspicious_columns_by_name"] = suspicious

    # correlation scan for numeric features
    num = df.select_dtypes(include=[np.number]).columns.tolist()
    if target in num:
        num.remove(target)
    corrs = {}
    high_corr = {}
    for c in num:
        try:
            corr = float(df[[c, target]].dropna().corr().iloc[0, 1])
        except Exception:
            corr = None
        corrs[c] = corr
        if corr is not None and abs(corr) > 0.95:
            high_corr[c] = corr
    report["numeric_correlations_with_target"] = {k: v for k, v in list(corrs.items())}
    report["high_correlation_features"] = high_corr

    # Split methodology validation
    if date_col:
        train_max = train[date_col].max()
        test_min = test[date_col].min()
        report["date_split"] = {
            "train_max": str(train_max),
            "test_min": str(test_min),
            "train_before_test": bool(
                pd.notna(train_max) and pd.notna(test_min) and train_max < test_min
            ),
        }

    # save report
    with open(OUT_PATH, "w") as fh:
        json.dump(report, fh, indent=2, default=str)

    # print concise summary
    print("Leakage audit saved to", OUT_PATH)
    print(
        "Total rows:",
        report["n_total"],
        "Train:",
        report["n_train"],
        "Test:",
        report["n_test"],
    )
    print(
        "Target:",
        report["target"],
        "std small?",
        report["target_flags"].get("std_too_small"),
        "unique_count:",
        report["target_stats"]["unique"],
    )
    print("Duplicates between splits:", report["duplicates_between_splits"])
    if id_overlap:
        for k, v in id_overlap.items():
            print(
                f"ID col {k}: train_unique={v['train_unique']} test_unique={v['test_unique']} overlap={v['overlap_count']}"
            )
    if suspicious:
        print("Suspicious columns (name-based):", suspicious[:20])
    if report.get("high_correlation_features"):
        print(
            "High-correlation features (>0.95):",
            list(report["high_correlation_features"].keys()),
        )

    return report


if __name__ == "__main__":
    leakage_audit()
