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

Generated: January 29, 2026
