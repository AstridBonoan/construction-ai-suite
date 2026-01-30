# Model Card - v8 relaxed baseline

Training skipped: insufficient positive examples.

## New label: `will_delay_rel1pct`
- Definition: relative schedule slippage > 1%: (elapsed_days - planned_duration_days) / planned_duration_days > 0.01
- Only computed when planned_duration_days > 14 days.
- Planned durations > 1825 days are capped as invalid (NaN).
- Label values: 0/1 numeric.
- Confidence: `label_confidence` retained (high/medium/low) for downstream weighting.

## New label: `will_delay_rel0pct`
- Definition: relative schedule slippage > 0: (elapsed_days - planned_duration_days) / planned_duration_days > 0
- Only computed when planned_duration_days > 0.
- Planned durations > 1825 days are capped as invalid (NaN).
- Label values: 0/1 numeric.
- Confidence: `label_confidence` retained (high/medium/low) for downstream weighting.

## Rule B cohort median imputation
- For projects with collapsed planned windows, replace `planned_duration_days` with the cohort median planned duration (per `project_type` when available, otherwise global median).
- For projects with collapsed planned windows or missing `actual_start`, impute `actual_start = actual_end - median_planned_duration` where median is computed per `project_type` when available, otherwise global median.
- Imputed rows are flagged with `actual_start_imputed=True`, `imputation_rule=RuleB`, and `label_confidence=low`.
- Delay and `will_delay_ruleB` are computed only where `planned_duration_days > 0`.
