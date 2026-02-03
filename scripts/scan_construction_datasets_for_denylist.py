"""scan_construction_datasets_for_denylist.py

Non-destructive verification scan of raw input files.

Purpose: validate ingestion-time leakage prevention by checking which source
files contain deny-listed columns (label-derived or post-outcome fields).

This script is informational only: it does NOT modify any files and will
exit with code 0 even if it cannot read some files. Presence of hits is
expected — the deny-list in `prepare_project_dataset.py` is meant to remove
these at ingestion.

Outputs:
 - construction_datasets_denylist_hits.csv
 - construction_datasets_denylist_hits.txt

Run from repository root:
  python scripts/scan_construction_datasets_for_denylist.py
"""

from __future__ import annotations
import csv
import sys
from pathlib import Path
import re
from typing import List, Dict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "construction_datasets"
OUT_CSV = ROOT / "construction_datasets_denylist_hits.csv"
OUT_TXT = ROOT / "construction_datasets_denylist_hits.txt"

# ------------------ Deny-list (kept in sync with prepare_project_dataset.py) ------------------
DENY_LIST_EXACT = {
    "will_delay",
    "schedule_slippage_pct",
    "slippage_days",
    "elapsed_days",
    "planned_duration_days",
    "actual_end",
    "planned_end",
    "actual_start",
    "Final Estimate of Actual Costs Through End of Phase Amount",
    "Total Phase Actual Spending Amount",
    "Award",
    "BBL",
    "BIN",
    "Borough",
    "Budget_Line",
}

DENY_LIST_PATTERNS = [
    r"(?i)^budget_line",
    r"(?i)final.*cost",
    r"(?i)actual.*cost",
    r"(?i)total.*actual.*spend",
    r"(?i)actual_?end",
    r"(?i)planned_?end",
    r"(?i)actual_?start",
    r"(?i)elapsed_?days",
    r"(?i)slippage",
    r"(?i)will_?delay",
]
# ----------------------------------------------------------------------------------------------


def read_csv_header(path: Path) -> List[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            return [h.strip() for h in header]
    except Exception:
        # Fallback: try pandas if available (but do not require it)
        try:
            import pandas as pd

            df = pd.read_csv(path, nrows=0, low_memory=True)
            return list(df.columns)
        except Exception:
            return []


def read_parquet_header(path: Path) -> List[str]:
    # Try pyarrow first (cheap metadata access), fall back to pandas
    try:
        import pyarrow.parquet as pq

        pf = pq.ParquetFile(str(path))
        return list(pf.schema.names)
    except Exception:
        try:
            import pandas as pd

            df = pd.read_parquet(
                path, engine="pyarrow", columns=[]
            )  # may still read metadata
            return list(df.columns)
        except Exception:
            return []


def check_columns(cols: List[str]) -> Dict[str, List[str]]:
    matches = {"exact": [], "pattern": []}
    lower_map = {c.lower(): c for c in cols}
    # exact checks (case-insensitive)
    for ex in DENY_LIST_EXACT:
        ex_low = ex.lower()
        if ex in cols:
            matches["exact"].append(ex)
        elif ex_low in lower_map:
            matches["exact"].append(lower_map[ex_low])
    # pattern checks
    for pat in DENY_LIST_PATTERNS:
        rx = re.compile(pat)
        for c in cols:
            if rx.search(c):
                if c not in matches["pattern"]:
                    matches["pattern"].append(c)
    return matches


def main() -> None:
    results = []
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        sys.exit(0)

    for p in sorted(DATA_DIR.rglob("*")):
        if p.is_dir():
            continue
        suffix = p.suffix.lower()
        cols: List[str] = []
        try:
            if suffix == ".csv":
                cols = read_csv_header(p)
            elif suffix in (".parquet", ".parq", ".pq"):
                cols = read_parquet_header(p)
            else:
                # skip non-CSV/parquet files
                continue
        except Exception:
            cols = []

        if not cols:
            # Could not read header; record that we attempted but couldn't inspect
            continue

        matches = check_columns(cols)
        if matches["exact"] or matches["pattern"]:
            results.append(
                {
                    "file": str(p.relative_to(ROOT)),
                    "exact_matches": (
                        ";".join(matches["exact"]) if matches["exact"] else ""
                    ),
                    "pattern_matches": (
                        ";".join(matches["pattern"]) if matches["pattern"] else ""
                    ),
                }
            )

    # Write CSV
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["file", "exact_matches", "pattern_matches"]
        )
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Write human-readable text summary
    with OUT_TXT.open("w", encoding="utf-8") as fh:
        fh.write("Deny-list scan results\n")
        fh.write("======================\n\n")
        if not results:
            fh.write("No deny-list columns found in inspected files.\n")
        else:
            for r in results:
                fh.write(f"File: {r['file']}\n")
                if r["exact_matches"]:
                    fh.write(f"  Exact matches: {r['exact_matches']}\n")
                if r["pattern_matches"]:
                    fh.write(f"  Pattern matches: {r['pattern_matches']}\n")
                fh.write("\n")

    print(f"Scan complete. Hits: {len(results)}. CSV -> {OUT_CSV}, TXT -> {OUT_TXT}")


if __name__ == "__main__":
    main()
