#!/usr/bin/env python3

"""
GCP Concurrent Scaling Test Script
Runs concurrent scaling tests on deployed GCP API
"""

import asyncio
import aiohttp
import time
import statistics
import sys
import argparse
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class GCPTestResult:
    test_name: str
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    requests_per_second: float
    success_rate: float

class GCPConcurrentTester:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.results = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, data: Dict = None):
        """Make a single async request"""
        start_time = time.time()
        
        try:
            if data:
                async with session.post(f"{self.api_url}{endpoint}", json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    await response.text()
                    end_time = time.time()
                    return {
                        'success': response.status == 200,
                        'response_time': end_time - start_time,
                        'status_code': response.status,
                        'timestamp': start_time
                    }
            else:
                async with session.get(f"{self.api_url}{endpoint}", timeout=aiohttp.ClientTimeout(total=30)) as response:
                    await response.text()
                    end_time = time.time()
                    return {
                        'success': response.status == 200,
                        'response_time': end_time - start_time,
                        'status_code': response.status,
                        'timestamp': start_time
                    }
                    
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'response_time': end_time - start_time,
                'status_code': 0,
                'error': str(e),
                'timestamp': start_time
            }
    
    async def run_concurrent_test(self, test_name: str, concurrent_users: int, requests_per_user: int):
        """Run concurrent load test"""
        
        print(f"Running {test_name}:")
        print(f"  Concurrent users: {concurrent_users}")
        print(f"  Requests per user: {requests_per_user}")
        print(f"  Total requests: {concurrent_users * requests_per_user}")
        
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        # Configure connection limits for GCP
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,
            limit_per_host=concurrent_users * 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for GCP
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create all tasks
            tasks = []
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.make_request(session, "/predict", test_data)
                    tasks.append(task)
            
            # Execute all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results
            successful_results = []
            failed_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append({'error': str(result)})
                elif result['success']:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            
            # Calculate metrics
            if successful_results:
                response_times = [r['response_time'] for r in successful_results]
                response_times_sorted = sorted(response_times)
                
                p95_index = int(0.95 * len(response_times_sorted))
                
                total_time = end_time - start_time
                rps = len(successful_results) / total_time if total_time > 0 else 0
                
                test_result = GCPTestResult(
                    test_name=test_name,
                    concurrent_users=concurrent_users,
                    total_requests=len(results),
                    successful_requests=len(successful_results),
                    failed_requests=len(failed_results),
                    avg_response_time=statistics.mean(response_times),
                    p95_response_time=response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else 0,
                    requests_per_second=rps,
                    success_rate=len(successful_results) / len(results) * 100
                )
                
                self.results.append(test_result)
                
                print(f"  Results:")
                print(f"    Success Rate: {test_result.success_rate:.1f}%")
                print(f"    Avg Response Time: {test_result.avg_response_time*1000:.1f}ms")
                print(f"    P95 Response Time: {test_result.p95_response_time*1000:.1f}ms")
                print(f"    Requests/Second: {test_result.requests_per_second:.1f}")
                print(f"    Total Time: {total_time:.2f}s")
                
                return test_result
            else:
                print(f"  All requests failed!")
                return None
    
    def print_summary(self):
        """Print test summary"""
        if not self.results:
            print("No successful tests to summarize")
            return
            
        print(f"\nGCP CONCURRENT SCALING TEST SUMMARY")
        print("=" * 60)
        
        print(f"{'Test Name':<20} {'Users':<6} {'Success%':<8} {'Avg RT(ms)':<10} {'RPS':<8}")
        print("-" * 60)
        
        for result in self.results:
            print(f"{result.test_name:<20} "
                  f"{result.concurrent_users:<6} "
                  f"{result.success_rate:<8.1f} "
                  f"{result.avg_response_time*1000:<10.1f} "
                  f"{result.requests_per_second:<8.1f}")
        
        # Calculate averages
        avg_success_rate = statistics.mean([r.success_rate for r in self.results])
        avg_response_time = statistics.mean([r.avg_response_time for r in self.results])
        avg_rps = statistics.mean([r.requests_per_second for r in self.results])
        
        print(f"\nOverall Performance:")
        print(f"  Average Success Rate: {avg_success_rate:.1f}%")
        print(f"  Average Response Time: {avg_response_time*1000:.1f}ms")
        print(f"  Average Throughput: {avg_rps:.1f} RPS")
        
        # Performance assessment
        print(f"\nPerformance Assessment:")
        if avg_success_rate >= 95:
            print("  Reliability: EXCELLENT (>95% success rate)")
        elif avg_success_rate >= 90:
            print("  Reliability: GOOD (>90% success rate)")
        else:
            print("  Reliability: NEEDS IMPROVEMENT (<90% success rate)")
            
        if avg_response_time < 0.1:
            print("  Response Time: EXCELLENT (<100ms)")
        elif avg_response_time < 0.5:
            print("  Response Time: GOOD (<500ms)")
        else:
            print("  Response Time: NEEDS IMPROVEMENT (>500ms)")
            
        if avg_rps > 50:
            print("  Throughput: EXCELLENT (>50 RPS)")
        elif avg_rps > 20:
            print("  Throughput: GOOD (>20 RPS)")
        else:
            print("  Throughput: NEEDS IMPROVEMENT (<20 RPS)")

async def test_gcp_api_health(api_url: str) -> bool:
    """Test if GCP API is accessible"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(f"{api_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"API Health Check: SUCCESS")
                    print(f"  Status: {data.get('status', 'unknown')}")
                    print(f"  Model Loaded: {data.get('model_loaded', 'unknown')}")
                    print(f"  Version: {data.get('version', 'unknown')}")
                    return True
                else:
                    print(f"API Health Check: FAILED (Status: {response.status})")
                    return False
    except Exception as e:
        print(f"API Health Check: ERROR - {e}")
        return False

async def detect_api_type(api_url: str) -> str:
    """Detect if API is basic or enhanced"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{api_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    if "version" in data and data.get("version") == "2.0.0":
                        return "enhanced"
                    elif "features" in data:
                        return "enhanced"
        return "basic"
    except:
        return "basic"

async def test_batch_processing(api_url: str):
    """Test batch processing if available"""
    print(f"\nTesting Batch Processing:")
    
    # Detect API type
    api_type = await detect_api_type(api_url)
    
    # Create base feature data
    features_data = [
        {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
        {"sepal_length": 6.2, "sepal_width": 3.4, "petal_length": 5.4, "petal_width": 2.3},
        {"sepal_length": 5.9, "sepal_width": 3.0, "petal_length": 5.1, "petal_width": 1.8}
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
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            start_time = time.time()
            async with session.post(f"{api_url}/predict_batch", json=batch_data) as response:
                end_time = time.time()
                
                if response.status == 200:
                    data = await response.json()
                    print(f"  Batch Processing: SUCCESS")
                    
                    # Handle different response formats
                    if api_type == "enhanced":
                        batch_size = len(batch_data["features_list"])
                        if isinstance(data, dict) and "predictions" in data:
                            predictions_count = len(data["predictions"])
                            print(f"  API Type: Enhanced (v2.0.0)")
                            print(f"  Batch ID: {data.get('batch_id', 'N/A')}")
                        else:
                            predictions_count = len(data) if isinstance(data, list) else 0
                    else:
                        batch_size = len(batch_data)
                        predictions_count = len(data) if isinstance(data, list) else 0
                        print(f"  API Type: Basic (v1.0.0)")
                    
                    print(f"  Batch Size: {batch_size}")
                    print(f"  Response Time: {(end_time - start_time)*1000:.1f}ms")
                    print(f"  Predictions Returned: {predictions_count}")
                    return True
                else:
                    print(f"  Batch Processing: FAILED (Status: {response.status})")
                    return False
    except Exception as e:
        print(f"  Batch Processing: ERROR - {e}")
        return False

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="GCP Concurrent Scaling Test")
    parser.add_argument("--url", required=True, help="GCP API URL")
    parser.add_argument("--light-test", action="store_true", help="Run light tests only (for CI)")
    
    args = parser.parse_args()
    
    api_url = args.url.rstrip('/')
    
    print("GCP Concurrent Scaling Test")
    print("=" * 40)
    print(f"API URL: {api_url}")
    print(f"Light test mode: {args.light_test}")
    print()
    
    # Test API health first
    try:
        if not await test_gcp_api_health(api_url):
            print("API health check failed. Exiting.")
            sys.exit(1)
    except Exception as e:
        print(f"Error during API health check: {e}")
        sys.exit(1)
    
    # Test batch processing
    await test_batch_processing(api_url)
    
    # Initialize tester
    tester = GCPConcurrentTester(api_url)
    
    # Define test configurations
    if args.light_test:
        # Light tests for CI environment
        test_configs = [
            {"name": "Light Load", "users": 25, "requests": 2},
            {"name": "Moderate Load", "users": 50, "requests": 1}
        ]
    else:
        # Full test suite
        test_configs = [
            {"name": "Light Load", "users": 25, "requests": 4},
            {"name": "Moderate Load", "users": 50, "requests": 2},
            {"name": "Heavy Load", "users": 100, "requests": 1}
        ]
    
    print(f"\nRunning Concurrent Load Tests:")
    print("=" * 40)
    
    # Run tests
    for config in test_configs:
        await tester.run_concurrent_test(
            config["name"], 
            config["users"], 
            config["requests"]
        )
        
        # Small delay between tests
        await asyncio.sleep(2)
    
    # Print summary
    tester.print_summary()
    
    print(f"\nGCP Concurrent Scaling Test Completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)