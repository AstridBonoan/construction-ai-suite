Step 8 — Leakage Lockdown (completed)
====================================

Summary
-------
Step 8 validated and removed label-derived / post-outcome features, enforced a feature blacklist, and produced audited, leakage-free CSV for baseline training.

Locked files
------------
- config/feature_blacklist_v8.json  — final blacklist (columns + prefixes + intent note)
- scripts/train_exploratory_baselines_v8.py — dry-run support and default to cleaned nodistrict CSV
- scripts/create_noleak_dataset_v8.py
- scripts/create_nodistrict_dataset_v8.py
- scripts/leakage_audit_v8_clean.py
- scripts/leakage_audit_v8_final.py
- reports/leakage_audit_v8.json (archival marker)
- .gitignore (updated for temp/artifact discipline)

Clean dataset
-------------
Use this verified dataset for baseline training:

data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv

Blacklist purpose & usage
-------------------------
The blacklist prevents leakage by excluding known label-derived, post-outcome, or identifier-like fields.
It is authoritative for all baseline training runs and must NOT be bypassed without a new leakage audit.

Location: config/feature_blacklist_v8.json

Dry-run
-------
Before any training, run in dry-run to confirm the blacklist will be applied and no training will execute:

python scripts/train_exploratory_baselines_v8.py --dry-run

This prints which columns would be dropped and exits without writing models or reports.

Safe baseline training command (for Step 9; do NOT run until authorized)
--------------------------------------------------------------------------------
python scripts/train_exploratory_baselines_v8.py \
  --data data_splits/project_level_aggregated_v8_ruleB_imputed_expanded_noleak_nodistrict.csv \
  --enforce-blacklist \
  --model-dir models/ \
  --report-dir analysis/

Notes & best practices
----------------------
- Archive audit JSONs with a version tag before retraining (reports/). e.g. reports/leakage_audit_v8_final.json -> reports/archive/leakage_audit_v8_final_v1.json
- Keep artifact folders (`models/`, `analysis/`) consistent. `.gitignore` has been updated to avoid accidentally committing temp/test outputs and .pkl files.
- Review the single extreme outlier in `delay_days` (value 9223) before interpreting metrics; it's a data-quality decision, not leakage.

Commit message suggestion
------------------------
"Step 8 complete — leakage cleared, blacklist enforced, dry-run verified."

Contact
-------
For questions about the blacklist or next steps for Step 9, open an issue or ping the data-science owner.
