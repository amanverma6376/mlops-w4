#!/usr/bin/env python3

"""
GCP API Comparison Script
Compares deployed API performance on GCP infrastructure
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
class GCPAPIResult:
    api_type: str
    test_name: str
    concurrent_users: int
    avg_response_time: float
    p95_response_time: float
    requests_per_second: float
    success_rate: float
    total_requests: int

class GCPAPIComparison:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.results = []
        
    async def test_api_capabilities(self) -> Dict:
        """Test what capabilities the deployed API has"""
        capabilities = {
            'basic_predict': False,
            'batch_predict': False,
            'concurrent_predict': False,
            'enhanced_features': False
        }
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                # Test basic predict
                test_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
                async with session.post(f"{self.api_url}/predict", json=test_data) as response:
                    if response.status == 200:
                        capabilities['basic_predict'] = True
                
                # Test batch predict
                batch_data = {"features_list": [test_data, test_data]}
                try:
                    async with session.post(f"{self.api_url}/predict_batch", json=batch_data) as response:
                        if response.status == 200:
                            capabilities['batch_predict'] = True
                except:
                    pass
                
                # Test concurrent predict (enhanced API feature)
                try:
                    async with session.post(f"{self.api_url}/predict_concurrent", json=[test_data, test_data]) as response:
                        if response.status == 200:
                            capabilities['concurrent_predict'] = True
                            capabilities['enhanced_features'] = True
                except:
                    pass
                
                # Test stats endpoint (enhanced API feature)
                try:
                    async with session.get(f"{self.api_url}/stats") as response:
                        if response.status == 200:
                            capabilities['enhanced_features'] = True
                except:
                    pass
                    
        except Exception as e:
            print(f"Error testing API capabilities: {e}")
        
        return capabilities
    
    async def run_performance_test(self, test_name: str, concurrent_users: int, requests_per_user: int) -> GCPAPIResult:
        """Run performance test on the deployed API"""
        
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        async def make_request(session):
            start_time = time.time()
            try:
                async with session.post(f"{self.api_url}/predict", json=test_data, timeout=aiohttp.ClientTimeout(total=30)) as response:
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
        
        connector = aiohttp.TCPConnector(
            limit=concurrent_users * 2,
            limit_per_host=concurrent_users * 2
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for _ in range(concurrent_users):
                for _ in range(requests_per_user):
                    tasks.append(make_request(session))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_results = []
            failed_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append({'error': str(result)})
                elif result['success']:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            
            if successful_results:
                response_times = [r['response_time'] for r in successful_results]
                response_times_sorted = sorted(response_times)
                
                p95_index = int(0.95 * len(response_times_sorted))
                total_time = end_time - start_time
                rps = len(successful_results) / total_time if total_time > 0 else 0
                
                return GCPAPIResult(
                    api_type="Deployed API",
                    test_name=test_name,
                    concurrent_users=concurrent_users,
                    avg_response_time=statistics.mean(response_times),
                    p95_response_time=response_times_sorted[p95_index] if p95_index < len(response_times_sorted) else 0,
                    requests_per_second=rps,
                    success_rate=len(successful_results) / len(results) * 100,
                    total_requests=len(results)
                )
            else:
                return None
    
    async def test_batch_efficiency(self) -> Dict:
        """Test batch processing efficiency"""
        print("Testing batch processing efficiency...")
        
        # Test single requests
        single_times = []
        test_data = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        
        async with aiohttp.ClientSession() as session:
            for _ in range(10):
                start_time = time.time()
                try:
                    async with session.post(f"{self.api_url}/predict", json=test_data) as response:
                        if response.status == 200:
                            end_time = time.time()
                            single_times.append(end_time - start_time)
                except:
                    pass
        
        # Test batch requests
        batch_times = []
        batch_data = {"features_list": [test_data] * 10}
        
        async with aiohttp.ClientSession() as session:
            for _ in range(5):
                start_time = time.time()
                try:
                    async with session.post(f"{self.api_url}/predict_batch", json=batch_data) as response:
                        if response.status == 200:
                            end_time = time.time()
                            batch_times.append((end_time - start_time) / 10)  # Per item time
                except:
                    pass
        
        return {
            'single_avg_time': statistics.mean(single_times) if single_times else 0,
            'batch_avg_time': statistics.mean(batch_times) if batch_times else 0,
            'batch_efficiency': statistics.mean(single_times) / statistics.mean(batch_times) if single_times and batch_times else 0
        }
    
    def generate_report(self, capabilities: Dict, batch_results: Dict):
        """Generate comprehensive performance report"""
        
        print(f"\nGCP API PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        # API Type Detection
        if capabilities['enhanced_features']:
            api_type = "Enhanced API (iris_api_enhanced.py)"
            print(f"Detected API Type: {api_type}")
            print("Features: Async processing, thread pools, enhanced endpoints")
        else:
            api_type = "Basic API (iris_api.py)"
            print(f"Detected API Type: {api_type}")
            print("Features: Synchronous processing, basic endpoints")
        
        print(f"\nAPI Capabilities:")
        print(f"  Basic Prediction: {'✓' if capabilities['basic_predict'] else '✗'}")
        print(f"  Batch Processing: {'✓' if capabilities['batch_predict'] else '✗'}")
        print(f"  Concurrent Processing: {'✓' if capabilities['concurrent_predict'] else '✗'}")
        print(f"  Enhanced Features: {'✓' if capabilities['enhanced_features'] else '✗'}")
        
        # Performance Results
        if self.results:
            print(f"\nPerformance Test Results:")
            print(f"{'Test Name':<15} {'Users':<6} {'Success%':<8} {'Avg RT(ms)':<10} {'P95(ms)':<8} {'RPS':<8}")
            print("-" * 65)
            
            for result in self.results:
                print(f"{result.test_name:<15} "
                      f"{result.concurrent_users:<6} "
                      f"{result.success_rate:<8.1f} "
                      f"{result.avg_response_time*1000:<10.1f} "
                      f"{result.p95_response_time*1000:<8.1f} "
                      f"{result.requests_per_second:<8.1f}")
            
            # Calculate averages
            avg_success = statistics.mean([r.success_rate for r in self.results])
            avg_response_time = statistics.mean([r.avg_response_time for r in self.results])
            avg_rps = statistics.mean([r.requests_per_second for r in self.results])
            
            print(f"\nOverall Performance:")
            print(f"  Average Success Rate: {avg_success:.1f}%")
            print(f"  Average Response Time: {avg_response_time*1000:.1f}ms")
            print(f"  Average Throughput: {avg_rps:.1f} RPS")
        
        # Batch Processing Results
        if batch_results['batch_efficiency'] > 0:
            print(f"\nBatch Processing Efficiency:")
            print(f"  Single Request Avg Time: {batch_results['single_avg_time']*1000:.1f}ms")
            print(f"  Batch Request Avg Time (per item): {batch_results['batch_avg_time']*1000:.1f}ms")
            print(f"  Batch Efficiency Gain: {batch_results['batch_efficiency']:.1f}x faster")
        
        # Performance Assessment
        print(f"\nPerformance Assessment for GCP Deployment:")
        
        if capabilities['enhanced_features']:
            print("  Architecture: PRODUCTION-READY")
            print("    - Async request handling")
            print("    - Thread pool execution")
            print("    - Enhanced error handling")
            print("    - Built-in monitoring")
        else:
            print("  Architecture: BASIC")
            print("    - Synchronous processing")
            print("    - Limited concurrency")
            print("    - Basic error handling")
        
        if self.results:
            if avg_success >= 95:
                print("  Reliability: EXCELLENT")
            elif avg_success >= 90:
                print("  Reliability: GOOD")
            else:
                print("  Reliability: NEEDS IMPROVEMENT")
            
            if avg_response_time < 0.1:
                print("  Response Time: EXCELLENT")
            elif avg_response_time < 0.5:
                print("  Response Time: GOOD")
            else:
                print("  Response Time: ACCEPTABLE")
            
            if avg_rps > 50:
                print("  Throughput: EXCELLENT")
            elif avg_rps > 20:
                print("  Throughput: GOOD")
            else:
                print("  Throughput: ACCEPTABLE")
        
        # Recommendations
        print(f"\nRecommendations:")
        if not capabilities['enhanced_features']:
            print("  - Consider upgrading to Enhanced API for better performance")
            print("  - Implement async processing for higher concurrency")
            print("  - Add batch processing for improved throughput")
        else:
            print("  - Current API is well-optimized for production")
            print("  - Monitor performance metrics in production")
            print("  - Consider horizontal scaling for higher loads")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="GCP API Performance Analysis")
    parser.add_argument("--url", required=True, help="GCP API URL")
    
    args = parser.parse_args()
    
    print("GCP API Performance Analysis")
    print("=" * 40)
    print(f"API URL: {args.url}")
    
    comparison = GCPAPIComparison(args.url)
    
    # Test API capabilities
    print("\nAnalyzing API capabilities...")
    capabilities = await comparison.test_api_capabilities()
    
    # Run performance tests
    test_configs = [
        {"name": "Light", "users": 3, "requests": 3},
        {"name": "Moderate", "users": 5, "requests": 2},
        {"name": "Heavy", "users": 8, "requests": 2}
    ]
    
    print("\nRunning performance tests...")
    for config in test_configs:
        result = await comparison.run_performance_test(
            config["name"], 
            config["users"], 
            config["requests"]
        )
        if result:
            comparison.results.append(result)
        
        await asyncio.sleep(1)  # Small delay between tests
    
    # Test batch efficiency
    batch_results = {"batch_efficiency": 0}
    if capabilities['batch_predict']:
        batch_results = await comparison.test_batch_efficiency()
    
    # Generate comprehensive report
    comparison.generate_report(capabilities, batch_results)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Analysis failed: {e}")
        sys.exit(1)