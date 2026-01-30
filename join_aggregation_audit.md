## Join / Aggregation Audit: Where the target leaks

Summary
- Root cause: ingestion concatenates heterogeneous source files (row-level and project-level) into one table (`prepare_project_dataset.py::load_datasets`), then deduplication picks the most-complete row per project (see [scripts/eda_and_split.py](scripts/eda_and_split.py#L43-L55)). Some input files already contain label-derived fields (e.g. `schedule_slippage_pct` / `will_delay`) or date fields that allow computing them; those get carried into the deduped project row and become features.

Evidence inspected
- `prepare_project_dataset.py::load_datasets` concatenates all CSVs and adds `source_file` and `synthetic_flag`.
- `scripts/eda_and_split.py::deduplicate_keep_most_complete` deduplicates by `project_id`, keeping the most complete row (first after sorting) — this can preserve pre-aggregated/project-level rows with target fields.
- `scripts/redefine_target_and_split.py` will compute `schedule_slippage_pct` from date columns if missing, or respects existing `schedule_slippage_pct` if present in the input.
- Data artifacts: `data_splits/project_level_deduped_with_target.csv` (contains `will_delay`) and `analysis_outputs/v5/transformed_feature_mapping.csv` (mapping shows many transformed features map back to original columns such as `Award`, `BBL`, `BIN`, `Borough`, and many `Budget_Line_*` columns coming from source CSVs).

Why this causes perfect prediction
- If any source file already contains `will_delay` or `schedule_slippage_pct` (or fields that deterministically map to them after parsing), concatenation + deduplication can put that label information into the same row that supplies features. The model then learns direct or near-direct mappings (exact or near-exact matches), producing MAE=0 / R^2=1.0.

Concrete fixes (priority order)
1. Stop mixing row-level and project-level (already-aggregated) files in one concatenation step.
   - Implementation: change `prepare_project_dataset.py::discover_data_files` / `load_datasets` to separate files by a configurable whitelist/blacklist or by detecting pre-aggregated files (e.g., filenames containing "project_level" or explicit schema check).
2. Remove/ignore label-derived columns before concatenation/deduplication.
   - Implementation: in `load_datasets`, after reading each file, drop columns named `will_delay`, `schedule_slippage_pct`, `slippage_days`, `elapsed_days`, `planned_duration_days`, `actual_end`, `planned_end`, `actual_start` (configurable list). Also drop any column name matching a small deny-list used by leakage audits.
3. Compute the target only once, from a single, auditable aggregation step, and then join the target to the feature table using a controlled left-join.
   - Implementation: (a) Build feature table by concatenating only true row-level sources and deduplicating with clear priority rules; (b) separately run aggregation (`clean_planned_and_aggregate.py` or `agg_redefine_target_and_split.py`) to produce project-level target; (c) merge target into features by project id with an explicit `suffixes` policy and assert no duplicate target-like columns remain.
4. Change dedup logic to prefer row-level-derived rows over pre-aggregated rows.
   - Implementation: in `eda_and_split.py::deduplicate_keep_most_complete`, sort by (`project_id`, `source_priority`, `__completeness_score`) where `source_priority` prefers raw row-level sources (or explicitly deprioritizes known project-level source files). Alternatively, dedup before concatenating any project-level files.
5. Add automated guardrails and assertions.
   - Implementation suggestions:
     - After merging features and target, assert that no feature column name equals `will_delay` or `schedule_slippage_pct`.
     - Run a quick correlation scan and fail the pipeline if any raw feature has |corr| >= 0.99 with the target.
     - Log `source_file` provenance for any feature columns with high correlation for faster triage.

Quick checks to run now (no retrain)
- Search raw input files for `will_delay` / `schedule_slippage_pct` columns and report them (manual or script). If found, remove or rename before ingest.
- Re-run dedup but force `source_file` ordering so that known row-level inputs come first; then regenerate `project_level_deduped_with_target.csv` and re-run the leakage mapping.

Files & lines referenced
- [scripts/prepare_project_dataset.py](scripts/prepare_project_dataset.py#L46-L64) (load_datasets)
- [scripts/eda_and_split.py](scripts/eda_and_split.py#L43-L55) (deduplicate_keep_most_complete)
- [scripts/redefine_target_and_split.py](scripts/redefine_target_and_split.py#L32-L78) (target recompute / will_delay creation)
- `data_splits/project_level_deduped_with_target.csv` (observed to contain `will_delay` and many source-file columns)
- `analysis_outputs/v5/transformed_feature_mapping.csv` (leak mapping signal)

Next steps (I can do these if you want)
- Run a quick scan across `construction_datasets` to list which source files contain `will_delay`/`schedule_slippage_pct`/actual/planned date columns.
- Patch `prepare_project_dataset.py::load_datasets` to drop a small deny-list of label-derived columns (I can implement and run locally if you approve).
- Implement assertion checks after merging features & target and re-run the leakage diagnostics.

If you want me to implement a fix now, tell me which option to apply first (deny-list drop, separation of project-level files, or compute-and-join pattern) and I will patch the code and run the quick checks (no retraining unless you ask).
