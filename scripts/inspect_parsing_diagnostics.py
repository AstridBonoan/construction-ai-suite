import pandas as pd
import json
import os

AGG_PATH = os.path.join('data_splits', 'project_level_aggregated_v8.csv')
ROWS_PATH = os.path.join('data_splits', 'project_dataset_v7_cleaned.csv')
FALLBACKS_PATH = os.path.join('data_splits', 'v8', 'parse_fallbacks.json')
OUT_PATH = os.path.join('data_splits', 'v8', 'parsing_diagnostics_sample10.csv')

CANDIDATE_COLS = [
    'DateFiled', 'DatePermit',
    'Project Phase Planned Start Date', 'Project Phase Planned End Date',
    'Project Phase Actual Start Date', 'Project Phase Actual End Date',
    'PermitYear', 'CompltYear', 'DateComplt'
]

AGG_COLUMNS_OF_INTEREST = [
    'planned_start','planned_end','actual_start','actual_end','actual_start_imputed',
    'planned_duration_days','elapsed_days','delay_days','schedule_slippage_pct',
    'will_delay','will_delay_abs30','will_delay_rel5pct'
]


def collapse_unique_values(df, group_col, target_col):
    vals = df[target_col].dropna().astype(str).unique()
    if len(vals) == 0:
        return ''
    return ' | '.join(sorted(vals))


def main(sample_size=10):
    agg = pd.read_csv(AGG_PATH, low_memory=False)
    rows = pd.read_csv(ROWS_PATH, low_memory=False, dtype=str)

    # load parse fallbacks safely
    try:
        with open(FALLBACKS_PATH, 'r', encoding='utf-8') as f:
            fallbacks = json.load(f)
    except Exception:
        fallbacks = {}
    # parse_fallbacks.json may be a list of dicts; convert to mapping by project_id
    if isinstance(fallbacks, list):
        try:
            fallbacks = {str(item.get('project_id')): item for item in fallbacks}
        except Exception:
            # fallback to empty mapping if unexpected structure
            fallbacks = {}

    sample_project_ids = list(agg['project_id'].astype(str).unique())[:sample_size]
    if len(sample_project_ids) == 0 and isinstance(fallbacks, dict):
        sample_project_ids = list(fallbacks.keys())[:sample_size]

    diagnostics = []
    for pid in sample_project_ids:
        entry = {'project_id': pid}
        subset = rows[rows['project_id'].astype(str) == str(pid)]

        for col in CANDIDATE_COLS:
            if col in subset.columns:
                entry[f'raw__{col}'] = collapse_unique_values(subset, 'project_id', col)
            else:
                entry[f'raw__{col}'] = ''

        # add aggregated parsed outputs (if present)
        agg_row = agg[agg['project_id'].astype(str) == str(pid)]
        if len(agg_row) > 0:
            for col in AGG_COLUMNS_OF_INTEREST:
                entry[col] = agg_row.iloc[0].get(col, '')
        else:
            for col in AGG_COLUMNS_OF_INTEREST:
                entry[col] = ''

        # include parse fallback summary
        fb = fallbacks.get(str(pid), {})
        # keep a compact string of keys that indicate imputation/parse choices
        try:
            fb_summary = []
            if isinstance(fb, dict):
                for k, v in fb.items():
                    if isinstance(v, (str, int, float)):
                        fb_summary.append(f"{k}={v}")
                    else:
                        fb_summary.append(f"{k}")
            else:
                fb_summary = [str(fb)]
            entry['parse_fallback_summary'] = ' ; '.join(fb_summary)
        except Exception:
            entry['parse_fallback_summary'] = str(fb)

        diagnostics.append(entry)

    diag_df = pd.DataFrame(diagnostics)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    diag_df.to_csv(OUT_PATH, index=False)

    print(f"Wrote diagnostics for {len(diag_df)} projects to {OUT_PATH}")
    # print a tiny preview
    print(diag_df.head(5).to_string())


if __name__ == '__main__':
    main()
