#!/usr/bin/env python3

"""
Simple API Connectivity Test
Tests basic API connectivity and endpoints
"""

import requests
import sys
import json
from datetime import datetime

def test_api_connectivity(api_url: str):
    """Test basic API connectivity"""
    
    print(f"Testing API connectivity: {api_url}")
    print(f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 50)
    
    results = {
        "api_accessible": False,
        "health_endpoint": False,
        "prediction_endpoint": False,
        "api_info": {}
    }
    
    # Test basic connectivity
    try:
        response = requests.get(f"{api_url}/", timeout=10)
        results["api_accessible"] = True
        print(f"✅ API accessible (Status: {response.status_code})")
        
        if response.status_code == 200:
            try:
                api_info = response.json()
                results["api_info"] = api_info
                print(f"   API Info: {json.dumps(api_info, indent=2)}")
            except:
                print("   API returned non-JSON response")
    except Exception as e:
        print(f"❌ API not accessible: {e}")
        return results
    
    # Test health endpoint
    try:
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code == 200:
            results["health_endpoint"] = True
            health_info = response.json()
            print(f"✅ Health endpoint working")
            print(f"   Health Info: {json.dumps(health_info, indent=2)}")
        else:
            print(f"❌ Health endpoint failed (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test prediction endpoint
    try:
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        response = requests.post(f"{api_url}/predict", json=test_data, timeout=10)
        if response.status_code == 200:
            results["prediction_endpoint"] = True
            prediction_result = response.json()
            print(f"✅ Prediction endpoint working")
            print(f"   Prediction: {prediction_result.get('prediction', 'unknown')}")
        else:
            print(f"❌ Prediction endpoint failed (Status: {response.status_code})")
            print(f"   Response: {response.text[:200]}")
    except Exception as e:
        print(f"❌ Prediction endpoint error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("CONNECTIVITY TEST SUMMARY")
    print("=" * 50)
    print(f"API Accessible: {'✅' if results['api_accessible'] else '❌'}")
    print(f"Health Endpoint: {'✅' if results['health_endpoint'] else '❌'}")
    print(f"Prediction Endpoint: {'✅' if results['prediction_endpoint'] else '❌'}")
    
    if all(results[key] for key in ["api_accessible", "health_endpoint", "prediction_endpoint"]):
        print("\n🎉 All connectivity tests passed! API is ready for load testing.")
        return True
    else:
        print("\n⚠️  Some connectivity tests failed. Load testing may not work properly.")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_api_connectivity.py <api_url>")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    success = test_api_connectivity(api_url)
    sys.exit(0 if success else 1)