# Baseline v1 — Project Delay Prediction

**Purpose**

- This baseline provides a minimal, reproducible model for predicting project schedule delay (baseline experiment v1). It was produced to establish a performance reference and basic analysis outputs for the project-delay prediction pipeline.

**Model summary**

- Algorithm: RandomForestRegressor (scikit-learn)
- Trained to predict a numeric score corresponding to the delay indicator derived from project schedule slippage. The training pipeline derives a binary `will_delay` label from `schedule_slippage_pct` (> 0.05), and the regressor is trained on that label (0/1) to produce a numeric score.

**Artifacts (locations in repo)**

- Trained model: `models/baseline_project_delay_model.pkl`
- Metrics (MAE, RMSE, R²): `analysis_outputs/metrics.json`
- Plots (analysis): `analysis_outputs/actual_vs_predicted.png`, `analysis_outputs/residuals_distribution.png`, `analysis_outputs/error_histogram.png`
- Commit: `099e5529376d4915ac77b7bdbeca4736803e71b0` on branch `feature/project-delay-prediction` (pushed to remote)

**Input / Output**

- Input: a project-level, deduplicated CSV after preprocessing (`data_splits/project_dataset_v1_cleaned.csv` or other deduped/aggregated project-level files). The pipeline expects project-level features with ID and date columns; the splitting script will derive `schedule_slippage_pct` and the binary `will_delay` target.
- Output: numeric prediction score (float). For evaluation the score is compared against the numeric target (0/1) and reported with regression metrics (MAE, RMSE, R²).

**Evaluation (recorded)**

- MAE: 0.0
- RMSE: 0.0
- R²: 1.0

These metric values are the numbers recorded at the time the baseline was trained and committed. They appear in `analysis_outputs/metrics.json`.

**Reproducibility notes**

- The training was executed inside the project Docker workflow. Build steps and the container environment are defined in `docker/Dockerfile` and orchestrated via `scripts/run_pipeline.ps1`.
- The container runtime creates a Python virtual environment at `/opt/venv` and installs dependencies from `backend/requirements.txt` (plus minimal ML libs installed in the venv when needed).
- Large datasets used by the pipeline are tracked with Git LFS; ensure you have `git-lfs` installed and `git lfs pull` executed when cloning to retrieve the underlying CSVs.
- The run that produced these artifacts created a local commit which was placed on branch `feature/project-delay-prediction` and pushed to the remote repository at commit `099e5529376d4915ac77b7bdbeca4736803e71b0`.

**How to reproduce / re-run the baseline (host)**

1. Ensure Docker Desktop is running on your host and you have `git-lfs` installed and authenticated for the repository.
2. From the repository root, build the baseline image (optional — `scripts/run_pipeline.ps1` also builds):

```powershell
docker build -t construction-ai-baseline:latest -f docker/Dockerfile .
```

3. Run the full pipeline (build+train+analysis). The provided PowerShell helper does the right mounts and invocation:

```powershell
.\scripts\run_pipeline.ps1
```

Or run the container directly (mounts the repo into `/workspace`):

```bash
docker run --rm -v ${PWD}:/workspace -w /workspace construction-ai-baseline:latest
```

4. If you prefer to run only the training step inside the prepared container environment (after building and/or entering the container), run:

```bash
/opt/venv/bin/python3 backend/train_baseline_project_delay.py --splits-dir data_splits
```

Notes:
- The pipeline expects `data_splits/X_train.csv`, `y_train.csv`, `X_test.csv`, and `y_test.csv` to exist; use `scripts/redefine_target_and_split.py` to derive `will_delay` and create stratified splits from an aggregated project CSV.
- Do not commit raw dataset files to the repository; use `git-lfs` for large CSVs as configured.

**Branch / commit reference**

- Branch: `feature/project-delay-prediction`
- Commit: `099e5529376d4915ac77b7bdbeca4736803e71b0`
- Remote repository: https://github.com/AstridBonoan/construction-ai-suite

**Contact / notes for maintainers**

- This document describes only Baseline v1 (the exact run and artifacts listed above). For any questions about how the training run was executed, check `scripts/run_pipeline.ps1`, `docker/Dockerfile`, and the training script `backend/train_baseline_project_delay.py` for implementation details.

---

## Baseline v2 — Project Delay Prediction (improved)

**Summary**

- Model: RandomForestRegressor with preprocessing (numeric imputation + scaling, categorical OneHotEncoding)
- Model artifact: `models/v2/baseline_project_delay_model_v2.pkl`
- Metrics: `analysis_outputs/v2/metrics.json`
- Plots: `analysis_outputs/v2/actual_vs_predicted.png`, `analysis_outputs/v2/residuals_distribution.png`, `analysis_outputs/v2/error_histogram.png`

**Recorded v2 metrics**

- MAE: 4.427390791027153e-06
- RMSE: 0.0005008846954721267
- R²: 0.9999893559392963

**How v2 was produced**

- A preprocessing pipeline was added: numeric median imputation + standard scaling; categorical columns imputed with a constant and One-Hot encoded (sparse output).
- RandomizedSearchCV was used to tune core RandomForest hyperparameters; the best estimator was saved under `models/v2/` and analysis outputs under `analysis_outputs/v2/`.

**Reproducibility**

- To reproduce v2 locally (inside the container):

```bash
docker run --rm -v ${PWD}:/workspace -w /workspace construction-ai-baseline:latest /opt/venv/bin/python3 scripts/train_baseline_v2.py --n-iter 12
```

Or run the script inside the prepared venv in the container.

**Notes**

- The recorded v2 metrics are extremely high (R² ~ 0.99999). This likely indicates data leakage, label leakage, or that the model is effectively learning the training labels perfectly — please inspect feature derivation and ensure the test split is strictly held-out.
- Baseline v1 artifacts remain unchanged for reference.

---

Generated: January 29, 2026

---

## Baseline v4 — Project Delay Prediction (cleaned, leakage-mitigated)

**Summary**

- Model: RandomForestRegressor with preprocessing; direct label and audit-flagged features removed.
- Model artifact: `models/v4/baseline_project_delay_model_v4.pkl`
- Metrics: `analysis_outputs/v4/metrics.json`
- Plots: `analysis_outputs/v4/actual_vs_predicted.png`, `analysis_outputs/v4/residuals_distribution.png`, `analysis_outputs/v4/error_histogram.png`

**What changed**

- Removed direct label leakage: `will_delay` was present in features and has been dropped.
- Dropped constant and ID/date-like columns flagged by diagnostics (see `analysis_outputs/v3/top_suspicious_features.csv`).
- Splits now created in `data_splits/v4/` with reproducible `random_state` and a project-level split with a row-level fallback.

**Recorded v4 metrics**

- MAE: 0.0
- RMSE: 0.0
- R²: 1.0

**Branch / commit reference**

- Branch: `feature/project-delay-v4`
- Commit: 14c21d0

**How to reproduce v4 (inside container)**

1. Prepare v4 splits (drops `will_delay` and audit-flagged features):

```bash
/opt/venv/bin/python3 scripts/prepare_splits_v3.py --random-state 42 --test-size 0.2
```

2. Train Baseline v4 and save artifacts:

```bash
/opt/venv/bin/python3 scripts/train_baseline_v4.py --random-state 42 --n-iter 12
```

Notes:
- Confirm `analysis_outputs/v3/top_suspicious_features.csv` is present to apply diagnostic drops.
- The v4 run should be used for review; further feature engineering and stricter time-based splits are recommended before production.


---

## Baseline v3 — Project Delay Prediction (leakage-mitigated)

**Summary**

- Model: RandomForestRegressor with preprocessing; leakage-mitigated split preparation and dropped audit-flagged features.
- Model artifact: `models/v3/baseline_project_delay_model_v3.pkl`
- Metrics: `analysis_outputs/v3/metrics.json`
- Plots: `analysis_outputs/v3/actual_vs_predicted.png`, `analysis_outputs/v3/residuals_distribution.png`, `analysis_outputs/v3/error_histogram.png`

**Features removed / modified (sample)**

The v3 split preparation removed audit-flagged and id/date/constant features. Sample of removed features (from `data_splits/v3/metadata.json`):

- ()
- Accident Report ID
- Country Code
- DSF Number(s)
- INDICATOR_CODE
- INDICATOR_NAME
- Landmark
- NonresFlag
- PL_FIRM07
- PL_PFIRM15
- Project Budget Amount
- Project Building Identifier
- Project Description
- Project Geographic District
- Project Phase Name
- Project School Name
- Project Status Name
- Project Type
- ResidFlag
- SOURCE_NOTE
- SOURCE_ORGANIZATION
- SchMiddle
- Version
- project_id
- schedule_slippage_pct

**Recorded v3 metrics**

- MAE: 0.0
- RMSE: 0.0
- R²: 1.0

**Branch / commit reference**

- Branch: `feature/project-delay-v3`
- Commit: TO_BE_FILLED_AFTER_COMMIT
 - Commit: 6ac3eca

**How to reproduce v3 (inside container)**

1. Prepare v3 splits (drops audit-flagged features and uses project-level splitting with a row-level fallback):

```bash
/opt/venv/bin/python3 scripts/prepare_splits_v3.py --random-state 42 --test-size 0.2
```

2. Train Baseline v3 and save artifacts:

```bash
/opt/venv/bin/python3 scripts/train_baseline_v3.py --random-state 42 --n-iter 12
```

Notes:
- The `prepare_splits_v3.py` script writes `data_splits/v3/` and `metadata.json` with the list of dropped features.
- Ensure `analysis_outputs/leakage_audit/feature_correlations.csv` exists before running prepare if you want the audit-based drops.

# Baseline v1 — Project Delay Prediction

**Purpose**

- This baseline provides a minimal, reproducible model for predicting project schedule delay (baseline experiment v1). It was produced to establish a performance reference and basic analysis outputs for the project-delay prediction pipeline.

**Model summary**

- Algorithm: RandomForestRegressor (scikit-learn)
- Trained to predict a numeric score corresponding to the delay indicator derived from project schedule slippage. The training pipeline derives a binary `will_delay` label from `schedule_slippage_pct` (> 0.05), and the regressor is trained on that label (0/1) to produce a numeric score.

**Artifacts (locations in repo)**

- Trained model: `models/baseline_project_delay_model.pkl`
- Metrics (MAE, RMSE, R²): `analysis_outputs/metrics.json`
- Plots (analysis): `analysis_outputs/actual_vs_predicted.png`, `analysis_outputs/residuals_distribution.png`, `analysis_outputs/error_histogram.png`
- Commit: `099e5529376d4915ac77b7bdbeca4736803e71b0` on branch `feature/project-delay-prediction` (pushed to remote)

**Input / Output**

- Input: a project-level, deduplicated CSV after preprocessing (`data_splits/project_dataset_v1_cleaned.csv` or other deduped/aggregated project-level files). The pipeline expects project-level features with ID and date columns; the splitting script will derive `schedule_slippage_pct` and the binary `will_delay` target.
- Output: numeric prediction score (float). For evaluation the score is compared against the numeric target (0/1) and reported with regression metrics (MAE, RMSE, R²).

**Evaluation (recorded)**

- MAE: 0.0
- RMSE: 0.0
- R²: 1.0

These metric values are the numbers recorded at the time the baseline was trained and committed. They appear in `analysis_outputs/metrics.json`.

**Reproducibility notes**

- The training was executed inside the project Docker workflow. Build steps and the container environment are defined in `docker/Dockerfile` and orchestrated via `scripts/run_pipeline.ps1`.
- The container runtime creates a Python virtual environment at `/opt/venv` and installs dependencies from `backend/requirements.txt` (plus minimal ML libs installed in the venv when needed).
- Large datasets used by the pipeline are tracked with Git LFS; ensure you have `git-lfs` installed and `git lfs pull` executed when cloning to retrieve the underlying CSVs.
- The run that produced these artifacts created a local commit which was placed on branch `feature/project-delay-prediction` and pushed to the remote repository at commit `099e5529376d4915ac77b7bdbeca4736803e71b0`.

**How to reproduce / re-run the baseline (host)**

1. Ensure Docker Desktop is running on your host and you have `git-lfs` installed and authenticated for the repository.
2. From the repository root, build the baseline image (optional — `scripts/run_pipeline.ps1` also builds):

```powershell
docker build -t construction-ai-baseline:latest -f docker/Dockerfile .
```

3. Run the full pipeline (build+train+analysis). The provided PowerShell helper does the right mounts and invocation:

```powershell
.\scripts\run_pipeline.ps1
```

Or run the container directly (mounts the repo into `/workspace`):

```bash
docker run --rm -v ${PWD}:/workspace -w /workspace construction-ai-baseline:latest
```

4. If you prefer to run only the training step inside the prepared container environment (after building and/or entering the container), run:

```bash
/opt/venv/bin/python3 backend/train_baseline_project_delay.py --splits-dir data_splits
```

Notes:
- The pipeline expects `data_splits/X_train.csv`, `y_train.csv`, `X_test.csv`, and `y_test.csv` to exist; use `scripts/redefine_target_and_split.py` to derive `will_delay` and create stratified splits from an aggregated project CSV.
- Do not commit raw dataset files to the repository; use `git-lfs` for large CSVs as configured.

**Branch / commit reference**

- Branch: `feature/project-delay-prediction`
- Commit: `099e5529376d4915ac77b7bdbeca4736803e71b0`
- Remote repository: https://github.com/AstridBonoan/construction-ai-suite

**Contact / notes for maintainers**

- This document describes only Baseline v1 (the exact run and artifacts listed above). For any questions about how the training run was executed, check `scripts/run_pipeline.ps1`, `docker/Dockerfile`, and the training script `backend/train_baseline_project_delay.py` for implementation details.

***

## Baseline v5 — Project Delay Prediction (cleaned, leakage-removed)

**Summary**

- Model: RandomForestRegressor with preprocessing; additional leakage-derived features removed.
- Model artifact: `models/v5/baseline_project_delay_model_v5.pkl`
- Metrics: `analysis_outputs/v5/metrics.json`
- Plots: `analysis_outputs/v5/actual_vs_predicted.png`, `analysis_outputs/v5/residuals_distribution.png`, `analysis_outputs/v5/error_histogram.png`

**What changed**

- Removed residual leakage candidates identified in `analysis_outputs/v4/residual_leakage_candidates.csv` (if any).
- Explicitly dropped the direct label `will_delay` and the label-derived field `schedule_slippage_pct`.
- Dropped ID/date-like and timestamp columns (name patterns: id, date, time, timestamp, start, end, planned, actual, year, month, day) to avoid future-derived leakage.
- Splits are written to `data_splits/v5/` and use a project-level reproducible split with `random_state` and a row-level fallback.

**Recorded v5 metrics**

- See `analysis_outputs/v5/metrics.json` after training. (Commit hash below contains the v5 artifacts.)

**How v5 was produced**

1. Prepare cleaned v5 splits (drops leakage candidates and ID/date-like columns):

```bash
python scripts/prepare_splits_v5.py --random-state 42 --test-size 0.2
```

2. Train Baseline v5 and save artifacts:

```bash
python scripts/train_baseline_v5.py --random-state 42 --n-iter 12
```

**Reproducibility**

- Run inside the project Docker environment (see `scripts/run_pipeline.ps1`). Ensure `git-lfs` is used for large CSVs.

**Branch / commit reference**

- Branch: `feature/project-delay-v5`
- Commit: TO_BE_FILLED_AFTER_COMMIT


Generated: January 29, 2026
