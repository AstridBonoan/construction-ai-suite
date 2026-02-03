"""Apply Rule B cohort median imputation for v8 aggregated projects.

For each project_type (if present) compute median planned_duration_days from projects
with full planned windows (0 < planned_duration_days <= 1825). For projects with
collapsed planned windows or missing actual_start, impute actual_start = actual_end - median_duration
for the project's project_type (or global median if project_type missing). Flag imputed rows
with actual_start_imputed=True and imputation_rule='RuleB' and label_confidence='low'.

Recompute elapsed_days, delay_days and schedule_slippage_pct where planned_duration_days > 0.
Create will_delay_ruleB = 1 if delay_days > 0 else 0 (only computed when planned_duration_days > 0).

Outputs:
- updates data_splits/project_level_aggregated_v8_relaxed.csv
- diagnostics: data_splits/v8/diagnostics_ruleB.txt
- splits: data_splits/v8/X_train_ruleB.csv, X_test_ruleB.csv, y_train_ruleB.csv, y_test_ruleB.csv
- filtered splits excluding low-confidence: *_ruleB_filtered.csv
- appends RuleB notes to MODEL_CARD_relaxed.md
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
import json

ROOT = Path(".")
AGG = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT_AGG = ROOT / "data_splits" / "project_level_aggregated_v8_ruleB_imputed.csv"
OUT_DIAG = ROOT / "data_splits" / "v8" / "diagnostics_ruleB.txt"
OUT_DIR = ROOT / "data_splits" / "v8"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def to_dt_series(s):
    return pd.to_datetime(s, errors="coerce")


def main():
    if not AGG.exists():
        raise FileNotFoundError(f"Aggregated file not found: {AGG}")
    df = pd.read_csv(AGG, dtype=str)

    # ensure numeric columns
    for n in [
        "planned_duration_days",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
    ]:
        df[n] = pd.to_numeric(df.get(n, pd.Series()), errors="coerce")

    # cap planned durations > 1825
    df.loc[df["planned_duration_days"] > 1825, "planned_duration_days"] = np.nan

    # Normalize date columns to datetime
    for dcol in ["planned_start", "planned_end", "actual_start", "actual_end"]:
        if dcol in df.columns:
            df[dcol + "_dt"] = to_dt_series(df[dcol])
        else:
            df[dcol + "_dt"] = pd.NaT

    # Determine project_type column name if exists
    project_type_col = None
    for candidate in ["project_type", "type", "Project Type", "projectType"]:
        if candidate in df.columns:
            project_type_col = candidate
            break

    # Compute median planned duration per project_type
    medians = {}
    if project_type_col:
        groups = df.groupby(df[project_type_col].fillna(""))
        for k, g in groups:
            vals = g["planned_duration_days"].dropna()
            vals = vals[(vals > 0) & (vals <= 1825)]
            medians[k if k != "" else None] = (
                float(vals.median()) if len(vals) > 0 else np.nan
            )
    # global median fallback
    global_vals = df["planned_duration_days"].dropna()
    global_vals = global_vals[(global_vals > 0) & (global_vals <= 1825)]
    global_median = float(global_vals.median()) if len(global_vals) > 0 else 365.0

    # Apply Rule B imputation
    imputed_count = 0
    imputation_rules = df.get("imputation_rule", pd.Series(["none"] * len(df))).fillna(
        "none"
    )
    actual_start_imputed = (
        df.get("actual_start_imputed", pd.Series([False] * len(df)))
        .astype(bool)
        .fillna(False)
    )
    label_confidence = df.get("label_confidence", pd.Series(["low"] * len(df))).fillna(
        "low"
    )

    for idx, row in df.iterrows():
        # conditions: collapsed planned window or missing actual_start
        pdur = row.get("planned_duration_days")
        try:
            pdur = float(pdur)
        except Exception:
            pdur = np.nan
        actual_start_dt = row.get("actual_start_dt")
        actual_end_dt = row.get("actual_end_dt")

        collapsed_planned = (not np.isnan(pdur) and pdur <= 0) or pd.isna(pdur)
        missing_actual_start = pd.isna(actual_start_dt)

        if collapsed_planned:
            # choose median for project_type to replace planned_duration_days only for collapsed windows
            key = None
            if project_type_col:
                k = row.get(project_type_col)
                key = k if pd.notna(k) and k != "" else None
            median_d = medians.get(key, np.nan) if medians else np.nan
            if np.isnan(median_d):
                median_d = global_median
            if not np.isnan(median_d):
                df.at[idx, "planned_duration_days"] = float(median_d)
                # mark that we imputed planned duration (tag via imputation_rule/label_confidence and actual_start_imputed)
                df.at[idx, "imputation_rule"] = "RuleB"
                df.at[idx, "label_confidence"] = "low"
                df.at[idx, "actual_start_imputed"] = True
                imputed_count += 1

        # After potentially replacing planned_duration_days, if actual_start missing but actual_end present, impute actual_start
        if (pd.isna(actual_start_dt) or pd.isna(df.at[idx, "actual_start_dt"])) and (
            not pd.isna(actual_end_dt)
        ):
            # use median (if available) to impute actual_start as actual_end - median
            key = None
            if project_type_col:
                k = row.get(project_type_col)
                key = k if pd.notna(k) and k != "" else None
            median_d = medians.get(key, np.nan) if medians else np.nan
            if np.isnan(median_d):
                median_d = global_median
            if not np.isnan(median_d):
                new_actual_start = pd.to_datetime(actual_end_dt) - pd.Timedelta(
                    days=int(round(median_d))
                )
                df.at[idx, "actual_start"] = new_actual_start.isoformat()
                df.at[idx, "actual_start_dt"] = new_actual_start
                df.at[idx, "actual_start_imputed"] = True
                df.at[idx, "imputation_rule"] = "RuleB"
                df.at[idx, "label_confidence"] = "low"
                imputed_count += 1

    # Re-apply planned-duration cap > 1825 in case medians exceeded cap
    df.loc[df["planned_duration_days"] > 1825, "planned_duration_days"] = np.nan

    # Recompute elapsed_days using dt columns
    df["elapsed_days"] = (df["actual_end_dt"] - df["actual_start_dt"]).dt.days

    # Recompute delay_days and schedule_slippage_pct only where planned_duration_days > 0
    df["delay_days"] = np.nan
    df["schedule_slippage_pct"] = np.nan
    mask = (
        (df["planned_duration_days"].notna())
        & (df["planned_duration_days"] > 0)
        & (df["elapsed_days"].notna())
    )
    df.loc[mask, "delay_days"] = (
        df.loc[mask, "elapsed_days"] - df.loc[mask, "planned_duration_days"]
    )
    df.loc[mask & (df["planned_duration_days"] > 0), "schedule_slippage_pct"] = (
        df.loc[mask, "delay_days"] / df.loc[mask, "planned_duration_days"]
    )

    # Create will_delay_ruleB
    df["will_delay_ruleB"] = 0
    df.loc[mask & (df["delay_days"] > 0), "will_delay_ruleB"] = 1

    # Save updated aggregated CSV (write new file)
    df.to_csv(OUT_AGG, index=False)

    # Diagnostics
    total = len(df)
    positives = int(df["will_delay_ruleB"].sum())
    negatives = total - positives
    counts_by_rule = df["imputation_rule"].fillna("none").value_counts().to_dict()
    counts_by_conf = df["label_confidence"].fillna("low").value_counts().to_dict()

    diag = {
        "total_projects": total,
        "will_delay_ruleB_positives": int(positives),
        "will_delay_ruleB_negatives": int(negatives),
        "imputed_count_ruleB": int(imputed_count),
        "counts_by_imputation_rule": counts_by_rule,
        "counts_by_label_confidence": counts_by_conf,
    }
    with open(OUT_DIAG, "w", encoding="utf-8") as f:
        f.write(json.dumps(diag, indent=2))

    # Prepare splits for will_delay_ruleB where label computed (planned_duration_days > 0 and elapsed present)
    computable = df[mask].copy()
    if len(computable) == 0:
        print("No computable rows for will_delay_ruleB; wrote diagnostics only.")
        return

    y = computable["will_delay_ruleB"].astype(int)
    X = computable.drop(
        columns=[
            "will_delay_ruleB",
            "will_delay",
            "will_delay_abs30",
            "will_delay_rel1pct",
            "will_delay_rel0pct",
        ],
        errors=True,
    )

    # Drop deny-list columns
    DENY = set(
        [
            c.lower()
            for c in [
                "will_delay",
                "schedule_slippage_pct",
                "award",
                "bbl",
                "bin",
                "cost",
                "cost_estimated",
            ]
        ]
    )
    for c in list(X.columns):
        if c.lower() in DENY:
            X.drop(columns=[c], inplace=True, errors=True)

    # Split
    stratify = y if y.nunique() > 1 and y.sum() > 0 else None
    if len(X) < 2:
        X_train = X.copy()
        X_test = X.iloc[0:0].copy()
        y_train = y.copy()
        y_test = y.iloc[0:0].copy()
    else:
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=stratify
            )
        except Exception:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

    X_train.to_csv(OUT_DIR / "X_train_ruleB.csv", index=False)
    X_test.to_csv(OUT_DIR / "X_test_ruleB.csv", index=False)
    y_train.to_frame("will_delay_ruleB").to_csv(
        OUT_DIR / "y_train_ruleB.csv", index=False
    )
    y_test.to_frame("will_delay_ruleB").to_csv(
        OUT_DIR / "y_test_ruleB.csv", index=False
    )

    # Filtered splits excluding low-confidence
    filtered = computable[
        computable["label_confidence"].isin(["high", "medium"])
    ].copy()
    if len(filtered) > 0:
        yf = filtered["will_delay_ruleB"].astype(int)
        Xf = filtered.drop(
            columns=[
                "will_delay_ruleB",
                "will_delay",
                "will_delay_abs30",
                "will_delay_rel1pct",
                "will_delay_rel0pct",
            ],
            errors=True,
        )
        for c in list(Xf.columns):
            if c.lower() in DENY:
                Xf.drop(columns=[c], inplace=True, errors=True)
        if len(Xf) < 2:
            Xf_train = Xf.copy()
            Xf_test = Xf.iloc[0:0].copy()
            yf_train = yf.copy()
            yf_test = yf.iloc[0:0].copy()
        else:
            try:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(
                    Xf,
                    yf,
                    test_size=0.2,
                    random_state=42,
                    stratify=(yf if yf.nunique() > 1 and yf.sum() > 0 else None),
                )
            except Exception:
                Xf_train, Xf_test, yf_train, yf_test = train_test_split(
                    Xf, yf, test_size=0.2, random_state=42
                )
        Xf_train.to_csv(OUT_DIR / "X_train_ruleB_filtered.csv", index=False)
        Xf_test.to_csv(OUT_DIR / "X_test_ruleB_filtered.csv", index=False)
        yf_train.to_frame("will_delay_ruleB").to_csv(
            OUT_DIR / "y_train_ruleB_filtered.csv", index=False
        )
        yf_test.to_frame("will_delay_ruleB").to_csv(
            OUT_DIR / "y_test_ruleB_filtered.csv", index=False
        )

    # Update model card
    model_card = ROOT / "MODEL_CARD_relaxed.md"
    add_text = "\n## Rule B cohort median imputation\n- For projects with collapsed planned windows, replace `planned_duration_days` with the cohort median planned duration (per `project_type` when available, otherwise global median).\n- For projects with collapsed planned windows or missing `actual_start`, impute `actual_start = actual_end - median_planned_duration` where median is computed per `project_type` when available, otherwise global median.\n- Imputed rows are flagged with `actual_start_imputed=True`, `imputation_rule=RuleB`, and `label_confidence=low`.\n- Delay and `will_delay_ruleB` are computed only where `planned_duration_days > 0`.\n"
    if model_card.exists():
        with model_card.open("a", encoding="utf-8") as f:
            f.write(add_text)
    else:
        with model_card.open("w", encoding="utf-8") as f:
            f.write("# Model Card - v8 relaxed baseline\n")
            f.write(add_text)

    # Write diagnostics already saved
    print("Applied Rule B imputation, wrote diagnostics and splits to", OUT_DIR)


if __name__ == "__main__":
    main()
