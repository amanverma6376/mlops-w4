#!/usr/bin/env python3

"""
Test script to verify batch processing works with both basic and enhanced APIs
"""

import requests
import json

def test_basic_api():
    """Test batch processing with basic API (iris_api.py)"""
    print("Testing Basic API (iris_api.py)...")
    
    # Basic API expects direct list of features
    batch_data = [
        {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        },
        {
            "sepal_length": 6.2,
            "sepal_width": 3.4,
            "petal_length": 5.4,
            "petal_width": 2.3
        }
    ]
    
    try:
        response = requests.post("http://localhost:8000/predict_batch", json=batch_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Predictions returned: {len(data)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_enhanced_api():
    """Test batch processing with enhanced API (iris_api_enhanced.py)"""
    print("\nTesting Enhanced API (iris_api_enhanced.py)...")
    
    # Enhanced API expects BatchPredictionRequest format
    batch_data = {
        "features_list": [
            {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            },
            {
                "sepal_length": 6.2,
                "sepal_width": 3.4,
                "petal_length": 5.4,
                "petal_width": 2.3
            }
        ],
        "batch_id": "test_batch_123"
    }
    
    try:
        response = requests.post("http://localhost:8001/predict_batch", json=batch_data, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Batch ID: {data.get('batch_id', 'N/A')}")
            print(f"Predictions returned: {len(data.get('predictions', []))}")
            print(f"Total processing time: {data.get('total_processing_time_ms', 0):.2f}ms")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Batch Processing API Compatibility Test")
    print("=" * 50)
    
    basic_success = test_basic_api()
    enhanced_success = test_enhanced_api()
    
    print(f"\n" + "=" * 50)
    print("RESULTS:")
    print(f"Basic API (port 8000): {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"Enhanced API (port 8001): {'✅ PASS' if enhanced_success else '❌ FAIL'}")
    
    if basic_success and enhanced_success:
        print("\n🎉 Both APIs support batch processing correctly!")
    elif basic_success or enhanced_success:
        print("\n⚠️  One API working, check the other configuration")
    else:
        print("\n❌ Both APIs failed - check if servers are running")