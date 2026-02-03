import json

js = json.load(open("data_splits/v8/parse_fallbacks.json"))
col_counts = {}
any_parsed = 0
for rec in js:
    used = rec["used"]
    any_this = False
    for role, pcs in used.items():
        for pc in pcs:
            any_this = True
            col = pc.replace("_parsed__", "")
            col_counts[col] = col_counts.get(col, 0) + 1
    if any_this:
        any_parsed += 1

proj_primary = sum(
    1
    for rec in js
    if any("project phase" in c.lower() for pcs in rec["used"].values() for c in pcs)
)
proj_fallback = sum(
    1
    for rec in js
    if any(
        not ("project phase" in c.lower()) for pcs in rec["used"].values() for c in pcs
    )
)
failed_all = sum(1 for rec in js if not any(rec["used"].values()))

print("projects_total=", len(js))
print("projects_with_any_parsed=", any_parsed)
print("projects_using_project_phase_cols=", proj_primary)
print("projects_using_fallback_cols=", proj_fallback)
print("projects_failed_all_parsing=", failed_all)
print("col_counts top contributors:")
for k, v in sorted(col_counts.items(), key=lambda x: -x[1]):
    print(" ", k, v)
