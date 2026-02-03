from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
RELAXED = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
RULEB = ROOT / "data_splits" / "project_level_aggregated_v8_ruleB_imputed.csv"
OUT_CSV = ROOT / "data_splits" / "v8" / "project_level_ruleB_imputation_summary.csv"
OUT_TXT = ROOT / "data_splits" / "v8" / "project_level_ruleB_imputation_summary.txt"
OUT_SAMPLE = ROOT / "data_splits" / "v8" / "project_level_ruleB_imputation_sample.csv"


def detect_project_type_col(df):
    for candidate in ["project_type", "type", "Project Type", "projectType"]:
        if candidate in df.columns:
            return candidate
    return None


def detect_id_col(df):
    for candidate in ["project_id", "projectId", "id", "ID", "ID_"]:
        if candidate in df.columns:
            return candidate
    # fallback to first column
    return df.columns[0]


def main():
    if not RELAXED.exists():
        raise FileNotFoundError(RELAXED)
    if not RULEB.exists():
        raise FileNotFoundError(RULEB)

    relaxed = pd.read_csv(RELAXED, dtype=str)
    ruleb = pd.read_csv(RULEB, dtype=str)

    id_col = detect_id_col(ruleb)
    pt_col = detect_project_type_col(ruleb) or detect_project_type_col(relaxed)

    # normalize numeric planned_duration
    relaxed["planned_duration_days"] = pd.to_numeric(
        relaxed.get("planned_duration_days"), errors="coerce"
    )
    ruleb["planned_duration_days"] = pd.to_numeric(
        ruleb.get("planned_duration_days"), errors="coerce"
    )

    # Merge on id_col (left from ruleb)
    merged = ruleb.merge(
        relaxed[[id_col, "planned_duration_days"]],
        how="left",
        on=id_col,
        suffixes=("_imputed", "_original"),
    )
    merged.rename(
        columns={
            "planned_duration_days_imputed": "imputed_planned_duration_days",
            "planned_duration_days_original": "original_planned_duration_days",
        },
        inplace=True,
    )

    # pick project_type if present
    if pt_col and pt_col in merged.columns:
        merged["project_type"] = merged[pt_col].fillna("")
    else:
        merged["project_type"] = ""

    # Ensure needed columns exist
    for col in [
        "actual_start",
        "actual_end",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
        "imputation_rule",
        "actual_start_imputed",
        "label_confidence",
    ]:
        if col not in merged.columns:
            merged[col] = np.nan

    # determine where cohort median planned-duration was applied
    orig = merged["original_planned_duration_days"]
    imp = merged["imputed_planned_duration_days"]
    applied = ((orig.isna() | (orig <= 0)) & (imp.notna() & (imp > 0))) | (
        merged["imputation_rule"] == "RuleB"
    )

    merged["imputed_planned_applied"] = applied.astype(bool)

    # select summary columns
    summary_cols = [
        id_col,
        "project_type",
        "original_planned_duration_days",
        "imputed_planned_duration_days",
        "actual_start",
        "actual_end",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
        "imputation_rule",
        "actual_start_imputed",
        "label_confidence",
        "imputed_planned_applied",
    ]

    summary = merged[[c for c in summary_cols if c in merged.columns]].copy()

    # counts per project_type
    counts_by_pt = (
        summary.groupby("project_type")["imputed_planned_applied"]
        .sum()
        .sort_values(ascending=False)
        .to_dict()
    )

    # diagnostics
    total_projects = len(summary)
    total_imputed_planned = int(summary["imputed_planned_applied"].sum())
    will_delay_pos = int(
        pd.to_numeric(merged.get("will_delay_ruleB", 0), errors="coerce")
        .fillna(0)
        .astype(int)
        .sum()
    )
    counts_by_rule = merged["imputation_rule"].fillna("none").value_counts().to_dict()
    counts_by_conf = merged["label_confidence"].fillna("low").value_counts().to_dict()

    # sample changed projects
    # detect actual_start change by comparing to relaxed actual_start where possible
    relaxed_idxed = relaxed.set_index(id_col)
    relaxed_actual_start = (
        relaxed_idxed.reindex(merged[id_col]).get("actual_start")
        if id_col in relaxed_idxed.columns
        else pd.Series([None] * len(merged))
    )
    changed = summary[
        (summary["imputed_planned_applied"])
        | (merged["actual_start"].fillna("") != relaxed_actual_start.fillna(""))
    ]
    sample = changed.head(10).copy()

    # write outputs
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUT_CSV, index=False)
    sample.to_csv(OUT_SAMPLE, index=False)

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(f"Total projects: {total_projects}\n")
        f.write(
            f"Projects with imputed planned_duration (cohort median applied): {total_imputed_planned}\n"
        )
        f.write(f"will_delay_ruleB positives: {will_delay_pos}\n")
        f.write("\nCounts by project_type (imputed planned applied):\n")
        for k, v in counts_by_pt.items():
            f.write(f' - {k if k!="" else "<unknown>"}: {int(v)}\n')
        f.write("\nCounts by imputation_rule:\n")
        for k, v in counts_by_rule.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nCounts by label_confidence:\n")
        for k, v in counts_by_conf.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nSample of changed projects saved to: {}\n".format(OUT_SAMPLE))

    print("Wrote summary CSV to", OUT_CSV)
    print("Wrote diagnostics to", OUT_TXT)
    print("Wrote sample CSV to", OUT_SAMPLE)


if __name__ == "__main__":
    main()
