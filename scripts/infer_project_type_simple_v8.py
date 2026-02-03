from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(".")
RELAXED = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed.csv"
OUT = ROOT / "data_splits" / "project_level_aggregated_v8_relaxed_with_types.csv"
OUT_DIAG = ROOT / "data_splits" / "v8" / "diagnostics_project_type_inferred.txt"


def detect_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    # case-insensitive match
    lowcols = {col.lower(): col for col in df.columns}
    for c in candidates:
        if c.lower() in lowcols:
            return lowcols[c.lower()]
    return None


KEYWORD_MAP = [
    (
        ["high school", "hs", "school", "elementary", "middle school", "primary"],
        "School",
    ),
    (["hospital", "clinic", "medical", "health", "urgent care"], "Hospital"),
    (["bridge"], "Bridge"),
    (["library"], "Library"),
    (["park", "playground", "recreation"], "Park"),
    (["residential", "housing", "apartments", "senior"], "Residential"),
    (["police", "precinct"], "Police"),
    (["fire", "firehouse", "fire station"], "Fire"),
    (["road", "street", "highway", "pavement"], "Road"),
    (["transit", "subway", "station", "rail", "bus"], "Transit"),
]


def infer_type(text):
    if not isinstance(text, str):
        return None
    t = text.lower()
    for kws, label in KEYWORD_MAP:
        for kw in kws:
            if kw in t:
                return label
    return None


def main():
    if not RELAXED.exists():
        raise FileNotFoundError(RELAXED)
    df = pd.read_csv(RELAXED, dtype=str)

    # detect columns
    id_col = (
        detect_col(df, ["project_id", "Project ID", "ID", "projectId"]) or df.columns[0]
    )
    pt_col = detect_col(df, ["project_type", "Project Type", "Project Type "])
    name_col = (
        detect_col(
            df,
            [
                "Project School Name",
                "Title",
                "Project Description",
                "project_name",
                "project",
            ],
        )
        or id_col
    )

    # normalize project_type column name; if absent, create it
    if pt_col is None:
        df["project_type"] = np.nan
        pt_col = "project_type"

    missing_mask = df[pt_col].isna() | (df[pt_col].astype(str).str.strip() == "")
    to_infer_idx = df[missing_mask].index

    inferred = []
    for idx in to_infer_idx:
        text = ""
        if id_col in df.columns and isinstance(df.at[idx, id_col], str):
            text += df.at[idx, id_col] + " "
        if name_col in df.columns and isinstance(df.at[idx, name_col], str):
            text += df.at[idx, name_col]
        label = infer_type(text)
        if label:
            df.at[idx, pt_col] = label
            inferred.append(idx)

    # Save updated CSV
    df.to_csv(OUT, index=False)

    # Diagnostics
    total = len(df)
    inferred_count = len(inferred)
    still_missing = int(
        ((df[pt_col].isna()) | (df[pt_col].astype(str).str.strip() == "")).sum()
    )
    counts_by_rule = (
        df.get("imputation_rule", pd.Series()).fillna("none").value_counts().to_dict()
    )
    counts_by_conf = (
        df.get("label_confidence", pd.Series()).fillna("low").value_counts().to_dict()
    )

    OUT_DIAG.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIAG, "w", encoding="utf-8") as f:
        f.write(f"Total projects: {total}\n")
        f.write(f"Projects with inferred project_type: {inferred_count}\n")
        f.write(f"Projects still missing project_type: {still_missing}\n")
        f.write("\nCounts by imputation_rule:\n")
        for k, v in counts_by_rule.items():
            f.write(f" - {k}: {int(v)}\n")
        f.write("\nCounts by label_confidence:\n")
        for k, v in counts_by_conf.items():
            f.write(f" - {k}: {int(v)}\n")

    print("Wrote updated CSV to", OUT)
    print("Wrote diagnostics to", OUT_DIAG)


if __name__ == "__main__":
    main()
