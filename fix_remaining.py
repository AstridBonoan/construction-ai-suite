#!/usr/bin/env python3
"""Fix remaining parameter name issues"""

with open('scripts/production_readiness_validator.py', 'r') as f:
    lines = f.readlines()

fixed = []
for i, line in enumerate(lines, 1):
    # Only fix score= that appears in function calls, not in variable names
    if 'score=' in line and 'risk_score=' not in line and 'explain_risk_score' in '\n'.join(lines[max(0,i-10):i]):
        line = line.replace('score=', 'risk_score=')
    # Fix context= in same context
    if 'context=' in line and 'additional_context=' not in line and 'explain_risk_score' in '\n'.join(lines[max(0,i-10):i]):
        line = line.replace('context=', 'additional_context=')
    fixed.append(line)

with open('scripts/production_readiness_validator.py', 'w') as f:
    f.writelines(fixed)

print("Fixed all parameter names")
