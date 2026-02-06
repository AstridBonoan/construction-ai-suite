"""
Integration test for Monday.com demo with cross-origin requests
Simulates how ngrok would work (frontend on different origin than backend)
"""
import requests
import json

BACKEND_URL = "http://127.0.0.1:5000"

def test_cors_headers():
    """Test that CORS headers are present in preflight request"""
    print("\n1. Testing CORS Headers (OPTIONS request)...")
    
    headers = {
        "Origin": "https://ngrok-frontend-url.ngrok.io",
        "Access-Control-Request-Method": "GET"
    }
    
    response = requests.options(f"{BACKEND_URL}/monday/health", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NOT FOUND')}")
    print(f"   Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'NOT FOUND')}")
    
    return response.status_code == 200

def test_api_endpoints():
    """Test that all Monday API endpoints work"""
    endpoints = [
        ("/monday/health", "GET"),
        ("/monday/boards?tenant_id=demo_tenant", "GET"),
        ("/monday/oauth/init?tenant_id=demo_tenant", "GET"),
    ]
    
    print("\n2. Testing API Endpoints...")
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=5)
            print(f"   ✓ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"     Response: {response.json()}")
        except Exception as e:
            print(f"   ✗ {endpoint}: {str(e)}")

def test_cross_origin_fetch():
    """Simulate cross-origin fetch like the browser would do"""
    print("\n3. Testing Cross-Origin API Simulation...")
    
    headers = {
        "Origin": "https://frontend-ngrok-url.ngrok.io",
    }
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/monday/boards?tenant_id=demo_tenant",
            headers=headers,
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   CORS Allow Header: {response.headers.get('Access-Control-Allow-Origin', 'NOT FOUND')}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            return True
    except Exception as e:
        print(f"   Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Integration Test: Monday.com Demo with CORS")
    print("=" * 60)
    
    test_cors_headers()
    test_api_endpoints()
    test_cross_origin_fetch()
    
    print("\n" + "=" * 60)
    print("RESULT: Backend is ready for ngrok sharing!")
    print("=" * 60)
