"""Annotate Rule A aggregated CSV with imputation_rule and label_confidence.

Reads: data_splits/project_level_aggregated_v8_ruleA.csv
Writes:
- data_splits/project_level_aggregated_v8_ruleA_annotated.csv
- data_splits/v8/diagnostics_ruleA_annotated.txt
"""

from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
IN_CSV = ROOT / "data_splits" / "project_level_aggregated_v8_ruleA.csv"
OUT_CSV = ROOT / "data_splits" / "project_level_aggregated_v8_ruleA_annotated.csv"
OUT_SUM = ROOT / "data_splits" / "v8" / "diagnostics_ruleA_annotated.txt"


def to_dt(val):
    try:
        return pd.to_datetime(val, errors="coerce")
    except Exception:
        return pd.NaT


def main():
    df = pd.read_csv(IN_CSV, dtype=str)
    df = df.copy()

    # Ensure boolean column exists
    if "actual_start_imputed" not in df.columns:
        df["actual_start_imputed"] = False

    imputation_rules = []
    label_confidences = []

    for _, r in df.iterrows():
        imputed = str(r.get("actual_start_imputed")).strip().lower() in (
            "1",
            "true",
            "t",
            "yes",
        )
        ps = to_dt(r.get("planned_start"))
        pe = to_dt(r.get("planned_end"))

        planned_full = (not pd.isna(ps)) and (not pd.isna(pe)) and (ps != pe)
        planned_duration = np.nan
        if planned_full:
            planned_duration = (pe - ps).days

        if imputed:
            # Determine if Rule A or median fallback
            if (
                planned_full
                and (not pd.isna(planned_duration))
                and planned_duration <= 1825
            ):
                imputation_rules.append("Rule A full-date planned window")
                label_confidences.append("high")
            else:
                imputation_rules.append("median fallback")
                label_confidences.append("low")
        else:
            imputation_rules.append("none")
            label_confidences.append("original")

    df["imputation_rule"] = imputation_rules
    df["label_confidence"] = label_confidences

    # write annotated CSV
    df.to_csv(OUT_CSV, index=False)

    # diagnostics counts
    total = len(df)
    counts_by_rule = df["imputation_rule"].value_counts(dropna=False).to_dict()
    counts_by_conf = df["label_confidence"].value_counts(dropna=False).to_dict()

    with OUT_SUM.open("w", encoding="utf-8") as f:
        f.write(f"total_projects={total}\n")
        f.write("counts_by_imputation_rule:\n")
        for k, v in counts_by_rule.items():
            f.write(f"  {k}={v}\n")
        f.write("counts_by_label_confidence:\n")
        for k, v in counts_by_conf.items():
            f.write(f"  {k}={v}\n")

    print("Wrote annotated CSV to", OUT_CSV)
    print("Wrote diagnostics to", OUT_SUM)


if __name__ == "__main__":
    main()
