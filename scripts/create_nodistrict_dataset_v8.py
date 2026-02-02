import pandas as pd
from pathlib import Path

SRC = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak.csv")
OUT = Path("data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv")

DROP_COL = 'Project Geographic District'

def main():
    df = pd.read_csv(SRC, low_memory=False)
    # normalize column names (strip) to find variations
    cols = [c for c in df.columns]
    cols_stripped = [str(c).strip() for c in cols]
    df.columns = cols_stripped
    if DROP_COL in df.columns:
        df = df.drop(columns=[DROP_COL])
        df.to_csv(OUT, index=False)
        print(f"Wrote nodistrict dataset to {OUT}")
    else:
        # if exact match not found, drop any column that contains the phrase
        matches = [c for c in df.columns if DROP_COL in c]
        if matches:
            df = df.drop(columns=matches)
            df.to_csv(OUT, index=False)
            print(f"Dropped columns {matches} and wrote nodistrict dataset to {OUT}")
        else:
            print(f"Column {DROP_COL} not found in {SRC}; copying original to {OUT}")
            df.to_csv(OUT, index=False)


if __name__ == '__main__':
    main()
