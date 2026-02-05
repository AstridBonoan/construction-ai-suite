import re

with open('scripts/production_readiness_validator.py', 'r') as f:
    content = f.read()

# Replace score= with risk_score=
content = content.replace('score=', 'risk_score=')
# Replace context= with additional_context=
content = content.replace('context=', 'additional_context=')

with open('scripts/production_readiness_validator.py', 'w') as f:
    f.write(content)

print("Fixed parameters")
