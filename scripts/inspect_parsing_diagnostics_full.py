import pandas as pd
import json
import os
from datetime import datetime

AGG_PATH = os.path.join('data_splits', 'project_level_aggregated_v8.csv')
ROWS_PATH = os.path.join('data_splits', 'project_dataset_v7_cleaned.csv')
FALLBACKS_PATH = os.path.join('data_splits', 'v8', 'parse_fallbacks.json')
OUT_CSV = os.path.join('data_splits', 'v8', 'parsing_diagnostics_full.csv')
OUT_SUM = os.path.join('data_splits', 'v8', 'parsing_diagnostics_full_summary.txt')

# columns to capture from row-level raw data
RAW_CANDIDATES = [
    'Project Phase Planned Start Date', 'Project Phase Planned End Date',
    'Project Phase Actual Start Date', 'Project Phase Actual End Date',
    'PermitYear', 'CompltYear', 'DateFiled', 'DatePermit', 'DateComplt'
]

AGG_FIELDS = [
    'planned_start', 'planned_end', 'actual_start', 'actual_end', 'actual_start_imputed',
    'planned_duration_days', 'elapsed_days', 'delay_days', 'schedule_slippage_pct',
    'will_delay', 'will_delay_abs30', 'will_delay_rel5pct'
]


def collect_raw_values(rows_df, pid):
    subset = rows_df[rows_df['project_id'].astype(str) == str(pid)]
    out = {}
    for c in RAW_CANDIDATES:
        if c in subset.columns:
            vals = subset[c].dropna().astype(str).unique()
            out[c] = ' | '.join(sorted(vals)) if len(vals) else ''
        else:
            out[c] = ''
    return out


def load_fallbacks(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(item.get('project_id')): item for item in data}
        elif isinstance(data, dict):
            return data
        else:
            return {}
    except Exception:
        return {}


def summarize_issues(df):
    issues = {
        'planned_start_eq_planned_end': [],
        'missing_actual_start': [],
        'missing_planned_start_or_end': [],
        'actual_end_present_but_start_missing': [],
        'imputed_actual_start_true': []
    }
    for _, r in df.iterrows():
        pid = r['project_id']
        ps = r.get('planned_start', '')
        pe = r.get('planned_end', '')
        ast = r.get('actual_start', '')
        aet = r.get('actual_end', '')
        imputed = str(r.get('actual_start_imputed', False)).lower() in ('true','1')

        if ps and pe and str(ps) == str(pe):
            issues['planned_start_eq_planned_end'].append(pid)
        if pd.isna(ast) or ast == '' or str(ast).lower() == 'nan':
            issues['missing_actual_start'].append(pid)
        if (not ps) or (not pe):
            issues['missing_planned_start_or_end'].append(pid)
        if (aet and (not ast or str(ast).lower() == 'nan')):
            issues['actual_end_present_but_start_missing'].append(pid)
        if imputed:
            issues['imputed_actual_start_true'].append(pid)
    return issues


def main():
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    agg = pd.read_csv(AGG_PATH, low_memory=False)
    rows = pd.read_csv(ROWS_PATH, low_memory=False, dtype=str)
    fallbacks = load_fallbacks(FALLBACKS_PATH)

    diagnostics = []
    for idx, row in agg.iterrows():
        pid = str(row['project_id'])
        rec = {'project_id': pid}
        # raw candidate aggregates
        rawvals = collect_raw_values(rows, pid)
        rec.update({f'raw__{k}': v for k, v in rawvals.items()})

        # aggregated parsed/derived fields
        for f in AGG_FIELDS:
            rec[f] = row.get(f, '')

        # fallback record
        fb = fallbacks.get(pid, {})
        rec['parse_fallback_used'] = ''
        if isinstance(fb, dict):
            used = fb.get('used')
            ro = fb.get('year_only_parse')
            rec['parse_fallback_used'] = f"used_keys={list(used.keys()) if isinstance(used, dict) else used}; year_only={ro}; actual_start_imputed={fb.get('actual_start_imputed', False)}"
        else:
            rec['parse_fallback_used'] = str(fb)

        # add simple issue flags
        ps = rec.get('planned_start', '')
        pe = rec.get('planned_end', '')
        ast = rec.get('actual_start', '')
        aet = rec.get('actual_end', '')
        rec['flag_planned_start_eq_planned_end'] = bool(ps and pe and str(ps) == str(pe))
        rec['flag_missing_actual_start'] = not (ast and str(ast).lower() != 'nan')
        rec['flag_missing_planned_start_or_end'] = not (ps and pe)
        rec['flag_actual_end_present_but_start_missing'] = bool(aet and (not ast or str(ast).lower() == 'nan'))
        rec['flag_actual_start_imputed'] = bool(str(rec.get('actual_start_imputed', False)).lower() in ('true','1'))

        diagnostics.append(rec)

    df = pd.DataFrame(diagnostics)
    # write full CSV
    df.to_csv(OUT_CSV, index=False)

    # summarize issues
    issues = summarize_issues(df)
    lines = []
    lines.append(f"Diagnostics generated: {datetime.utcnow().isoformat()}Z")
    lines.append(f"Total projects analyzed: {len(df)}")
    for k, v in issues.items():
        lines.append(f"{k}: count={len(v)}")
        # include up to 20 project ids for quick inspection
        if len(v) > 0:
            lines.append(', '.join(v[:20]))
    with open(OUT_SUM, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Wrote diagnostics CSV to {OUT_CSV}")
    print(f"Wrote summary to {OUT_SUM}")


if __name__ == '__main__':
    main()
