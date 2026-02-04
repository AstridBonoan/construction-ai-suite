# Phase 9 — Intelligence Stabilization & Output Contracts

This document describes Phase 9: freezing the intelligence outputs, feature
contracts, risk scoring, recommendations, and monday.com field mappings.

Key goals
- Produce a canonical, versioned JSON output schema for each project
- Make risk scoring deterministic and explainable
- Deliver an auditable recommendation engine (rule-first)
- Lock monday.com field mappings (no schema drift)
- Provide CI-safe validation and tests

See the repository scripts under `scripts/phase9/` for implementation details.

Schema highlights
- Version: `phase9-v1`
- Fields (per project): `project_id`, `project_name`, `risk_score` (0.0-1.0),
  `risk_level` (low/medium/high/critical), `predicted_delay_days`,
  `confidence_score` (0.0-1.0), `primary_risk_factors` (ordered list of
  {factor, weight}), `recommended_actions` (list), `model_version`,
  `generated_at` (ISO 8601)

Risk scoring
- Deterministic linear weighting over a small, documented set of features
- Normalized into 0.0–1.0, thresholds defined in `scripts/phase9/risk.py`
- Explanation strings with contribution breakdown are included in outputs

Recommendations
- Rule-based first: each recommendation references observable data and
  includes the reason and data pointers.
- Model-driven recommendations are allowed only if backed by deterministic
  rules and saved model version references (not introduced in this phase).

monday.com mapping
- Final mapping is in `scripts/phase9/monday_mapping.py` and documented here.
- Column updates are `overwrite` by default; mappings show which output field
  maps to which column ID.

Validation & CI
- Schema validation is enforced in code before writing `reports/` files.
- Unit tests validate schema enforcement and deterministic scoring.
- All tests run with `DRY_RUN=1` and `MOCK_CENTRAL_HANDLER=1` so CI stays offline.

Important: Phase 9 is intentionally UI-free. Use the JSON/CSV outputs and this
documentation as the contract for any future UI work.

Next: see `scripts/phase9/README.md` for developer notes and examples.
