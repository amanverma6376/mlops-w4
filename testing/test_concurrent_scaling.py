#!/usr/bin/env python3

"""
Comprehensive Concurrent Scaling Test Suite
Tests various concurrency scenarios and identifies bottlenecks
"""

import asyncio
import subprocess
import time
import sys
import os
from concurrent_load_test import ConcurrentLoadTester


class ConcurrentScalingTestSuite:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.test_results = []

    async def run_scaling_test(self, test_name: str, users: int, requests_per_user: int):
        """Run a single scaling test"""
        print(f"\n{'='*60}")
        print(f"Running Test: {test_name}")
        print(f"   Users: {users}, Requests per user: {requests_per_user}")
        print(f"{'='*60}")

        tester = ConcurrentLoadTester(self.api_url)

        # Test data
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }

        # Run the test
        results = await tester.run_concurrent_test(
            endpoint="/predict",
            concurrent_users=users,
            requests_per_user=requests_per_user,
            test_data=test_data
        )

        # Analyze results
        summary = tester.analyze_results(results)
        tester.print_summary(summary)
        tester.identify_bottlenecks(summary)

        # Store results for comparison
        self.test_results.append({
            'test_name': test_name,
            'users': users,
            'requests_per_user': requests_per_user,
            'total_requests': summary.total_requests,
            'success_rate': 100 - summary.error_rate,
            'avg_response_time': summary.avg_response_time,
            'requests_per_second': summary.requests_per_second,
            'p95_response_time': summary.p95_response_time
        })

        return summary

    async def run_batch_vs_single_comparison(self):
        """Compare batch vs single request performance"""
        print(f"\n{'='*60}")
        print(f"Batch vs Single Request Comparison")
        print(f"{'='*60}")

        tester = ConcurrentLoadTester(self.api_url)

        # Test data for batch
        batch_data = {
            "features_list": [
                {"sepal_length": 5.1, "sepal_width": 3.5,
                    "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.2, "sepal_width": 3.4,
                    "petal_length": 5.4, "petal_width": 2.3},
                {"sepal_length": 5.9, "sepal_width": 3.0,
                    "petal_length": 5.1, "petal_width": 1.8},
                {"sepal_length": 5.0, "sepal_width": 3.6,
                    "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 7.0, "sepal_width": 3.2,
                    "petal_length": 4.7, "petal_width": 1.4}
            ]
        }

        # Test single requests
        print("\nTesting Single Requests (5 concurrent users, 10 requests each):")
        single_results = await tester.run_concurrent_test(
            endpoint="/predict",
            concurrent_users=5,
            requests_per_user=10,
            test_data={"sepal_length": 5.1, "sepal_width": 3.5,
                       "petal_length": 1.4, "petal_width": 0.2}
        )
        single_summary = tester.analyze_results(single_results)

        # Test batch requests
        print("\nTesting Batch Requests (10 concurrent users, 10 batches each):")
        batch_results = await tester.run_concurrent_test(
            endpoint="/predict_batch",
            concurrent_users=10,
            requests_per_user=10,
            test_data=batch_data
        )
        batch_summary = tester.analyze_results(batch_results)

        # Compare results
        print(f"\nComparison Results:")
        print(f"   Single Requests:")
        print(f"     Total Predictions: {single_summary.total_requests}")
        print(
            f"     Avg Response Time: {single_summary.avg_response_time*1000:.1f}ms")
        print(f"     Throughput: {single_summary.requests_per_second:.1f} RPS")

        print(f"   Batch Requests:")
        print(f"     Total Batches: {batch_summary.total_requests}")
        print(f"     Total Predictions: {batch_summary.total_requests * 5}")
        print(
            f"     Avg Response Time: {batch_summary.avg_response_time*1000:.1f}ms")
        print(
            f"     Batch Throughput: {batch_summary.requests_per_second:.1f} batches/sec")
        print(
            f"     Prediction Throughput: {batch_summary.requests_per_second * 5:.1f} predictions/sec")

        batch_efficiency = (batch_summary.requests_per_second *
                            5) / single_summary.requests_per_second
        print(f"\nBatch Processing Efficiency: {batch_efficiency:.2f}x faster")

    async def run_progressive_load_test(self):
        """Run progressive load test to find breaking point"""
        print(f"\n{'='*60}")
        print(f"Progressive Load Test - Finding Breaking Point")
        print(f"{'='*60}")

        load_levels = [
            (1, 10),    # Light load
            (5, 10),    # Moderate load
            (10, 10),   # Heavy load
            (20, 10),   # Very heavy load
            (50, 5),    # Extreme load
            (100, 2),   # Breaking point test
        ]

        breaking_point_found = False

        for users, requests_per_user in load_levels:
            if breaking_point_found:
                break

            summary = await self.run_scaling_test(
                f"Progressive Load - {users} users",
                users,
                requests_per_user
            )

            # Check if we've hit a breaking point
            if summary.error_rate > 10 or summary.avg_response_time > 5.0:
                print(f"\nBreaking point detected at {users} concurrent users")
                breaking_point_found = True

            print("Waiting 5 seconds for system recovery...")
            await asyncio.sleep(5)

    def print_final_comparison(self):
        """Print final comparison of all tests"""
        if not self.test_results:
            return

        print(f"\n{'='*80}")
        print(f"FINAL PERFORMANCE COMPARISON")
        print(f"{'='*80}")

        print(f"{'Test Name':<30} {'Users':<6} {'Success%':<8} {'Avg RT(ms)':<10} {'RPS':<8} {'P95(ms)':<8}")
        print(f"{'-'*80}")

        for result in self.test_results:
            print(f"{result['test_name']:<30} "
                  f"{result['users']:<6} "
                  f"{result['success_rate']:<8.1f} "
                  f"{result['avg_response_time']*1000:<10.1f} "
                  f"{result['requests_per_second']:<8.1f} "
                  f"{result['p95_response_time']*1000:<8.1f}")

        best_rps = max(self.test_results,
                       key=lambda x: x['requests_per_second'])
        best_latency = min(self.test_results,
                           key=lambda x: x['avg_response_time'])

        print(f"\nPerformance Highlights:")
        print(
            f"   Best Throughput: {best_rps['test_name']} - {best_rps['requests_per_second']:.1f} RPS")
        print(
            f"   Best Latency: {best_latency['test_name']} - {best_latency['avg_response_time']*1000:.1f}ms")


async def main():
    """Main test suite execution"""
    print("Starting Concurrent Scaling Test Suite")
    print("="*60)

    import requests
    api_url = "http://localhost:8000"

    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print("Error: API is not responding properly. Please start the API first.")
            sys.exit(1)
    except Exception as e:
        print(
            f"Error: Cannot connect to API at {api_url}. Please start the API first.")
        print(f"   Error: {e}")
        sys.exit(1)

    print("API is running and accessible")

    # Initialize test suite
    test_suite = ConcurrentScalingTestSuite(api_url)

    try:
        # Run basic scaling tests
        await test_suite.run_scaling_test("Baseline - Light Load", 1, 10)
        await asyncio.sleep(2)

        await test_suite.run_scaling_test("Moderate Load", 5, 10)
        await asyncio.sleep(2)

        await test_suite.run_scaling_test("Heavy Load", 10, 10)
        await asyncio.sleep(2)

        await test_suite.run_scaling_test("Very Heavy Load", 20, 5)
        await asyncio.sleep(2)

        # Run batch vs single comparison
        await test_suite.run_batch_vs_single_comparison()
        await asyncio.sleep(2)

        # Run progressive load test
        await test_suite.run_progressive_load_test()

        # Print final comparison
        test_suite.print_final_comparison()

        print(f"\nConcurrent Scaling Test Suite Completed")
        print(f"\nNext Steps:")
        print(f"   1. Analyze the results above to identify bottlenecks")
        print(f"   2. Run 'python performance_monitor.py' for real-time monitoring")
        print(f"   3. Consider optimizations based on the identified issues")
        print(f"   4. Test with the enhanced API (iris_api_enhanced.py) for better performance")

    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
    except Exception as e:
        print(f"\nTest suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
