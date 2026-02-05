#!/usr/bin/env python3
"""
Production Readiness Validator - Execute and Generate Report
"""
import subprocess
import sys
import json
from pathlib import Path

# Change to project root
ROOT = Path(__file__).parent
import os
os.chdir(str(ROOT))

# Run the validator script
print("Running production readiness validation...")
result = subprocess.run(
    [sys.executable, "scripts/production_readiness_validator.py"],
    capture_output=True,
    text=True,
    cwd=str(ROOT)
)

# Write output to files
with open("validation_output.txt", "w", encoding="utf-8", errors="replace") as f:
    f.write("=== STDOUT ===\n")
    f.write(result.stdout)
    f.write("\n\n=== STDERR ===\n")
    f.write(result.stderr)
    f.write(f"\n\n=== EXIT CODE: {result.returncode} ===\n")

print(f"Validation completed with exit code: {result.returncode}")
print(f"Output written to validation_output.txt")

# Try to read the JSON report if it exists
report_path = ROOT / "PRODUCTION_READINESS_REPORT.json"
if report_path.exists():
    with open(report_path, "r") as f:
        report = json.load(f)
    
    print(f"\n📊 PRODUCTION READINESS REPORT")
    print(f"{'='*60}")
    print(f"Overall Status: {report.get('overall_status', 'UNKNOWN')}")
    print(f"Confidence Level: {report.get('confidence_level', 'N/A')}%")
    print(f"Customer Trial Ready: {report.get('customer_trial_ready', False)}")
    
    # Summary by checkpoint
    if 'checkpoints' in report:
        passed = sum(1 for cp in report['checkpoints'].values() if cp.get('status') == 'PASS')
        total = len(report['checkpoints'])
        print(f"\nCheckpoints Passed: {passed}/{total}")
    
    # Blocking issues
    if report.get('blocking_issues'):
        print(f"\n🔴 BLOCKING ISSUES ({len(report['blocking_issues'])}):")
        for issue in report['blocking_issues'][:5]:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No blocking issues found!")
    
    # Non-blocking improvements
    if report.get('non_blocking_improvements'):
        print(f"\n⚠️  NON-BLOCKING IMPROVEMENTS ({len(report['non_blocking_improvements'])}):")
        for issue in report['non_blocking_improvements'][:3]:
            print(f"  - {issue}")

sys.exit(result.returncode)
