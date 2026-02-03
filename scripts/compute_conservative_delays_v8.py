import pandas as pd
import json
import os
from datetime import datetime

AGG_IN = os.path.join("data_splits", "project_level_aggregated_v8.csv")
FALLBACKS = os.path.join("data_splits", "v8", "parse_fallbacks.json")
AGG_OUT = os.path.join("data_splits", "project_level_aggregated_v8_conservative.csv")
SUMMARY_OUT = os.path.join(
    "data_splits", "v8", "project_level_aggregated_v8_conservative_summary.txt"
)


def load_fallbacks(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {str(item.get("project_id")): item for item in data}
        elif isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def used_contains_full_date(used_list):
    # used_list is expected like ["_parsed__DateFiled", "_parsed__PermitYear"]
    if not used_list:
        return False
    for token in used_list:
        t = str(token)
        # treat any token that references PermitYear/CompltYear as year-only
        if "PermitYear" in t or "CompltYear" in t or "Year" in t and "Date" not in t:
            continue
        # if token contains Date or 'Project Phase' assume full-date parse
        if (
            "Date" in t
            or "Project Phase" in t
            or "Filed" in t
            or "Permit" in t
            or "Complt" in t
        ):
            return True
    return False


def main():
    os.makedirs(os.path.dirname(AGG_OUT), exist_ok=True)
    agg = pd.read_csv(AGG_IN, low_memory=False)
    fallbacks = load_fallbacks(FALLBACKS)

    # ensure output cols exist
    agg["can_compute_delay"] = False
    agg["cons_planned_duration_days"] = pd.NA
    agg["cons_elapsed_days"] = pd.NA
    agg["cons_delay_days"] = pd.NA
    agg["cons_schedule_slippage_pct"] = pd.NA

    for i, r in agg.iterrows():
        pid = str(r.get("project_id"))
        fb = fallbacks.get(pid, {})
        used = fb.get("used", {}) if isinstance(fb, dict) else {}

        # determine whether planned_start/planned_end full-date parsed
        ps_full = False
        pe_full = False
        ast_full = False
        aet_full = False

        try:
            ps_used = used.get("planned_start", [])
            pe_used = used.get("planned_end", [])
            ast_used = used.get("actual_start", [])
            aet_used = used.get("actual_end", [])
        except Exception:
            ps_used = pe_used = ast_used = aet_used = []

        ps_full = used_contains_full_date(ps_used)
        pe_full = used_contains_full_date(pe_used)
        ast_full = used_contains_full_date(ast_used)
        aet_full = used_contains_full_date(aet_used)

        # parse candidate strings only if they exist and are considered full
        planned_start = r.get("planned_start", "") if ps_full else ""
        planned_end = r.get("planned_end", "") if pe_full else ""
        actual_start = r.get("actual_start", "") if ast_full else ""
        actual_end = r.get("actual_end", "") if aet_full else ""

        try:
            pstart = (
                pd.to_datetime(planned_start, errors="coerce")
                if planned_start
                else pd.NaT
            )
            pend = (
                pd.to_datetime(planned_end, errors="coerce") if planned_end else pd.NaT
            )
            astart = (
                pd.to_datetime(actual_start, errors="coerce")
                if actual_start
                else pd.NaT
            )
            aend = pd.to_datetime(actual_end, errors="coerce") if actual_end else pd.NaT
        except Exception:
            pstart = pend = astart = aend = pd.NaT

        can_compute = False
        cons_planned_duration = pd.NA
        cons_elapsed = pd.NA
        cons_delay = pd.NA
        cons_pct = pd.NA

        if not (pd.isna(pstart) or pd.isna(pend)):
            cons_planned_duration = (pend - pstart).days
        if not (pd.isna(astart) or pd.isna(aend)):
            cons_elapsed = (aend - astart).days
        if (
            cons_planned_duration is not pd.NA
            and cons_elapsed is not pd.NA
            and pd.notna(cons_planned_duration)
        ):
            # both numeric
            try:
                cons_delay = int(cons_elapsed) - int(cons_planned_duration)
            except Exception:
                cons_delay = pd.NA
            try:
                if cons_planned_duration != 0:
                    cons_pct = float(cons_delay) / float(cons_planned_duration)
                else:
                    cons_pct = pd.NA
            except Exception:
                cons_pct = pd.NA

        if (
            pd.notna(cons_planned_duration)
            and pd.notna(cons_elapsed)
            and pd.notna(cons_delay)
        ):
            can_compute = True

        agg.at[i, "can_compute_delay"] = bool(can_compute)
        agg.at[i, "cons_planned_duration_days"] = cons_planned_duration
        agg.at[i, "cons_elapsed_days"] = cons_elapsed
        agg.at[i, "cons_delay_days"] = cons_delay
        agg.at[i, "cons_schedule_slippage_pct"] = cons_pct

    agg.to_csv(AGG_OUT, index=False)

    # summary
    total = len(agg)
    computable = int(agg["can_compute_delay"].sum())
    lines = []
    lines.append(
        f"Conservative delay computation run: {datetime.utcnow().isoformat()}Z"
    )
    lines.append(f"Input aggregated projects: {total}")
    lines.append(
        f"Projects with computable delay (all four full-date parses present): {computable}"
    )
    lines.append(f"Projects missing computable delay: {total - computable}")
    with open(SUMMARY_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote conservative aggregated CSV to {AGG_OUT}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
