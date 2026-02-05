#!/usr/bin/env python3
"""Quick test of explain_risk_score"""
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "app"))

try:
    from app.phase15_explainability import RiskExplainer
    
    exp = RiskExplainer()
    result = exp.explain_risk_score(
        risk_score=0.45,
        project_name="Test Project",
        additional_context={"budget": 1_000_000}
    )
    print(f"✅ SUCCESS")
    print(f"Summary: {result.summary}")
    print(f"Confidence: {result.confidence_level} ({result.confidence_percentage}%)")
    print(f"Factors: {len(result.key_factors)}")
    
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
