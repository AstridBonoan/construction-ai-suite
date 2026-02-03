#!/usr/bin/env python3
"""Map transformed feature names back to original columns for v5 preprocessor.

Writes:
- analysis_outputs/v5/transformed_feature_mapping.csv
- analysis_outputs/v5/transformed_leakage_summary.txt
"""

from __future__ import annotations
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

ROOT = Path(".")
MODEL = ROOT / "models" / "v5" / "baseline_project_delay_model_v5.pkl"
OUT_DIR = ROOT / "analysis_outputs" / "v5"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "transformed_feature_mapping.csv"
OUT_TXT = OUT_DIR / "transformed_leakage_summary.txt"
DEEP = OUT_DIR / "deep_leakage_candidates.csv"


def load_deep_candidates():
    if not DEEP.exists():
        return set()
    try:
        df = pd.read_csv(DEEP, low_memory=False)
        return set(df["feature"].astype(str).tolist())
    except Exception:
        return set()


def main():
    model = joblib.load(MODEL)
    pre = None
    try:
        pre = model.named_steps["pre"]
    except Exception:
        raise SystemExit("Preprocessor not found in model pipeline")

    feat_names = []
    try:
        feat_names = list(pre.get_feature_names_out())
    except Exception:
        # fallback: empty
        feat_names = []

    mapping_rows = []
    # build a dict of transformer -> original cols from transformers_
    transform_info = []
    try:
        for name, trans, cols in pre.transformers_:
            transform_info.append((name, trans, cols))
    except Exception:
        transform_info = []

    deep_candidates = load_deep_candidates()

    # For each transformer, try to enumerate transformed names and map
    handled = set()
    for name, trans, cols in transform_info:
        if name == "remainder" or trans == "drop":
            continue
        # resolve original columns list
        orig_cols = []
        if isinstance(cols, (list, tuple, np.ndarray)):
            orig_cols = list(cols)
        else:
            # cols could be slice or string
            try:
                orig_cols = list(cols)
            except Exception:
                orig_cols = [str(cols)]

        # attempt per-transformer handling
        # If transformer is a Pipeline, get last step
        last = trans
        try:
            if hasattr(trans, "named_steps"):
                # pipeline
                # get last step
                last_name = list(trans.named_steps.keys())[-1]
                last = trans.named_steps[last_name]
        except Exception:
            last = trans

        # If OneHotEncoder-like
        try:
            from sklearn.preprocessing import OneHotEncoder

            is_ohe = isinstance(last, OneHotEncoder)
        except Exception:
            is_ohe = False

        if is_ohe:
            try:
                # OneHotEncoder can produce feature names
                # ask for ohe.get_feature_names_out(orig_cols)
                raw_names = last.get_feature_names_out(orig_cols)
            except Exception:
                raw_names = []
            for rn in raw_names:
                # full name likely is f"{name}__{rn}"
                full = f"{name}__{rn}"
                # try to find match in feat_names
                if full in feat_names:
                    mapped_orig = rn.split("_")[0] if "_" in rn else rn
                    mapping_rows.append(
                        {
                            "transformed_feature": full,
                            "original_column": mapped_orig,
                            "transformer": name,
                            "flagged_reason": (
                                "deep_candidate" if full in deep_candidates else ""
                            ),
                        }
                    )
                    handled.add(full)
                else:
                    # try without prefix
                    if rn in feat_names:
                        mapping_rows.append(
                            {
                                "transformed_feature": rn,
                                "original_column": (
                                    rn.split("_")[0] if "_" in rn else rn
                                ),
                                "transformer": name,
                                "flagged_reason": (
                                    "deep_candidate" if rn in deep_candidates else ""
                                ),
                            }
                        )
                        handled.add(rn)
        else:
            # numeric or passthrough: expect one-to-one mapping
            for col in orig_cols:
                col_str = str(col)
                # expected name
                candidates = [f"{name}__{col_str}", f"{name}__{col_str} ", col_str]
                matched = None
                for c in candidates:
                    if c in feat_names:
                        matched = c
                        break
                if matched is None:
                    # try substring match
                    for fn in feat_names:
                        if col_str in fn:
                            matched = fn
                            break
                if matched:
                    mapping_rows.append(
                        {
                            "transformed_feature": matched,
                            "original_column": col_str,
                            "transformer": name,
                            "flagged_reason": (
                                "deep_candidate"
                                if matched in deep_candidates
                                or matched.replace(" ", "") in deep_candidates
                                else ""
                            ),
                        }
                    )
                    handled.add(matched)
                else:
                    # record no transformed name found
                    mapping_rows.append(
                        {
                            "transformed_feature": "",
                            "original_column": col_str,
                            "transformer": name,
                            "flagged_reason": "",
                        }
                    )

    # For any remaining feat_names not handled, add best-effort mapping
    for fn in feat_names:
        if fn in handled:
            continue
        # split by '__' to get transformer and rest
        if "__" in fn:
            prefix, rest = fn.split("__", 1)
            # attempt to extract original col as first token before '_' or '='
            orig = rest.split("_")[0] if "_" in rest else rest.split("=")[0]
            mapping_rows.append(
                {
                    "transformed_feature": fn,
                    "original_column": orig,
                    "transformer": prefix,
                    "flagged_reason": (
                        "deep_candidate" if fn in deep_candidates else ""
                    ),
                }
            )
        else:
            mapping_rows.append(
                {
                    "transformed_feature": fn,
                    "original_column": "",
                    "transformer": "",
                    "flagged_reason": (
                        "deep_candidate" if fn in deep_candidates else ""
                    ),
                }
            )

    df_map = pd.DataFrame(mapping_rows)
    df_map.to_csv(OUT_CSV, index=False)

    # produce summary: group by original_column where any transformed features flagged
    flagged = df_map[df_map["flagged_reason"] != ""]
    with open(OUT_TXT, "w", encoding="utf8") as fh:
        fh.write("Transformed feature mapping and leakage summary\n")
        fh.write(f"Total transformed features mapped: {len(df_map)}\n")
        fh.write(
            f"Total flagged transformed features (deep candidates): {len(flagged)}\n\n"
        )
        fh.write("Flagged original columns (and transformed features):\n")
        for orig, group in flagged.groupby("original_column"):
            fh.write(f" - {orig}:\n")
            for _, r in group.iterrows():
                fh.write(
                    f"    - {r['transformed_feature']} (transformer={r['transformer']})\n"
                )
        fh.write("\nRecommendations:\n")
        fh.write(
            "- Remove or prevent construction of the above transformed features that map to original columns containing target-derived values.\n"
        )
        fh.write(
            "- Audit join/aggregation steps that produce the original columns listed above (look in scripts/prepare_splits_v*.py and any earlier preprocessing).\n"
        )
        fh.write(
            "- Ensure that `will_delay` and `schedule_slippage_pct` are never merged into feature rows during feature engineering.\n"
        )

    print("Wrote mapping to", OUT_CSV)
    print("Wrote summary to", OUT_TXT)


if __name__ == "__main__":
    main()
