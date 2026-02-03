import csv
from datetime import datetime, timedelta
from difflib import get_close_matches
import math
import pandas as pd


def find_project_type_col(cols):
    for c in cols:
        if "project" in c.lower() and "type" in c.lower():
            return c
    # fallback common names
    for name in ["project_type", "Project Type", "Project Type "]:
        if name in cols:
            return name
    return None


def parse_date(x):
    if pd.isna(x):
        return None
    if isinstance(x, datetime):
        return x
    s = str(x).strip()
    if s == "" or s.lower() in ["nan", "none"]:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(s)
    except Exception:
        return None


def infer_types(df, project_type_col):
    known_map = {
        "high school": "High School",
        "hs": "High School",
        "highschool": "High School",
        "elementary": "Elementary",
        "elem": "Elementary",
        "primary": "Elementary",
        "middle": "Middle",
        "middleschool": "Middle",
        "ms": "Middle",
        "hospital": "Hospital",
        "medical": "Hospital",
        "bridge": "Bridge",
        "park": "Park",
        "playground": "Park",
        "residential": "Residential",
        "housing": "Residential",
        "apartment": "Residential",
        "apt": "Residential",
        "library": "Library",
        "road": "Road",
        "roadway": "Road",
        "street": "Road",
        "st": "Road",
        "sewer": "Utility",
        "water": "Utility",
        "police": "Police",
        "fire": "Fire",
        "hotel": "Hotel",
        "office": "Office",
        "commercial": "Commercial",
        "retail": "Commercial",
        "stadium": "Stadium",
        "airport": "Airport",
        "school": "School",
    }
    known_types = sorted(list(set(known_map.values())))

    text_cols = [
        c
        for c in df.columns
        if any(k in c.lower() for k in ("title", "desc", "description", "name"))
    ]

    inferred = 0
    for idx, row in df.iterrows():
        cur = row.get(project_type_col, None)
        if isinstance(cur, str) and cur.strip() != "" and not pd.isna(cur):
            continue
        # build search text
        pieces = []
        for c in text_cols:
            v = row.get(c, "")
            if pd.isna(v):
                continue
            pieces.append(str(v))
        txt = " ".join(pieces).lower()
        chosen = None
        if txt:
            # substring keyword map
            for k, v in known_map.items():
                if (
                    (" " + k + " ") in (" " + txt + " ")
                    or txt.startswith(k)
                    or txt.endswith(k)
                    or (" " + k + ",") in txt
                ):
                    chosen = v
                    break
            # abbreviations boundary check
            if not chosen:
                if "\bhs\b" in txt or " high school" in txt:
                    chosen = "High School"
            # fuzzy match tokens
            if not chosen:
                tokens = [
                    t
                    for t in txt.replace("/", " ").replace("-", " ").split()
                    if len(t) > 2
                ]
                for t in tokens:
                    cm = get_close_matches(
                        t, list(known_map.keys()) + known_types, n=1, cutoff=0.85
                    )
                    if cm:
                        cand = cm[0]
                        # map back if key
                        if cand in known_map:
                            chosen = known_map[cand]
                        else:
                            chosen = cand
                        break
        if chosen:
            df.at[idx, project_type_col] = chosen
            inferred += 1
    return df, inferred


def main():
    in_path = "data_splits/project_level_aggregated_v8_relaxed_with_types.csv"
    out_relaxed_expanded = (
        "data_splits/project_level_aggregated_v8_relaxed_with_types_expanded.csv"
    )
    out_imputed = "data_splits/project_level_aggregated_v8_ruleB_imputed_expanded.csv"
    diag_path = "data_splits/v8/diagnostics_ruleB_expanded.txt"

    df = pd.read_csv(in_path, dtype=str)
    # preserve numeric columns as numeric
    numeric_cols = [
        "planned_duration_days",
        "elapsed_days",
        "delay_days",
        "schedule_slippage_pct",
    ]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    project_type_col = find_project_type_col(df.columns)
    if project_type_col is None:
        raise RuntimeError("Could not find project_type column")

    missing_before = df[project_type_col].isna() | (
        df[project_type_col].astype(str).str.strip() == ""
    )

    df_inf, inferred = infer_types(df.copy(), project_type_col)

    df_inf.to_csv(out_relaxed_expanded, index=False, quoting=csv.QUOTE_MINIMAL)

    # compute per-type medians using only planned_duration_days > 0
    if "planned_duration_days" in df_inf.columns:
        df_inf["planned_duration_days"] = pd.to_numeric(
            df_inf["planned_duration_days"], errors="coerce"
        )
    else:
        df_inf["planned_duration_days"] = pd.NA

    pos_pd = df_inf[df_inf["planned_duration_days"] > 0]
    per_type_medians = pos_pd.groupby(project_type_col)[
        "planned_duration_days"
    ].median()
    global_median = pos_pd["planned_duration_days"].median()
    if math.isnan(global_median) or pd.isna(global_median):
        global_median = 365.0

    # apply RuleB imputation for rows where planned_duration_days <=0 or NaN
    imputed_count = 0
    for idx, row in df_inf.iterrows():
        pdur = row.get("planned_duration_days")
        try:
            valid = float(pdur) > 0
        except Exception:
            valid = False
        if not valid:
            ptype = row.get(project_type_col, "")
            median = None
            if ptype in per_type_medians.index:
                median = per_type_medians.loc[ptype]
            if pd.isna(median) or median is None:
                median = global_median
            df_inf.at[idx, "planned_duration_days"] = float(median)
            imputed_count += 1
            # set flags
            if "actual_start_imputed" in df_inf.columns:
                df_inf.at[idx, "actual_start_imputed"] = True
            else:
                df_inf.loc[idx, "actual_start_imputed"] = True
            df_inf.at[idx, "imputation_rule"] = "RuleB"
            df_inf.at[idx, "label_confidence"] = "low"

    # recompute planned_end_dt if possible
    for idx, row in df_inf.iterrows():
        ps = row.get("planned_start_dt") or row.get("planned_start")
        try:
            planned_start_dt = parse_date(ps)
        except Exception:
            planned_start_dt = None
        pdur = row.get("planned_duration_days")
        try:
            pdur_n = float(pdur)
        except Exception:
            pdur_n = None
        if (
            planned_start_dt is not None
            and pdur_n is not None
            and not math.isnan(pdur_n)
        ):
            new_planned_end = planned_start_dt + timedelta(days=int(round(pdur_n)))
            df_inf.at[idx, "planned_end_dt"] = new_planned_end.strftime("%Y-%m-%d")

    # parse date columns for computations
    for c in ["planned_start_dt", "planned_end_dt", "actual_start_dt", "actual_end_dt"]:
        if c in df_inf.columns:
            df_inf[c + "_parsed"] = df_inf[c].apply(parse_date)
        else:
            df_inf[c + "_parsed"] = None

    # recompute elapsed_days = (actual_start_dt - planned_start_dt).days
    # delay_days = (actual_start_dt - planned_end_dt).days
    df_inf["elapsed_days"] = None
    df_inf["delay_days"] = None
    df_inf["schedule_slippage_pct"] = None
    df_inf["will_delay_ruleB"] = 0
    for idx, row in df_inf.iterrows():
        a = row.get("actual_start_dt_parsed")
        ps = row.get("planned_start_dt_parsed")
        pe = row.get("planned_end_dt_parsed")
        try:
            if pd.notna(a) and a is not None and pd.notna(ps) and ps is not None:
                elapsed = (a - ps).days
                df_inf.at[idx, "elapsed_days"] = int(elapsed)
            if pd.notna(a) and a is not None and pd.notna(pe) and pe is not None:
                delay = (a - pe).days
                df_inf.at[idx, "delay_days"] = int(delay)
                pdur = row.get("planned_duration_days")
                try:
                    pdur_f = float(pdur)
                except Exception:
                    pdur_f = None
                if pdur_f and pdur_f != 0:
                    sl = (delay / pdur_f) * 100.0
                    df_inf.at[idx, "schedule_slippage_pct"] = float(sl)
                df_inf.at[idx, "will_delay_ruleB"] = 1 if delay > 0 else 0
        except Exception:
            continue

    # write outputs
    df_inf.to_csv(out_imputed, index=False, quoting=csv.QUOTE_MINIMAL)

    total_projects = len(df_inf)
    projects_with_inferred = int(inferred)
    counts_by_imputation = (
        df_inf["imputation_rule"].value_counts(dropna=False).to_dict()
        if "imputation_rule" in df_inf.columns
        else {}
    )
    counts_by_confidence = (
        df_inf["label_confidence"].value_counts(dropna=False).to_dict()
        if "label_confidence" in df_inf.columns
        else {}
    )
    will_delay_pos = int(df_inf["will_delay_ruleB"].astype(int).sum())
    will_delay_neg = total_projects - will_delay_pos

    diag = {
        "total_projects": total_projects,
        "projects_with_inferred_project_type": projects_with_inferred,
        "imputed_count_ruleB": imputed_count,
        "counts_by_imputation_rule": counts_by_imputation,
        "counts_by_label_confidence": counts_by_confidence,
        "will_delay_ruleB_positives": will_delay_pos,
        "will_delay_ruleB_negatives": will_delay_neg,
        "per_type_medians": per_type_medians.fillna("").to_dict(),
        "global_median_used": float(global_median),
    }

    # write diagnostics file
    import json

    with open(diag_path, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2)

    print("Wrote", out_relaxed_expanded)
    print("Wrote", out_imputed)
    print("Wrote", diag_path)


if __name__ == "__main__":
    main()
