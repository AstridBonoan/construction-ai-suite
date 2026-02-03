import pandas as pd
import sys
from pathlib import Path

# Source CSV — adjust if your filename differs
SRC = Path(
    "data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv"
)
OUT = Path("data_splits/project_level_for_monday.csv")


def main():
    if not SRC.exists():
        print(f"ERROR: source file not found: {SRC}", file=sys.stderr)
        sys.exit(2)

    df = pd.read_csv(SRC)

    # Minimal required columns for Monday mapping
    # Map your actual column names here if different
    # Priority: project_id, predicted_delay, revenue, risk, status
    # Try common names, then fallback to defaults
    col_project = None
    for c in ("project_id", "projectId", "id", "projectId_original"):
        if c in df.columns:
            col_project = c
            break
    if col_project is None:
        print("ERROR: could not find a project_id column in source", file=sys.stderr)
        sys.exit(2)

    # predicted delay
    pred_col = None
    for c in (
        "predicted_delay",
        "predicted_delay_days",
        "delay_pred",
        "delay_days_pred",
        "delay_days",
    ):
        if c in df.columns:
            pred_col = c
            break

    revenue_col = None
    for c in ("revenue", "project_revenue", "budget"):
        if c in df.columns:
            revenue_col = c
            break

    risk_col = None
    for c in ("risk", "risk_score", "leakage_risk"):
        if c in df.columns:
            risk_col = c
            break

    status_col = None
    for c in ("status", "current_status", "project_status"):
        if c in df.columns:
            status_col = c
            break

    out = pd.DataFrame()
    out["project_id"] = df[col_project].astype(str)
    out["predicted_delay"] = df[pred_col] if pred_col else 0
    out["revenue"] = df[revenue_col] if revenue_col else ""
    out["risk"] = df[risk_col] if risk_col else ""
    out["status"] = df[status_col] if status_col else ""

    # Data integrity checks
    if out["project_id"].isnull().any():
        print("ERROR: null project_id present", file=sys.stderr)
        sys.exit(2)

    # ensure no problematic NA in predicted_delay
    if out["predicted_delay"].isnull().any():
        print("WARNING: some predicted_delay are null — filling with 0")
        out["predicted_delay"] = out["predicted_delay"].fillna(0)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Transformed {len(out)} rows to {OUT}")


if __name__ == "__main__":
    main()
