#!/usr/bin/env python3

"""
Concurrent Load Testing Script for Iris ML Model API
Tests concurrent inference performance and identifies bottlenecks
"""

import asyncio
import aiohttp
import time
import statistics
import json
import argparse
from typing import List, Dict, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import psutil
import sys

@dataclass
class LoadTestResult:
    """Results from a single request"""
    success: bool
    response_time: float
    status_code: int
    error_message: str = ""
    timestamp: float = 0.0

@dataclass
class LoadTestSummary:
    """Summary of load test results"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    errors: Dict[str, int]

class ConcurrentLoadTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.results: List[LoadTestResult] = []
        self.system_metrics = []
        
    async def make_request(self, session: aiohttp.ClientSession, endpoint: str, data: Dict = None) -> LoadTestResult:
        """Make a single async request"""
        start_time = time.time()
        
        try:
            if data:
                async with session.post(f"{self.base_url}{endpoint}", json=data) as response:
                    await response.text()  # Consume response
                    end_time = time.time()
                    return LoadTestResult(
                        success=response.status == 200,
                        response_time=end_time - start_time,
                        status_code=response.status,
                        timestamp=start_time
                    )
            else:
                async with session.get(f"{self.base_url}{endpoint}") as response:
                    await response.text()  # Consume response
                    end_time = time.time()
                    return LoadTestResult(
                        success=response.status == 200,
                        response_time=end_time - start_time,
                        status_code=response.status,
                        timestamp=start_time
                    )
                    
        except Exception as e:
            end_time = time.time()
            return LoadTestResult(
                success=False,
                response_time=end_time - start_time,
                status_code=0,
                error_message=str(e),
                timestamp=start_time
            )
    
    def monitor_system_resources(self, duration: float, interval: float = 0.5):
        """Monitor system resources during load test"""
        start_time = time.time()
        
        while time.time() - start_time < duration:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            self.system_metrics.append({
                'timestamp': time.time(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_available_gb': memory.available / (1024**3)
            })
            
            time.sleep(interval)
    
    async def run_concurrent_test(self, 
                                 endpoint: str,
                                 concurrent_users: int,
                                 requests_per_user: int,
                                 test_data: Dict = None) -> List[LoadTestResult]:
        """Run concurrent load test"""
        
        print(f"Starting concurrent test:")
        print(f"   Endpoint: {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Requests per user: {requests_per_user}")
        print(f"   Total requests: {concurrent_users * requests_per_user}")
        
        # Start system monitoring in background
        monitor_thread = threading.Thread(
            target=self.monitor_system_resources,
            args=(requests_per_user * 2,)  # Monitor for expected duration
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Configure connection limits
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,  # Total connection pool size
            limit_per_host=concurrent_users * 2,  # Per-host connection limit
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30)  # 30 second timeout
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        ) as session:
            
            # Create all tasks
            tasks = []
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    task = self.make_request(session, endpoint, test_data)
                    tasks.append(task)
            
            # Execute all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(LoadTestResult(
                        success=False,
                        response_time=0.0,
                        status_code=0,
                        error_message=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            print(f"Test completed in {end_time - start_time:.2f} seconds")
            return processed_results
    
    def analyze_results(self, results: List[LoadTestResult]) -> LoadTestSummary:
        """Analyze load test results"""
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        if not successful_results:
            return LoadTestSummary(
                total_requests=len(results),
                successful_requests=0,
                failed_requests=len(failed_results),
                avg_response_time=0.0,
                min_response_time=0.0,
                max_response_time=0.0,
                p95_response_time=0.0,
                p99_response_time=0.0,
                requests_per_second=0.0,
                error_rate=100.0,
                errors={}
            )
        
        response_times = [r.response_time for r in successful_results]
        
        # Calculate percentiles
        response_times_sorted = sorted(response_times)
        p95_index = int(0.95 * len(response_times_sorted))
        p99_index = int(0.99 * len(response_times_sorted))
        
        # Calculate RPS based on actual test duration
        if successful_results:
            timestamps = [r.timestamp for r in successful_results if r.timestamp > 0]
            if len(timestamps) > 1:
                test_duration = max(timestamps) - min(timestamps)
                requests_per_second = len(successful_results) / max(test_duration, 0.001)
            else:
                requests_per_second = 0.0
        else:
            requests_per_second = 0.0
        
        # Count error types
        error_counts = {}
        for result in failed_results:
            if result.status_code > 0:
                key = f"HTTP_{result.status_code}"
            else:
                key = "Connection_Error"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        return LoadTestSummary(
            total_requests=len(results),
            successful_requests=len(successful_results),
            failed_requests=len(failed_results),
            avg_response_time=statistics.mean(response_times),
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            p95_response_time=response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else 0,
            p99_response_time=response_times_sorted[p99_index] if p99_index < len(response_times_sorted) else 0,
            requests_per_second=requests_per_second,
            error_rate=(len(failed_results) / len(results)) * 100,
            errors=error_counts
        )
    
    def print_summary(self, summary: LoadTestSummary):
        """Print test summary"""
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        
        print(f"Request Statistics:")
        print(f"   Total Requests: {summary.total_requests}")
        print(f"   Successful: {summary.successful_requests}")
        print(f"   Failed: {summary.failed_requests}")
        print(f"   Success Rate: {100 - summary.error_rate:.1f}%")
        
        print(f"\nResponse Time Statistics:")
        print(f"   Average: {summary.avg_response_time*1000:.1f}ms")
        print(f"   Minimum: {summary.min_response_time*1000:.1f}ms")
        print(f"   Maximum: {summary.max_response_time*1000:.1f}ms")
        print(f"   95th Percentile: {summary.p95_response_time*1000:.1f}ms")
        print(f"   99th Percentile: {summary.p99_response_time*1000:.1f}ms")
        
        print(f"\nThroughput:")
        print(f"   Requests/Second: {summary.requests_per_second:.1f}")
        
        if summary.errors:
            print(f"\nError Breakdown:")
            for error_type, count in summary.errors.items():
                print(f"   {error_type}: {count}")
        
        if self.system_metrics:
            cpu_values = [m['cpu_percent'] for m in self.system_metrics]
            memory_values = [m['memory_percent'] for m in self.system_metrics]
            
            print(f"\nSystem Resource Usage:")
            print(f"   CPU - Avg: {statistics.mean(cpu_values):.1f}%, Max: {max(cpu_values):.1f}%")
            print(f"   Memory - Avg: {statistics.mean(memory_values):.1f}%, Max: {max(memory_values):.1f}%")
    
    def identify_bottlenecks(self, summary: LoadTestSummary):
        """Identify potential bottlenecks"""
        print(f"\nBOTTLENECK ANALYSIS")
        print("="*60)
        
        bottlenecks = []
        
        if summary.error_rate > 5:
            bottlenecks.append(f"High error rate ({summary.error_rate:.1f}%) - Check server capacity")
        
        if summary.avg_response_time > 1.0:
            bottlenecks.append(f"Slow average response time ({summary.avg_response_time*1000:.0f}ms) - Optimize model inference")
        
        if summary.p99_response_time > 2.0:
            bottlenecks.append(f"High P99 latency ({summary.p99_response_time*1000:.0f}ms) - Check for resource contention")
        
        if summary.requests_per_second < 10:
            bottlenecks.append(f"Low throughput ({summary.requests_per_second:.1f} RPS) - Consider scaling or optimization")
        
        if self.system_metrics:
            cpu_values = [m['cpu_percent'] for m in self.system_metrics]
            memory_values = [m['memory_percent'] for m in self.system_metrics]
            
            if max(cpu_values) > 90:
                bottlenecks.append(f"High CPU usage ({max(cpu_values):.1f}%) - CPU bound")
            
            if max(memory_values) > 90:
                bottlenecks.append(f"High memory usage ({max(memory_values):.1f}%) - Memory bound")
        
        if bottlenecks:
            for bottleneck in bottlenecks:
                print(f"   {bottleneck}")
        else:
            print("   No significant bottlenecks detected")
        
        print(f"\nRECOMMENDATIONS:")
        if summary.error_rate > 5:
            print("   - Increase server worker processes/threads")
            print("   - Add connection pooling")
            print("   - Implement request queuing")
        
        if summary.avg_response_time > 0.5:
            print("   - Optimize model inference code")
            print("   - Consider model quantization")
            print("   - Add response caching for repeated requests")
        
        if summary.requests_per_second < 50:
            print("   - Use async/await for I/O operations")
            print("   - Implement batch processing")
            print("   - Consider horizontal scaling")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Concurrent load test for Iris API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument("--endpoint", default="/predict", help="Endpoint to test")
    
    args = parser.parse_args()
    
    # Test data for predictions
    test_data = {
        "sepal_length": 5.1,
        "sepal_width": 3.5,
        "petal_length": 1.4,
        "petal_width": 0.2
    }
    
    tester = ConcurrentLoadTester(args.url)
    
    # Run the load test
    results = await tester.run_concurrent_test(
        endpoint=args.endpoint,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        test_data=test_data if args.endpoint == "/predict" else None
    )
    
    # Analyze and display results
    summary = tester.analyze_results(results)
    tester.print_summary(summary)
    tester.identify_bottlenecks(summary)
    
    # Return exit code based on success rate
    return 0 if summary.error_rate < 5 else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        sys.exit(1)