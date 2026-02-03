import pandas as pd
from pathlib import Path

SRC = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded.csv")
OUT = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak.csv")

# Conservative blacklist (explicit names and prefixes)
BLACKLIST_EXACT = {
    "elapsed_days",
    "schedule_slippage_pct",
    "actual_start",
    "actual_end",
    "actual_start_imputed",
}
BLACKLIST_PREFIXES = (
    "will_delay",
    "actual_",
)


def should_keep(col: str) -> bool:
    if col in BLACKLIST_EXACT:
        return False
    for p in BLACKLIST_PREFIXES:
        if col.startswith(p):
            return False
    return True


def main():
    df = pd.read_csv(SRC, low_memory=False)
    cols_keep = [c for c in df.columns if should_keep(c)]
    df_clean = df[cols_keep].copy()
    df_clean.to_csv(OUT, index=False)
    print(
        f"Wrote cleaned no-leak dataset to {OUT} (kept {len(cols_keep)} of {len(df.columns)} columns)"
    )


if __name__ == "__main__":
    main()
