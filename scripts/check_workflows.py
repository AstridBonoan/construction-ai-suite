import yaml
import glob
import sys

def main():
    files = glob.glob('.github/workflows/*.yml')
    ok = True
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = yaml.safe_load(fh)
        except Exception as e:
            print(f'PARSE ERROR in {f}: {e}')
            ok = False
            continue
        if not isinstance(data, dict):
            print(f'INVALID YAML root in {f}')
            ok = False
            continue
        on = data.get('on')
        if on is None:
            print(f"MISSING or EMPTY 'on' in {f}")
            ok = False
            continue
        if (isinstance(on, dict) and len(on) == 0) or (isinstance(on, list) and len(on) == 0):
            print(f"EMPTY 'on' in {f}: {on}")
            ok = False
            continue
        print(f"OK: {f} -> triggers: {list(on.keys()) if isinstance(on, dict) else on}")
    return 0 if ok else 2

if __name__ == '__main__':
    sys.exit(main())
