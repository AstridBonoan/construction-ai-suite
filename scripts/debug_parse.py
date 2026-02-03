import pandas as pd
import re
from datetime import datetime, timedelta


def clean_token(s: str) -> str:
    if pd.isna(s):
        return ""
    s = str(s).strip()
    if not s:
        return ""
    s_low = s.strip().lower()
    if s_low in ("unknown", "na", "n/a", "none", "ieh", "doer", "pns", "ftk", "does"):
        return ""
    s = re.sub(r"^[A-Za-z:._\-\s]+", "", s)
    return s.strip()


def parse_date_str(s: str):
    s = clean_token(s)
    if not s:
        return pd.NaT
    dt = pd.to_datetime(s, errors="coerce")
    if not pd.isna(dt):
        return dt
    # try extracting digits
    m = re.search(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{4}", s)
    if m:
        return pd.to_datetime(m.group(0), errors="coerce")
    return pd.NaT


df = pd.read_csv("data_splits/project_dataset_v7_cleaned.csv", dtype=str)
cols = df.columns.tolist()
print("columns", len(cols))
cand = {"planned_start": [], "planned_end": [], "actual_start": [], "actual_end": []}
for c in cols:
    cl = c.lower()
    if "planned" in cl and "start" in cl:
        cand["planned_start"].append(c)
    if "planned" in cl and "end" in cl:
        cand["planned_end"].append(c)
    if "actual" in cl and "start" in cl:
        cand["actual_start"].append(c)
    if "actual" in cl and "end" in cl:
        cand["actual_end"].append(c)
    if "filed" in cl:
        cand["actual_start"].append(c)
    if "permit" in cl:
        cand["planned_start"].append(c)
    if "complt" in cl or "complt" in cl or "complt" in cl:
        cand["actual_end"].append(c)

print("candidate map", cand)

# parse small sample
sample = df.head(200)
for role, cols in cand.items():
    for c in cols:
        parsed = sample[c].apply(parse_date_str)
        non_null = parsed.dropna()
        print(role, c, "parsed non-null count", len(non_null))

grp = df.groupby("project_id")
first = next(iter(grp))[1]
print("first project rows", len(first))
for c in cols:
    if "Project Phase" in c and ("Planned" in c or "Actual" in c):
        vals = first[c].tolist()[:10]
        print(c, "sample values", vals)

print("debug parse check done")
