"""
Simple CI check to prevent committing Monday config files containing plaintext tokens.

Usage (pre-commit):
    python scripts/ci_checks.py

Exits with code 1 if any config file under `configs/` contains an unencrypted `api_key` or `token` field.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs"


def check_file(p: Path):
    try:
        j = json.load(open(p, "r", encoding="utf-8"))
    except Exception:
        return []
    issues = []
    # If file is an encrypted wrapper, it's ok
    if isinstance(j, dict) and j.get("_encrypted"):
        return []
    # Allow template/example files that contain placeholder values
    name_l = p.stem.lower()
    if "template" in name_l or "example" in name_l or "sample" in name_l:
        return []
    # Check common token fields
    for key in ("api_key", "access_token", "token"):
        if key in j and j.get(key):
            val = str(j.get(key))
            vlow = val.lower()
            # skip obvious placeholders or simulated values
            if any(
                x in vlow
                for x in (
                    "placeholder",
                    "replace_me",
                    "replace",
                    "example",
                    "simulated",
                    "dummy",
                )
            ):
                continue
            issues.append(f"Found plaintext '{key}' in {p}")
    return issues


def main():
    if not CONFIG_DIR.exists():
        print("No configs/ directory found — skipping checks")
        return 0
    problems = []
    for f in CONFIG_DIR.glob("*.json"):
        problems += check_file(f)
    if problems:
        print("CI check failed: potential secret leaks detected:")
        for p in problems:
            print(" -", p)
        print(
            "\nRemediation: remove secrets from committed files or use encrypted/managed backend."
        )
        return 1
    print("CI check passed: no plaintext tokens found in configs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
