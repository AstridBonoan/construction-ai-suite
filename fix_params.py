#!/usr/bin/env python3
"""Quick script to fix parameter names in validator"""
import re

with open('scripts/production_readiness_validator.py', 'r') as f:
    content = f.read()

# Replace score= with risk_score=
content = re.sub(r'score=', 'risk_score=', content)

# Replace context= with additional_context= (but not in comments or strings about context)
# Be careful not to replace in explain_risk_score signature itself
lines = content.split('\n')
new_lines = []
for line in lines:
    # Only replace context= that appears as a parameter inside explain_risk_score calls
    if 'explain_risk_score' in '\n'.join(new_lines[-3:] if len(new_lines) >= 3 else new_lines) or 'context=' in line:
        line = re.sub(r'\bcontext=', 'additional_context=', line)
    new_lines.append(line)

content = '\n'.join(new_lines)

with open('scripts/production_readiness_validator.py', 'w') as f:
    f.write(content)

print("✅ Fixed all parameter names")
