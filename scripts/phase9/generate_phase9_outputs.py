"""Generate Phase 9 outputs for local development.

This utility reads the existing frontend mock (or other source), stamps
`generated_at` with the current time and writes a validated Phase9 outputs
file to `reports/phase9_outputs.json` using the canonical output writer.

Run locally when you want to produce a canonical Phase9 outputs file for
integration testing:

    python scripts/phase9/generate_phase9_outputs.py

"""
from pathlib import Path
import json
from datetime import datetime, timezone
import sys

# ensure repo root is on sys.path so we can import package-style modules
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    from scripts.phase9 import output_writer
except Exception:
    # fallback when running inside scripts/phase9 directly
    from phase9 import output_writer


MOCK_PATH = ROOT / 'frontend_phase10' / 'src' / 'mock' / 'phase9_sample.json'
OUT_DIR = ROOT / 'reports'
OUT_PATH = OUT_DIR / 'phase9_outputs.json'


def main():
    if not MOCK_PATH.exists():
        print('Mock sample not found at', MOCK_PATH)
        return
    with open(MOCK_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # stamp generated_at to now
    now = datetime.now(timezone.utc).isoformat()
    for obj in data:
        obj['generated_at'] = now

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # write validated outputs
    try:
        output_writer.write_phase9_outputs(OUT_PATH, data)
        print('Wrote phase9 outputs to', OUT_PATH)
    except Exception as e:
        print('Failed to write outputs:', e)


if __name__ == '__main__':
    main()
