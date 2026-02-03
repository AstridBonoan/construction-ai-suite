from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
RULEB = ROOT / "data_splits" / "project_level_aggregated_v8_ruleB_imputed.csv"
RELAXED = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT_CSV = (
    ROOT / "data_splits" / "v8" / "project_type_median_planned_duration_summary.csv"
)
OUT_TXT = (
    ROOT / "data_splits" / "v8" / "project_type_median_planned_duration_summary.txt"
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


def main():
    if not RULEB.exists():
        raise FileNotFoundError(f"Missing: {RULEB}")

    ruleb = pd.read_csv(RULEB, dtype=str)
    ruleb_cols = ruleb.columns.tolist()
    id_col = detect_id_col(ruleb)
    pt_col = detect_project_type_col(ruleb)

    # numeric planned_duration in ruleb
    ruleb["planned_duration_days"] = pd.to_numeric(
        ruleb.get("planned_duration_days"), errors="coerce"
    )

    # Compute medians from RELAXED if available (as original imputation source)
    medians = {}
    global_median = np.nan
    if RELAXED.exists():
        relaxed = pd.read_csv(RELAXED, dtype=str)
        relaxed["planned_duration_days"] = pd.to_numeric(
            relaxed.get("planned_duration_days"), errors="coerce"
        )
        # cap >1825
        relaxed.loc[
            relaxed["planned_duration_days"] > 1825, "planned_duration_days"
        ] = np.nan
        if pt_col and pt_col in relaxed.columns:
            groups = relaxed.groupby(relaxed[pt_col].fillna(""))
            for k, g in groups:
                vals = g["planned_duration_days"].dropna()
                vals = vals[(vals > 0) & (vals <= 1825)]
                medians[k if k != "" else None] = (
                    float(vals.median()) if len(vals) > 0 else np.nan
                )
        global_vals = relaxed["planned_duration_days"].dropna()
        global_vals = global_vals[(global_vals > 0) & (global_vals <= 1825)]
        global_median = float(global_vals.median()) if len(global_vals) > 0 else np.nan
    else:
        # fallback: compute from ruleb rows not imputed (imputation_rule != RuleB)
        ruleb["planned_duration_days_source"] = ruleb["planned_duration_days"]
        if pt_col and pt_col in ruleb.columns:
            groups = ruleb[ruleb.get("imputation_rule", "") != "RuleB"].groupby(
                ruleb[pt_col].fillna("")
            )
            for k, g in groups:
                vals = pd.to_numeric(
                    g["planned_duration_days"], errors="coerce"
                ).dropna()
                vals = vals[(vals > 0) & (vals <= 1825)]
                medians[k if k != "" else None] = (
                    float(vals.median()) if len(vals) > 0 else np.nan
                )
        global_vals = pd.to_numeric(
            ruleb[ruleb.get("imputation_rule", "") != "RuleB"]["planned_duration_days"],
            errors="coerce",
        ).dropna()
        global_vals = global_vals[(global_vals > 0) & (global_vals <= 1825)]
        global_median = float(global_vals.median()) if len(global_vals) > 0 else np.nan

    # Build summary table from project_type values present in ruleb
    if pt_col and pt_col in ruleb.columns:
        ruleb_pt = ruleb[pt_col].fillna("")
        types = ruleb_pt.unique().tolist()
    else:
        ruleb_pt = pd.Series([""] * len(ruleb), index=ruleb.index)
        types = [""]

    rows = []
    for t in types:
        key = t if t != "" else None
        median = medians.get(t if t != "" else None, np.nan)
        if np.isnan(median):
            median = global_median
        count_projects = int((ruleb_pt == (t if t is not None else "")).sum())
        # imputed planned: original planned missing or <=0 and current planned_duration_days >0
        # attempt to merge original planned if RELAXED exists
        imputed_count = 0
        if RELAXED.exists():
            relaxed = pd.read_csv(RELAXED, dtype=str)
            relaxed["planned_duration_days"] = pd.to_numeric(
                relaxed.get("planned_duration_days"), errors="coerce"
            )
            merged = ruleb.merge(
                relaxed[[id_col, "planned_duration_days"]],
                how="left",
                on=id_col,
                suffixes=("", "_orig"),
            )
            orig = merged["planned_duration_days_orig"]
            imp = merged["planned_duration_days"]
            merged_pt = (
                merged[pt_col].fillna("")
                if pt_col and pt_col in merged.columns
                else pd.Series([""] * len(merged), index=merged.index)
            )
            mask = (
                (merged_pt == (t if t is not None else ""))
                & ((orig.isna()) | (orig <= 0))
                & (imp.notna() & (imp > 0))
            )
            imputed_count = int(mask.sum())
        else:
            # conservative: count rows with imputation_rule == RuleB for this type
            imputed_count = int(
                (
                    (ruleb_pt == (t if t is not None else ""))
                    & (ruleb.get("imputation_rule", "") == "RuleB")
                ).sum()
            )

        rows.append(
            {
                "project_type": (t if t != "" else "<unknown>"),
                "median_planned_duration_days": (
                    float(median) if not np.isnan(median) else np.nan
                ),
                "count_projects": count_projects,
                "count_imputed_planned_duration": imputed_count,
            }
        )

    out_df = pd.DataFrame(rows).sort_values(
        by="count_imputed_planned_duration", ascending=False
    )
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)

    # Overall diagnostics
    total_projects = len(ruleb)
    total_imputed = int(
        (
            (ruleb.get("imputation_rule", "") == "RuleB")
            | (
                (pd.to_numeric(ruleb.get("planned_duration_days"), errors="coerce") > 0)
                & True
            )
        ).sum()
    )
    counts_by_rule = ruleb["imputation_rule"].fillna("none").value_counts().to_dict()
    counts_by_conf = ruleb["label_confidence"].fillna("low").value_counts().to_dict()

    with open(OUT_TXT, "w", encoding="utf-8") as f:
        f.write(f"Total projects: {total_projects}\n")
        f.write(
            f'Total imputed (imputation_rule==RuleB): {int((ruleb.get("imputation_rule","")=="RuleB").sum())}\n'
        )
        f.write("\nPer-project-type medians and counts (see CSV):\n")
        for _, r in out_df.iterrows():
            f.write(
                f" - {r['project_type']}: median={r['median_planned_duration_days']}, count={int(r['count_projects'])}, imputed={int(r['count_imputed_planned_duration'])}\n"
            )
        f.write("\nCounts by imputation_rule:\n")
        for k, v in counts_by_rule.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nCounts by label_confidence:\n")
        for k, v in counts_by_conf.items():
            f.write(f" - {k}: {int(v)}\n")

    print("Wrote per-project-type median summary to", OUT_CSV)
    print("Wrote diagnostics to", OUT_TXT)


if __name__ == "__main__":
    main()
