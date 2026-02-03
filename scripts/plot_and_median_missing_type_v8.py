from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
RELAXED = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
RULEB = ROOT / "data_splits" / "project_level_aggregated_v8_ruleB_imputed.csv"
OUT_MISSING = ROOT / "data_splits" / "v8" / "projects_missing_type.csv"
OUT_DIAG = (
    ROOT / "data_splits" / "v8" / "diagnostics_global_median_and_missing_type.txt"
)
OUT_PLOT = ROOT / "data_splits" / "v8" / "planned_duration_distribution.png"


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
    if not RELAXED.exists():
        raise FileNotFoundError(RELAXED)
    relaxed = pd.read_csv(RELAXED, dtype=str)

    # normalize planned_duration_days
    relaxed["planned_duration_days"] = pd.to_numeric(
        relaxed.get("planned_duration_days"), errors="coerce"
    )
    vals = relaxed["planned_duration_days"].dropna()
    vals = vals[vals > 0]

    # compute global median from valid rows (>0)
    if len(vals) > 0:
        global_median = float(vals.median())
    else:
        global_median = 365.0

    # print basic distribution summary
    percentiles = (
        np.percentile(vals, [0, 1, 5, 10, 25, 50, 75, 90, 95, 99, 100])
        if len(vals) > 0
        else []
    )

    # attempt to plot histogram
    plotted = False
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(6, 3))
        if len(vals) > 0:
            # cap values for plotting at 1825 for visibility
            plot_vals = vals.clip(upper=1825)
            plt.hist(plot_vals, bins=50, color="#4C72B0")
            plt.axvline(
                global_median,
                color="red",
                linestyle="--",
                label=f"median={global_median:.1f}",
            )
            plt.xlabel("planned_duration_days (capped at 1825)")
            plt.ylabel("count")
            plt.legend()
            plt.tight_layout()
            OUT_PLOT.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(OUT_PLOT, dpi=150)
            plt.close()
            plotted = True
    except Exception:
        plotted = False

    # identify missing project_type rows in relaxed
    pt_col = detect_project_type_col(relaxed)
    id_col = detect_id_col(relaxed)
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

    # diagnostics: totals from relaxed; imputation counts from RULEB if available
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
        total_imputed = (
            int((relaxed.get("imputation_rule", "") == "RuleB").sum())
            if "imputation_rule" in relaxed.columns
            else 0
        )
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

    # write diagnostics text
    with open(OUT_DIAG, "w", encoding="utf-8") as f:
        f.write(
            f"Global median planned_duration_days (from relaxed, >0): {global_median}\n"
        )
        f.write(f"Total projects (relaxed): {total_projects}\n")
        f.write(f"Total imputed (RuleB, from ruleB file): {total_imputed}\n")
        f.write(f"Projects missing project_type (relaxed): {missing_count}\n")
        f.write("\nCounts by imputation_rule (from ruleB if available):\n")
        for k, v in counts_by_rule.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nCounts by label_confidence (from ruleB if available):\n")
        for k, v in counts_by_conf.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write(
            "\nPlotted histogram saved to: {}\n".format(
                OUT_PLOT if plotted else "<not created>"
            )
        )
        f.write("projects_missing_type.csv written to: {}\n".format(OUT_MISSING))
        f.write("\nDistribution percentiles (0,1,5,10,25,50,75,90,95,99,100):\n")
        if len(percentiles) > 0:
            f.write(",".join([f"{p:.2f}" for p in percentiles]) + "\n")
        else:
            f.write("No valid planned_duration_days > 0 found in relaxed file.\n")

    # print/log to terminal
    print("Global median planned_duration_days (relaxed >0):", global_median)
    print("Total projects (relaxed):", total_projects)
    print("Total imputed (RuleB):", total_imputed)
    print("Projects missing project_type (relaxed):", missing_count)
    print("Counts by imputation_rule:", counts_by_rule)
    print("Counts by label_confidence:", counts_by_conf)
    if len(percentiles) > 0:
        print(
            "Percentiles (0,1,5,10,25,50,75,90,95,99,100):",
            ",".join([f"{p:.2f}" for p in percentiles]),
        )
    if plotted:
        print("Histogram saved to", OUT_PLOT)


if __name__ == "__main__":
    main()
