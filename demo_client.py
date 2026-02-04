#!/usr/bin/env python3
"""
Demo Client for Construction AI Suite
Test the API with sample construction projects
"""
import json
import requests
from pathlib import Path

# Demo data
SAMPLE_PROJECTS = [
    {
        "project_id": "DEMO_001",
        "project_name": "Downtown Office Complex Renovation",
        "risk_score": 0.35,
        "delay_probability": 0.28,
        "predicted_delay_days": 5,
        "budget": 2500000,
        "actual_spend": 1200000,
        "scheduled_duration_days": 180,
        "actual_duration_days": 92,
        "phase": "construction",
        "status": "active",
        "location": "Downtown",
        "description": "Mid-rise office building renovation with modern amenities",
        "complexity": "medium",
        "team_size": 45,
        "key_risks": ["weather_delays", "material_sourcing"]
    },
    {
        "project_id": "DEMO_002",
        "project_name": "Highway Interchange Expansion",
        "risk_score": 0.68,
        "delay_probability": 0.72,
        "predicted_delay_days": 18,
        "budget": 8500000,
        "actual_spend": 3200000,
        "scheduled_duration_days": 365,
        "actual_duration_days": 145,
        "phase": "construction",
        "status": "active",
        "location": "Highway corridor",
        "description": "Major highway interchange expansion project",
        "complexity": "high",
        "team_size": 120,
        "key_risks": ["traffic_management", "weather", "supplier_delays"]
    },
    {
        "project_id": "DEMO_003",
        "project_name": "School Renovation and Expansion",
        "risk_score": 0.42,
        "delay_probability": 0.35,
        "predicted_delay_days": 8,
        "budget": 5000000,
        "actual_spend": 2100000,
        "scheduled_duration_days": 240,
        "actual_duration_days": 110,
        "phase": "construction",
        "status": "active",
        "location": "Downtown",
        "description": "School building expansion with new wings and HVAC upgrade",
        "complexity": "medium",
        "team_size": 65,
        "key_risks": ["student_operations", "material_sourcing"]
    }
]

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*70)
    print("TEST 1: Health Check")
    print("="*70)
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_phase9_data():
    """Test Phase 9 outputs endpoint"""
    print("\n" + "="*70)
    print("TEST 2: Phase 9 Data Retrieval")
    print("="*70)
    try:
        response = requests.get("http://localhost:5000/phase9/outputs?variant=live", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Projects received: {len(data)}")
        if len(data) > 0:
            print(f"\nFirst project:")
            project = data[0]
            print(f"  Name: {project.get('project_name')}")
            print(f"  Risk Score: {project.get('risk_score')}")
            print(f"  Delay Probability: {project.get('delay_probability')}")
            print(f"  Predicted Delay: {project.get('predicted_delay_days')} days")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analyze_project():
    """Test project analysis endpoint"""
    print("\n" + "="*70)
    print("TEST 3: Project Analysis (Explainability)")
    print("="*70)
    try:
        project = SAMPLE_PROJECTS[0]
        
        payload = {
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "risk_score": project["risk_score"],
            "delay_probability": project["delay_probability"],
            "predicted_delay_days": project["predicted_delay_days"],
            "budget": project["budget"],
            "complexity": project["complexity"]
        }
        
        print(f"\nAnalyzing: {project['project_name']}")
        print(f"Risk Score: {project['risk_score']}")
        print(f"Delay Probability: {project['delay_probability']}")
        
        response = requests.post(
            "http://localhost:5000/api/analyze_project",
            json=payload,
            timeout=5
        )
        
        print(f"\nStatus: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nResults:")
            print(f"  Risk Level: {result.get('risk_level', 'N/A')}")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            if 'summary' in result:
                print(f"  Summary: {result['summary'][:150]}...")
            if 'recommendations' in result:
                print(f"\n  Recommendations:")
                for i, rec in enumerate(result.get('recommendations', [])[:3], 1):
                    print(f"    {i}. {rec}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("  CONSTRUCTION AI SUITE - DEMO CLIENT")
    print("="*70)
    print("\nTesting API endpoints...")
    print("Server URL: http://localhost:5000")
    
    # Run tests
    results = {}
    results["Health Check"] = test_health_check()
    results["Phase 9 Data"] = test_phase9_data()
    results["Project Analysis"] = test_analyze_project()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the server logs.")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
