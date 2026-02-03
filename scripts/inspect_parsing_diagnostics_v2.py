import pandas as pd
import json
import os

AGG_PATH = os.path.join("data_splits", "project_level_aggregated_v8.csv")
ROWS_PATH = os.path.join("data_splits", "project_dataset_v7_cleaned.csv")
FALLBACKS_PATH = os.path.join("data_splits", "v8", "parse_fallbacks.json")
OUT_PATH = os.path.join("data_splits", "v8", "parsing_diagnostics_sample10_v2.csv")

CANDIDATE_COLS = [
    "DateFiled",
    "DatePermit",
    "Project Phase Planned Start Date",
    "Project Phase Planned End Date",
    "Project Phase Actual Start Date",
    "Project Phase Actual End Date",
    "PermitYear",
    "CompltYear",
    "DateComplt",
]

AGG_COLUMNS_OF_INTEREST = [
    "planned_start",
    "planned_end",
    "actual_start",
    "actual_end",
    "actual_start_imputed",
    "planned_duration_days",
    "elapsed_days",
    "delay_days",
    "schedule_slippage_pct",
    "will_delay",
    "will_delay_abs30",
    "will_delay_rel5pct",
]


def collapse_unique_values(df, col):
    if col not in df.columns:
        return ""
    vals = df[col].dropna().astype(str).unique()
    if len(vals) == 0:
        return ""
    return " | ".join(sorted(vals))


def main(sample_size=10):
    agg = pd.read_csv(AGG_PATH, low_memory=False)
    rows = pd.read_csv(ROWS_PATH, low_memory=False, dtype=str)

    with open(FALLBACKS_PATH, "r", encoding="utf-8") as f:
        fallbacks_list = json.load(f)

    # ensure list
    if isinstance(fallbacks_list, dict):
        fallbacks_list = list(fallbacks_list.values())

    sample = fallbacks_list[:sample_size]

    diagnostics = []
    for item in sample:
        pid = str(item.get("project_id"))
        subset = rows[rows["project_id"].astype(str) == pid]
        entry = {"project_id": pid}
        for col in CANDIDATE_COLS:
            entry[f"raw__{col}"] = collapse_unique_values(subset, col)

        agg_row = agg[agg["project_id"].astype(str) == pid]
        if len(agg_row) > 0:
            for col in AGG_COLUMNS_OF_INTEREST:
                entry[col] = agg_row.iloc[0].get(col, "")
        else:
            for col in AGG_COLUMNS_OF_INTEREST:
                entry[col] = ""

        # compact fallback info
        try:
            used = item.get("used", {})
            year_only = item.get("year_only_parse", [])
            imputed = item.get("actual_start_imputed", False)
            entry["parse_fallback_summary"] = (
                f"used_keys={list(used.keys())}; year_only={year_only}; actual_start_imputed={imputed}"
            )
        except Exception:
            entry["parse_fallback_summary"] = str(item)

        diagnostics.append(entry)

    diag_df = pd.DataFrame(diagnostics)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    diag_df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(diag_df)} diagnostic rows to {OUT_PATH}")


if __name__ == "__main__":
    main()
