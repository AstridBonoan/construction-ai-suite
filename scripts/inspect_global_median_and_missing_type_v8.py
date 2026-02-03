from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
RULEB = ROOT / "data_splits" / "project_level_aggregated_v8_ruleB_imputed.csv"
RELAXED = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT_MISSING = ROOT / "data_splits" / "v8" / "projects_missing_type.csv"
OUT_DIAG = (
    ROOT / "data_splits" / "v8" / "diagnostics_global_median_and_missing_type.txt"
)


def detect_project_type_col(df):
    for candidate in ["project_type", "type", "Project Type", "projectType"]:
        if candidate in df.columns:
            return candidate
    return None


def detect_id_col(df):
    for candidate in ["project_id", "projectId", "id", "ID", "ID_"]:
        if candidate in df.columns:
            return candidate
    return df.columns[0]


def compute_global_median():
    # prefer RELAXED planned durations
    if RELAXED.exists():
        r = pd.read_csv(RELAXED, dtype=str)
        r["planned_duration_days"] = pd.to_numeric(
            r.get("planned_duration_days"), errors="coerce"
        )
        vals = r["planned_duration_days"].dropna()
        vals = vals[(vals > 0) & (vals <= 1825)]
        if len(vals) > 0:
            return float(vals.median())
    # fallback: try from RULEB non-RuleB rows
    if RULEB.exists():
        rb = pd.read_csv(RULEB, dtype=str)
        rb["planned_duration_days"] = pd.to_numeric(
            rb.get("planned_duration_days"), errors="coerce"
        )
        vals = rb[rb.get("imputation_rule", "") != "RuleB"][
            "planned_duration_days"
        ].dropna()
        vals = vals[(vals > 0) & (vals <= 1825)]
        if len(vals) > 0:
            return float(vals.median())
    # final fallback
    return 365.0


def main():
    # Load relaxed aggregated CSV for median computation and missing-type inspection
    if not RELAXED.exists():
        raise FileNotFoundError(RELAXED)
    relaxed = pd.read_csv(RELAXED, dtype=str)

    id_col = detect_id_col(relaxed)
    pt_col = detect_project_type_col(relaxed)

    global_median = compute_global_median()

    # identify missing project_type rows in the relaxed file
    if pt_col and pt_col in relaxed.columns:
        missing_mask = relaxed[pt_col].isna() | (
            relaxed[pt_col].astype(str).str.strip() == ""
        )
    else:
        missing_mask = pd.Series([True] * len(relaxed), index=relaxed.index)

    missing = relaxed.loc[
        missing_mask,
        [
            id_col,
            "planned_start",
            "planned_end",
            "actual_start",
            "actual_end",
            "actual_start_imputed",
            "imputation_rule",
        ],
    ].copy()
    OUT_MISSING.parent.mkdir(parents=True, exist_ok=True)
    missing.to_csv(OUT_MISSING, index=False)
    # diagnostics: totals come from relaxed for project counts; imputation counts from RULEB if available
    total_projects = len(relaxed)
    if RULEB.exists():
        ruleb = pd.read_csv(RULEB, dtype=str)
        total_imputed = int((ruleb.get("imputation_rule", "") == "RuleB").sum())
        counts_by_rule = (
            ruleb["imputation_rule"].fillna("none").value_counts().to_dict()
        )
        counts_by_conf = (
            ruleb["label_confidence"].fillna("low").value_counts().to_dict()
        )
    else:
        total_imputed = 0
        counts_by_rule = (
            relaxed.get("imputation_rule", pd.Series())
            .fillna("none")
            .value_counts()
            .to_dict()
        )
        counts_by_conf = (
            relaxed.get("label_confidence", pd.Series())
            .fillna("low")
            .value_counts()
            .to_dict()
        )
    missing_count = int(missing.shape[0])

    with open(OUT_DIAG, "w", encoding="utf-8") as f:
        f.write(
            f"Global median planned_duration_days used (fallback logic): {global_median}\n"
        )
        f.write(f"Total projects: {total_projects}\n")
        f.write(f"Total imputed (imputation_rule==RuleB): {total_imputed}\n")
        f.write(f"Projects missing project_type: {missing_count}\n")
        f.write("\nCounts by imputation_rule:\n")
        for k, v in counts_by_rule.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nCounts by label_confidence:\n")
        for k, v in counts_by_conf.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write(f"\nprojects_missing_type.csv written to: {OUT_MISSING}\n")

    print("Global median:", global_median)
    print("Wrote", OUT_MISSING)
    print("Wrote", OUT_DIAG)


if __name__ == "__main__":
    main()
