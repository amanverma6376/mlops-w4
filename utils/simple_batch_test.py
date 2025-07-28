#!/usr/bin/env python3

"""
Simple Batch Test
Tests batch processing using basic HTTP requests
"""

import requests
import time
import sys
from datetime import datetime

def test_single_requests(api_url: str, count: int = 10):
    """Test individual single requests"""
    test_data = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }
    
    successful = 0
    total_time = 0
    response_times = []
    
    for i in range(count):
        try:
            start_time = time.time()
            response = requests.post(f"{api_url}/predict", json=test_data, timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                successful += 1
                response_time = (end_time - start_time) * 1000
                response_times.append(response_time)
                total_time += (end_time - start_time)
        except Exception:
            pass
    
    return {
        "successful": successful,
        "total_time": total_time,
        "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
        "throughput": successful / total_time if total_time > 0 else 0
    }

def test_batch_requests(api_url: str, batch_count: int = 2, batch_size: int = 5):
    """Test batch requests"""
    # Try enhanced API format first
    batch_data_enhanced = {
        "features_list": [
            {
                "sepal_length": 5.1 + (i * 0.1),
                "sepal_width": 3.5 + (i * 0.05),
                "petal_length": 1.4 + (i * 0.1),
                "petal_width": 0.2 + (i * 0.02)
            }
            for i in range(batch_size)
        ]
    }
    
    # Basic API format
    batch_data_basic = [
        {
            "sepal_length": 5.1 + (i * 0.1),
            "sepal_width": 3.5 + (i * 0.05),
            "petal_length": 1.4 + (i * 0.1),
            "petal_width": 0.2 + (i * 0.02)
        }
        for i in range(batch_size)
    ]
    
    successful = 0
    total_time = 0
    total_predictions = 0
    api_type = "unknown"
    
    for i in range(batch_count):
        try:
            start_time = time.time()
            
            # Try enhanced format first
            response = requests.post(f"{api_url}/predict_batch", json=batch_data_enhanced, timeout=15)
            
            if response.status_code != 200:
                # Try basic format
                response = requests.post(f"{api_url}/predict_batch", json=batch_data_basic, timeout=15)
            
            end_time = time.time()
            
            if response.status_code == 200:
                successful += 1
                total_time += (end_time - start_time)
                
                # Determine API type and count predictions
                result = response.json()
                if isinstance(result, dict) and "predictions" in result:
                    total_predictions += len(result["predictions"])
                    api_type = "enhanced"
                elif isinstance(result, list):
                    total_predictions += len(result)
                    api_type = "basic"
                else:
                    total_predictions += batch_size  # Estimate
        except Exception:
            pass
    
    return {
        "successful": successful,
        "total_time": total_time,
        "total_predictions": total_predictions,
        "throughput": total_predictions / total_time if total_time > 0 else 0,
        "api_type": api_type
    }

def generate_batch_comparison_report(api_url: str):
    """Generate batch comparison report"""
    
    print(f"Testing batch processing for API: {api_url}")
    
    # Test single requests
    single_results = test_single_requests(api_url, 10)
    
    # Test batch requests
    batch_results = test_batch_requests(api_url, 2, 5)
    
    # Generate report
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    report = f"""Batch Processing Performance Comparison
==================================================
Generated: {timestamp}
API URL: {api_url}

Testing 10 total predictions...
Single requests: 10 individual requests
Batch requests: 2 batches of 5 items each

Testing single requests...
Testing batch requests...

============================================================
BATCH PROCESSING COMPARISON RESULTS
============================================================

Metric                    Single Requests      Batch Requests       Improvement    
--------------------------------------------------------------------------------
Total Time (s)            {single_results['total_time']:<20.2f} {batch_results['total_time']:<20.2f} {single_results['total_time'] - batch_results['total_time']:<15.2f}
Avg Response Time (ms)    {single_results['avg_response_time']:<20.1f} {batch_results['total_time']*1000/batch_results['successful'] if batch_results['successful'] > 0 else 0:<20.1f} {single_results['avg_response_time'] - (batch_results['total_time']*1000/batch_results['successful'] if batch_results['successful'] > 0 else 0):<15.1f}
Throughput (pred/s)       {single_results['throughput']:<20.1f} {batch_results['throughput']:<20.1f} {batch_results['throughput'] - single_results['throughput']:<15.1f}
Success Rate (%)          {(single_results['successful']/10)*100:<20.1f} {(batch_results['successful']/2)*100 if batch_results['successful'] > 0 else 0:<20.1f} {((batch_results['successful']/2)*100 if batch_results['successful'] > 0 else 0) - (single_results['successful']/10)*100:<15.1f}

============================================================
BATCH PROCESSING ANALYSIS
============================================================"""

    if batch_results['successful'] > 0:
        efficiency_ratio = batch_results['throughput'] / single_results['throughput'] if single_results['throughput'] > 0 else 1
        time_saved = single_results['total_time'] - batch_results['total_time']
        time_saved_percent = (time_saved / single_results['total_time'] * 100) if single_results['total_time'] > 0 else 0
        
        report += f"""
Batch processing is {efficiency_ratio:.1f}x more efficient
Batch processing saves {time_saved:.1f}s ({time_saved_percent:.1f}%) in total time
API Type Detected: {batch_results['api_type'].title()} API

Key advantages of batch processing:
  - Reduced network overhead
  - Better resource utilization
  - Improved model inference efficiency
  - Lower latency per prediction"""
    else:
        report += f"""
Batch processing test failed
  - Batch endpoint may not be available
  - API may not support batch operations
  - Check API documentation for batch support

Single request processing is working:
  - Success rate: {(single_results['successful']/10)*100:.1f}%
  - Average response time: {single_results['avg_response_time']:.1f}ms
  - Throughput: {single_results['throughput']:.1f} predictions/second"""

    return report

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python simple_batch_test.py <api_url>")
        sys.exit(1)
    
    api_url = sys.argv[1].rstrip('/')
    
    try:
        report = generate_batch_comparison_report(api_url)
        print(report)
    except Exception as e:
        print(f"Batch Processing Performance Comparison")
        print(f"==================================================")
        print(f"Error: Failed to test batch processing")
        print(f"Details: {str(e)}")
        print(f"API URL: {api_url}")
        print(f"")
        print(f"This may indicate:")
        print(f"  - API is not accessible")
        print(f"  - Network connectivity issues")
        print(f"  - API does not support required endpoints")
        sys.exit(1)