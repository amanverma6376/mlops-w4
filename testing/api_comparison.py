#!/usr/bin/env python3

"""
API Comparison Script
Compares performance between basic iris_api.py and enhanced iris_api_enhanced.py
"""

import asyncio
import aiohttp
import time
import statistics
import subprocess
import sys
import os
import signal
import requests
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class APITestResult:
    api_name: str
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    success_rate: float
    concurrent_users: int
    total_requests: int
    errors: int

class APIComparison:
    def __init__(self):
        self.results = []
        self.api_processes = {}
        
    def start_api(self, api_file: str, port: int) -> int:
        """Start an API server and return the process ID"""
        try:
            # Start the API server
            process = subprocess.Popen([
                sys.executable, api_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for API to start
            api_url = f"http://localhost:{port}"
            for _ in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f"{api_url}/health", timeout=1)
                    if response.status_code == 200:
                        print(f"API {api_file} started successfully on port {port}")
                        return process.pid
                except:
                    time.sleep(1)
            
            # If we get here, API didn't start
            process.terminate()
            return None
            
        except Exception as e:
            print(f"Error starting API {api_file}: {e}")
            return None
    
    def stop_api(self, pid: int):
        """Stop an API server"""
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)  # Give it time to shut down gracefully
        except:
            try:
                os.kill(pid, signal.SIGKILL)
            except:
                pass
    
    async def test_api_performance(self, api_url: str, concurrent_users: int, requests_per_user: int) -> Dict:
        """Test API performance with concurrent requests"""
        
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        async def make_request(session):
            start_time = time.time()
            try:
                async with session.post(f"{api_url}/predict", json=test_data) as response:
                    await response.text()
                    end_time = time.time()
                    return {
                        'success': response.status == 200,
                        'response_time': end_time - start_time,
                        'status_code': response.status
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'response_time': end_time - start_time,
                    'status_code': 0,
                    'error': str(e)
                }
        
        # Configure connection limits
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,
            limit_per_host=concurrent_users * 2
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create all tasks
            tasks = []
            for _ in range(concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(make_request(session))
            
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
                p99_index = int(0.99 * len(response_times_sorted))
                
                total_time = end_time - start_time
                rps = len(successful_results) / total_time if total_time > 0 else 0
                
                return {
                    'avg_response_time': statistics.mean(response_times),
                    'p95_response_time': response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else 0,
                    'p99_response_time': response_times_sorted[p99_index] if p99_index < len(response_times_sorted) else 0,
                    'requests_per_second': rps,
                    'success_rate': len(successful_results) / len(results) * 100,
                    'total_requests': len(results),
                    'successful_requests': len(successful_results),
                    'failed_requests': len(failed_results)
                }
            else:
                return {
                    'avg_response_time': 0,
                    'p95_response_time': 0,
                    'p99_response_time': 0,
                    'requests_per_second': 0,
                    'success_rate': 0,
                    'total_requests': len(results),
                    'successful_requests': 0,
                    'failed_requests': len(failed_results)
                }
    
    async def run_comparison(self):
        """Run comparison between basic and enhanced APIs"""
        
        print("API Performance Comparison")
        print("=" * 60)
        
        # Test configurations
        test_configs = [
            {"users": 5, "requests": 10, "name": "Light Load"},
            {"users": 10, "requests": 10, "name": "Moderate Load"},
            {"users": 20, "requests": 5, "name": "Heavy Load"}
        ]
        
        apis_to_test = [
            {"file": "iris_api.py", "name": "Basic API", "port": 8000},
            {"file": "iris_api_enhanced.py", "name": "Enhanced API", "port": 8000}
        ]
        
        comparison_results = []
        
        for api in apis_to_test:
            print(f"\nTesting {api['name']} ({api['file']})")
            print("-" * 40)
            
            # Check if API file exists
            if not os.path.exists(api['file']):
                print(f"Error: {api['file']} not found")
                continue
            
            # Start API
            pid = self.start_api(api['file'], api['port'])
            if not pid:
                print(f"Failed to start {api['name']}")
                continue
            
            api_results = []
            
            try:
                for config in test_configs:
                    print(f"  Running {config['name']} test ({config['users']} users, {config['requests']} requests each)...")
                    
                    # Run the test
                    result = await self.test_api_performance(
                        f"http://localhost:{api['port']}", 
                        config['users'], 
                        config['requests']
                    )
                    
                    test_result = APITestResult(
                        api_name=api['name'],
                        avg_response_time=result['avg_response_time'],
                        p95_response_time=result['p95_response_time'],
                        p99_response_time=result['p99_response_time'],
                        requests_per_second=result['requests_per_second'],
                        success_rate=result['success_rate'],
                        concurrent_users=config['users'],
                        total_requests=result['total_requests'],
                        errors=result['failed_requests']
                    )
                    
                    api_results.append(test_result)
                    
                    print(f"    Success Rate: {result['success_rate']:.1f}%")
                    print(f"    Avg Response Time: {result['avg_response_time']*1000:.1f}ms")
                    print(f"    Requests/Second: {result['requests_per_second']:.1f}")
                    
                    # Small delay between tests
                    await asyncio.sleep(2)
                
                comparison_results.extend(api_results)
                
            finally:
                # Stop API
                self.stop_api(pid)
                print(f"  Stopped {api['name']}")
                
                # Wait a bit before starting next API
                await asyncio.sleep(3)
        
        # Generate comparison table
        self.generate_comparison_table(comparison_results)
    
    def generate_comparison_table(self, results: List[APITestResult]):
        """Generate a comparison table showing the differences"""
        
        print(f"\n{'='*80}")
        print("PERFORMANCE COMPARISON RESULTS")
        print(f"{'='*80}")
        
        # Group results by test configuration
        basic_results = [r for r in results if "Basic" in r.api_name]
        enhanced_results = [r for r in results if "Enhanced" in r.api_name]
        
        if not basic_results or not enhanced_results:
            print("Error: Could not get results from both APIs for comparison")
            return
        
        print(f"\n{'Metric':<25} {'Basic API':<15} {'Enhanced API':<15} {'Improvement':<15} {'% Change':<10}")
        print("-" * 80)
        
        # Compare each test configuration
        test_names = ["Light Load", "Moderate Load", "Heavy Load"]
        
        for i, test_name in enumerate(test_names):
            if i < len(basic_results) and i < len(enhanced_results):
                basic = basic_results[i]
                enhanced = enhanced_results[i]
                
                print(f"\n{test_name} ({basic.concurrent_users} users):")
                
                # Response Time Comparison
                basic_rt = basic.avg_response_time * 1000
                enhanced_rt = enhanced.avg_response_time * 1000
                rt_improvement = basic_rt - enhanced_rt
                rt_change = ((enhanced_rt - basic_rt) / basic_rt * 100) if basic_rt > 0 else 0
                
                print(f"{'Avg Response Time (ms)':<25} {basic_rt:<15.1f} {enhanced_rt:<15.1f} {rt_improvement:<15.1f} {rt_change:<10.1f}%")
                
                # Throughput Comparison
                rps_improvement = enhanced.requests_per_second - basic.requests_per_second
                rps_change = ((enhanced.requests_per_second - basic.requests_per_second) / basic.requests_per_second * 100) if basic.requests_per_second > 0 else 0
                
                print(f"{'Requests/Second':<25} {basic.requests_per_second:<15.1f} {enhanced.requests_per_second:<15.1f} {rps_improvement:<15.1f} {rps_change:<10.1f}%")
                
                # Success Rate Comparison
                success_improvement = enhanced.success_rate - basic.success_rate
                success_change = ((enhanced.success_rate - basic.success_rate) / basic.success_rate * 100) if basic.success_rate > 0 else 0
                
                print(f"{'Success Rate (%)':<25} {basic.success_rate:<15.1f} {enhanced.success_rate:<15.1f} {success_improvement:<15.1f} {success_change:<10.1f}%")
                
                # P95 Response Time
                basic_p95 = basic.p95_response_time * 1000
                enhanced_p95 = enhanced.p95_response_time * 1000
                p95_improvement = basic_p95 - enhanced_p95
                p95_change = ((enhanced_p95 - basic_p95) / basic_p95 * 100) if basic_p95 > 0 else 0
                
                print(f"{'P95 Response Time (ms)':<25} {basic_p95:<15.1f} {enhanced_p95:<15.1f} {p95_improvement:<15.1f} {p95_change:<10.1f}%")
        
        # Overall Summary
        print(f"\n{'='*80}")
        print("OVERALL PERFORMANCE SUMMARY")
        print(f"{'='*80}")
        
        # Calculate averages
        basic_avg_rt = statistics.mean([r.avg_response_time * 1000 for r in basic_results])
        enhanced_avg_rt = statistics.mean([r.avg_response_time * 1000 for r in enhanced_results])
        
        basic_avg_rps = statistics.mean([r.requests_per_second for r in basic_results])
        enhanced_avg_rps = statistics.mean([r.requests_per_second for r in enhanced_results])
        
        basic_avg_success = statistics.mean([r.success_rate for r in basic_results])
        enhanced_avg_success = statistics.mean([r.success_rate for r in enhanced_results])
        
        print(f"Average Response Time:")
        print(f"  Basic API: {basic_avg_rt:.1f}ms")
        print(f"  Enhanced API: {enhanced_avg_rt:.1f}ms")
        print(f"  Improvement: {basic_avg_rt - enhanced_avg_rt:.1f}ms ({((enhanced_avg_rt - basic_avg_rt) / basic_avg_rt * 100):.1f}%)")
        
        print(f"\nAverage Throughput:")
        print(f"  Basic API: {basic_avg_rps:.1f} RPS")
        print(f"  Enhanced API: {enhanced_avg_rps:.1f} RPS")
        print(f"  Improvement: {enhanced_avg_rps - basic_avg_rps:.1f} RPS ({((enhanced_avg_rps - basic_avg_rps) / basic_avg_rps * 100):.1f}%)")
        
        print(f"\nAverage Success Rate:")
        print(f"  Basic API: {basic_avg_success:.1f}%")
        print(f"  Enhanced API: {enhanced_avg_success:.1f}%")
        print(f"  Improvement: {enhanced_avg_success - basic_avg_success:.1f}% ({((enhanced_avg_success - basic_avg_success) / basic_avg_success * 100):.1f}%)")
        
        # Key Improvements
        print(f"\nKEY IMPROVEMENTS IN ENHANCED API:")
        
        if enhanced_avg_rt < basic_avg_rt:
            print(f"  - {((basic_avg_rt - enhanced_avg_rt) / basic_avg_rt * 100):.1f}% faster response times")
        
        if enhanced_avg_rps > basic_avg_rps:
            print(f"  - {((enhanced_avg_rps - basic_avg_rps) / basic_avg_rps * 100):.1f}% higher throughput")
        
        if enhanced_avg_success > basic_avg_success:
            print(f"  - {enhanced_avg_success - basic_avg_success:.1f}% better success rate")
        
        print(f"  - Async request handling")
        print(f"  - Thread pool for CPU-bound tasks")
        print(f"  - Better connection management")
        print(f"  - Enhanced error handling")

async def main():
    """Main function"""
    comparison = APIComparison()
    await comparison.run_comparison()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nComparison interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Comparison failed: {e}")
        sys.exit(1)