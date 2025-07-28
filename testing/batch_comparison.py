#!/usr/bin/env python3

"""
Batch Processing Comparison Script
Compares single requests vs batch requests performance
"""

import requests
import time
import statistics
from typing import List, Dict

def test_single_requests(api_url: str, num_requests: int) -> Dict:
    """Test individual single requests"""
    
    test_data = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }
    
    response_times = []
    successful = 0
    failed = 0
    
    start_time = time.time()
    
    for i in range(num_requests):
        request_start = time.time()
        try:
            response = requests.post(f"{api_url}/predict", json=test_data, timeout=5)
            request_end = time.time()
            
            if response.status_code == 200:
                successful += 1
                response_times.append(request_end - request_start)
            else:
                failed += 1
                
        except Exception as e:
            failed += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        'total_time': total_time,
        'avg_response_time': statistics.mean(response_times) if response_times else 0,
        'successful': successful,
        'failed': failed,
        'throughput': successful / total_time if total_time > 0 else 0
    }

def detect_api_type(api_url: str) -> str:
    """Detect if API is basic or enhanced"""
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "version" in data and data.get("version") == "2.0.0":
                return "enhanced"
            elif "features" in data:
                return "enhanced"
        return "basic"
    except:
        return "basic"

def test_batch_requests(api_url: str, num_batches: int, batch_size: int) -> Dict:
    """Test batch requests"""
    
    # Detect API type to format request correctly
    api_type = detect_api_type(api_url)
    
    # Create base feature data
    features_data = [
        {
            "sepal_length": 5.1 + (i * 0.1),
            "sepal_width": 3.5 + (i * 0.05),
            "petal_length": 1.4 + (i * 0.1),
            "petal_width": 0.2 + (i * 0.02)
        }
        for i in range(batch_size)
    ]
    
    # Format request based on API type
    if api_type == "enhanced":
        # Enhanced API expects BatchPredictionRequest format
        batch_data = {
            "features_list": features_data,
            "batch_id": f"test_batch_{int(time.time())}"
        }
    else:
        # Basic API expects direct list
        batch_data = features_data
    
    response_times = []
    successful = 0
    failed = 0
    total_predictions = 0
    
    start_time = time.time()
    
    for i in range(num_batches):
        request_start = time.time()
        try:
            response = requests.post(f"{api_url}/predict_batch", json=batch_data, timeout=10)
            request_end = time.time()
            
            if response.status_code == 200:
                successful += 1
                total_predictions += batch_size
                response_times.append(request_end - request_start)
            else:
                failed += 1
                
        except Exception as e:
            failed += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    
    return {
        'total_time': total_time,
        'avg_response_time': statistics.mean(response_times) if response_times else 0,
        'successful': successful,
        'failed': failed,
        'total_predictions': total_predictions,
        'throughput': total_predictions / total_time if total_time > 0 else 0
    }

def run_batch_comparison(api_url: str = "http://localhost:8000"):
    """Run batch vs single request comparison"""
    
    print("Batch Processing Performance Comparison")
    print("=" * 50)
    
    # Test configurations
    num_predictions = 50  # Total predictions to make
    batch_size = 10
    num_batches = num_predictions // batch_size
    
    print(f"Testing {num_predictions} total predictions...")
    print(f"Single requests: {num_predictions} individual requests")
    print(f"Batch requests: {num_batches} batches of {batch_size} items each")
    print()
    
    # Test single requests
    print("Testing single requests...")
    single_results = test_single_requests(api_url, num_predictions)
    
    # Small delay
    time.sleep(2)
    
    # Test batch requests
    print("Testing batch requests...")
    batch_results = test_batch_requests(api_url, num_batches, batch_size)
    
    # Display results
    print("\n" + "=" * 60)
    print("BATCH PROCESSING COMPARISON RESULTS")
    print("=" * 60)
    
    print(f"\n{'Metric':<25} {'Single Requests':<20} {'Batch Requests':<20} {'Improvement':<15}")
    print("-" * 80)
    
    # Total time comparison
    time_improvement = single_results['total_time'] - batch_results['total_time']
    time_change = ((batch_results['total_time'] - single_results['total_time']) / single_results['total_time'] * 100) if single_results['total_time'] > 0 else 0
    
    print(f"{'Total Time (s)':<25} {single_results['total_time']:<20.2f} {batch_results['total_time']:<20.2f} {time_improvement:<15.2f}")
    
    # Average response time comparison
    rt_improvement = single_results['avg_response_time'] - batch_results['avg_response_time']
    rt_change = ((batch_results['avg_response_time'] - single_results['avg_response_time']) / single_results['avg_response_time'] * 100) if single_results['avg_response_time'] > 0 else 0
    
    print(f"{'Avg Response Time (s)':<25} {single_results['avg_response_time']:<20.3f} {batch_results['avg_response_time']:<20.3f} {rt_improvement:<15.3f}")
    
    # Throughput comparison
    throughput_improvement = batch_results['throughput'] - single_results['throughput']
    throughput_change = ((batch_results['throughput'] - single_results['throughput']) / single_results['throughput'] * 100) if single_results['throughput'] > 0 else 0
    
    print(f"{'Throughput (pred/s)':<25} {single_results['throughput']:<20.1f} {batch_results['throughput']:<20.1f} {throughput_improvement:<15.1f}")
    
    # Success rate comparison
    single_success_rate = (single_results['successful'] / (single_results['successful'] + single_results['failed']) * 100) if (single_results['successful'] + single_results['failed']) > 0 else 0
    batch_success_rate = (batch_results['successful'] / (batch_results['successful'] + batch_results['failed']) * 100) if (batch_results['successful'] + batch_results['failed']) > 0 else 0
    success_improvement = batch_success_rate - single_success_rate
    
    print(f"{'Success Rate (%)':<25} {single_success_rate:<20.1f} {batch_success_rate:<20.1f} {success_improvement:<15.1f}")
    
    # Summary
    print(f"\n{'='*60}")
    print("BATCH PROCESSING BENEFITS")
    print(f"{'='*60}")
    
    if batch_results['throughput'] > single_results['throughput']:
        efficiency_gain = (batch_results['throughput'] / single_results['throughput'])
        print(f"Batch processing is {efficiency_gain:.1f}x more efficient")
    
    if batch_results['total_time'] < single_results['total_time']:
        time_saved = single_results['total_time'] - batch_results['total_time']
        time_saved_percent = (time_saved / single_results['total_time'] * 100)
        print(f"Batch processing saves {time_saved:.1f}s ({time_saved_percent:.1f}%) in total time")
    
    print(f"\nKey advantages of batch processing:")
    print(f"  - Reduced network overhead")
    print(f"  - Better resource utilization")
    print(f"  - Improved model inference efficiency")
    print(f"  - Lower latency per prediction")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python batch_comparison.py <api_url>")
        sys.exit(1)
    
    api_url = sys.argv[1]
    
    try:
        print(f"Testing batch comparison for API: {api_url}")
        
        # Check if API is accessible
        response = requests.get(f"{api_url}/health", timeout=10)
        if response.status_code != 200:
            print(f"Error: API at {api_url} is not accessible (Status: {response.status_code})")
            sys.exit(1)
        
        print("API health check passed, running batch comparison...")
        run_batch_comparison(api_url)
        
    except requests.exceptions.RequestException as e:
        print(f"Network error connecting to API: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running batch comparison: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)