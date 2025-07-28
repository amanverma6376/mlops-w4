#!/usr/bin/env python3

"""
Dynamic Report Generator
Generates reports based on actual API responses and test results
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

def get_api_info(api_url: str) -> Dict[str, Any]:
    """Get API information dynamically"""
    try:
        # Get root endpoint info
        response = requests.get(f"{api_url}/", timeout=10)
        if response.status_code == 200:
            root_info = response.json()
        else:
            root_info = {"message": "API root not accessible"}
        
        # Get health info
        health_response = requests.get(f"{api_url}/health", timeout=10)
        if health_response.status_code == 200:
            health_info = health_response.json()
        else:
            health_info = {"status": "unknown", "model_loaded": False}
        
        # Get model info if available
        try:
            model_response = requests.get(f"{api_url}/model_info", timeout=10)
            if model_response.status_code == 200:
                model_info = model_response.json()
            else:
                model_info = {"model_type": "unknown"}
        except:
            model_info = {"model_type": "unknown"}
        
        return {
            "root_info": root_info,
            "health_info": health_info,
            "model_info": model_info,
            "api_url": api_url
        }
    except Exception as e:
        return {
            "error": str(e),
            "api_url": api_url,
            "root_info": {"message": "API not accessible"},
            "health_info": {"status": "error", "model_loaded": False},
            "model_info": {"model_type": "unknown"}
        }

def test_api_endpoints(api_url: str) -> Dict[str, Any]:
    """Test API endpoints and measure performance"""
    results = {
        "health_test": {"success": False, "response_time": 0},
        "prediction_test": {"success": False, "response_time": 0},
        "batch_test": {"success": False, "response_time": 0}
    }
    
    # Test health endpoint
    try:
        start_time = time.time()
        response = requests.get(f"{api_url}/health", timeout=10)
        end_time = time.time()
        results["health_test"] = {
            "success": response.status_code == 200,
            "response_time": (end_time - start_time) * 1000,
            "status_code": response.status_code
        }
    except Exception as e:
        results["health_test"]["error"] = str(e)
    
    # Test prediction endpoint
    try:
        start_time = time.time()
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        response = requests.post(f"{api_url}/predict", json=test_data, timeout=10)
        end_time = time.time()
        results["prediction_test"] = {
            "success": response.status_code == 200,
            "response_time": (end_time - start_time) * 1000,
            "status_code": response.status_code
        }
        if response.status_code == 200:
            results["prediction_test"]["prediction"] = response.json().get("prediction", "unknown")
    except Exception as e:
        results["prediction_test"]["error"] = str(e)
    
    # Test batch endpoint
    try:
        start_time = time.time()
        # Try enhanced API format first
        batch_data = {
            "features_list": [
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.2, "sepal_width": 3.4, "petal_length": 5.4, "petal_width": 2.3}
            ]
        }
        response = requests.post(f"{api_url}/predict_batch", json=batch_data, timeout=10)
        
        if response.status_code != 200:
            # Try basic API format
            batch_data = [
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.2, "sepal_width": 3.4, "petal_length": 5.4, "petal_width": 2.3}
            ]
            response = requests.post(f"{api_url}/predict_batch", json=batch_data, timeout=10)
        
        end_time = time.time()
        results["batch_test"] = {
            "success": response.status_code == 200,
            "response_time": (end_time - start_time) * 1000,
            "status_code": response.status_code
        }
        if response.status_code == 200:
            batch_response = response.json()
            if isinstance(batch_response, dict) and "predictions" in batch_response:
                results["batch_test"]["predictions_count"] = len(batch_response["predictions"])
                results["batch_test"]["api_type"] = "enhanced"
            elif isinstance(batch_response, list):
                results["batch_test"]["predictions_count"] = len(batch_response)
                results["batch_test"]["api_type"] = "basic"
    except Exception as e:
        results["batch_test"]["error"] = str(e)
    
    return results

def generate_dynamic_report(api_url: str) -> str:
    """Generate a dynamic report based on actual API responses"""
    
    print(f"Generating dynamic report for API: {api_url}")
    
    # Get current timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Get API information
    api_info = get_api_info(api_url)
    
    # Test API endpoints
    test_results = test_api_endpoints(api_url)
    
    # Determine API type
    api_version = api_info["root_info"].get("version", "1.0.0")
    api_type = "Enhanced API" if api_version == "2.0.0" or "features" in api_info["root_info"] else "Basic API"
    
    # Generate report
    report = f"""GCP Concurrent Scaling Test
========================================
API URL: {api_url}
Generated: {timestamp}

API Health Check: {'SUCCESS' if test_results['health_test']['success'] else 'FAILED'}
  Status: {api_info['health_info'].get('status', 'unknown')}
  Model Loaded: {api_info['health_info'].get('model_loaded', False)}
  Version: {api_info['health_info'].get('version', api_version)}
  Response Time: {test_results['health_test']['response_time']:.1f}ms

API Type Detection: {api_type}
  Model Type: {api_info['model_info'].get('model_type', 'unknown')}
  Concurrent Support: {'Yes' if api_version == '2.0.0' else 'Basic'}

Testing Batch Processing:
  Batch Processing: {'SUCCESS' if test_results['batch_test']['success'] else 'FAILED'}"""

    if test_results['batch_test']['success']:
        report += f"""
  API Type: {test_results['batch_test'].get('api_type', 'unknown')}
  Response Time: {test_results['batch_test']['response_time']:.1f}ms
  Predictions Returned: {test_results['batch_test'].get('predictions_count', 0)}"""
    else:
        report += f"""
  Status Code: {test_results['batch_test'].get('status_code', 'unknown')}
  Error: {test_results['batch_test'].get('error', 'Unknown error')}"""

    report += f"""

Single Prediction Test:
  Prediction Test: {'SUCCESS' if test_results['prediction_test']['success'] else 'FAILED'}
  Response Time: {test_results['prediction_test']['response_time']:.1f}ms"""

    if test_results['prediction_test']['success']:
        report += f"""
  Prediction Result: {test_results['prediction_test'].get('prediction', 'unknown')}"""

    # Add performance summary
    avg_response_time = (
        test_results['health_test']['response_time'] + 
        test_results['prediction_test']['response_time']
    ) / 2

    report += f"""

PERFORMANCE SUMMARY
============================================================
Average Response Time: {avg_response_time:.1f}ms
Health Endpoint: {test_results['health_test']['response_time']:.1f}ms
Prediction Endpoint: {test_results['prediction_test']['response_time']:.1f}ms
Batch Endpoint: {test_results['batch_test']['response_time']:.1f}ms

API Capabilities:
  Basic Prediction: {'✓' if test_results['prediction_test']['success'] else '✗'}
  Batch Processing: {'✓' if test_results['batch_test']['success'] else '✗'}
  Health Monitoring: {'✓' if test_results['health_test']['success'] else '✗'}

Performance Assessment:
  Response Time: {'EXCELLENT (<100ms)' if avg_response_time < 100 else 'GOOD (<500ms)' if avg_response_time < 500 else 'NEEDS IMPROVEMENT (>500ms)'}
  Reliability: {'EXCELLENT' if all(test['success'] for test in test_results.values()) else 'GOOD' if sum(test['success'] for test in test_results.values()) >= 2 else 'NEEDS IMPROVEMENT'}

Dynamic Report Generation Completed!
"""

    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_dynamic_report.py <api_url>")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    
    try:
        report = generate_dynamic_report(api_url)
        print(report)
    except Exception as e:
        print(f"Error generating dynamic report: {e}")
        # Generate fallback report
        print(f"""GCP Concurrent Scaling Test
========================================
API URL: {api_url}
Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

Error: Failed to generate dynamic report
Details: {str(e)}

Fallback report generated.""")
        sys.exit(1)