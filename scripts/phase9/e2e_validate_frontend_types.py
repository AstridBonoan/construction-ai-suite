"""E2E check: compare Phase9 schema keys to frontend TypeScript `Phase9Output` keys
and validate the canonical reports/phase9_outputs.json using the Phase9 validator.

Run:
  python scripts/phase9/e2e_validate_frontend_types.py

"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.phase9 import schema as phase9_schema


def parse_ts_interface(ts_path: Path) -> set:
    txt = ts_path.read_text(encoding='utf-8')
    # crude parser: find `export interface Phase9Output {` block
    m = re.search(r"export interface Phase9Output\s*\{([\s\S]*?)\n\}", txt)
    if not m:
        raise RuntimeError('Phase9Output interface not found')
    body = m.group(1)
    keys = set()
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        # match `name: type` or `name?: type`
        mm = re.match(r"([A-Za-z0-9_]+)\??\s*:\s*", line)
        if mm:
            keys.add(mm.group(1))
    return keys


def main():
    ts_path = ROOT / 'frontend_phase10' / 'src' / 'types' / 'phase9.ts'
    reports_path = ROOT / 'reports' / 'phase9_outputs.json'
    print('Parsing TypeScript interface at', ts_path)
    ts_keys = parse_ts_interface(ts_path)
    print('TS keys:', ts_keys)

    schema_keys = set(phase9_schema.REQUIRED_FIELDS.keys()) | {'schema_version'}
    print('Schema required keys:', schema_keys)

    missing_in_ts = schema_keys - ts_keys
    extra_in_ts = ts_keys - schema_keys
    if missing_in_ts:
        print('WARNING: these schema keys are missing in TS interface:', missing_in_ts)
    if extra_in_ts:
        print('Note: extra keys in TS not in schema:', extra_in_ts)
    if not missing_in_ts:
        print('OK: TS interface covers schema required fields')

    # validate reports file
    if not reports_path.exists():
        print('reports/phase9_outputs.json not found; run generator first')
        return
    data = json.loads(reports_path.read_text(encoding='utf-8'))
    try:
        phase9_schema.validate_many(data)
        print('OK: reports/phase9_outputs.json validates against schema')
    except Exception as e:
        print('Validation error:', e)


if __name__ == '__main__':
    main()
