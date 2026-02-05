#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).parent
print(f"ROOT: {ROOT}")
print(f"Backend exists: {(ROOT / 'backend').exists()}")
print(f"Backend/app exists: {(ROOT / 'backend' / 'app').exists()}")
print(f"Python version: {sys.version}")
print(f"sys.path: {sys.path[:3]}")

# Try importing
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app"))

try:
    from app.phase15_explainability import RiskExplainer
    print("✅ Successfully imported RiskExplainer")
    
    # Test it
    exp = RiskExplainer()
    result = exp.explain_risk_score(risk_score=0.5, project_name="Test")
    print(f"✅ RiskExplainer works: {result.summary[:50]}...")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
