#!/usr/bin/env python3

"""
Memory Usage Test for Iris ML API
Tests memory consumption under different load patterns
"""

import psutil
import requests
import time
import threading
import sys
from typing import List, Dict
import gc

class MemoryTester:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip('/')
        self.memory_samples = []
        self.monitoring = False
        
    def get_memory_usage(self) -> Dict:
        """Get current memory usage"""
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'timestamp': time.time(),
            'process_memory_mb': memory_info.rss / (1024 * 1024),
            'process_memory_percent': process.memory_percent(),
            'system_memory_percent': system_memory.percent,
            'system_available_gb': system_memory.available / (1024**3)
        }
    
    def monitor_memory(self, duration: int):
        """Monitor memory usage in background"""
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < duration:
            self.memory_samples.append(self.get_memory_usage())
            time.sleep(0.5)  # Sample every 500ms
    
    def start_monitoring(self, duration: int):
        """Start memory monitoring"""
        self.monitoring = True
        self.memory_samples = []
        
        monitor_thread = threading.Thread(
            target=self.monitor_memory,
            args=(duration,)
        )
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
    
    def make_requests(self, num_requests: int, delay: float = 0.1):
        """Make multiple requests to test memory usage"""
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        successful_requests = 0
        failed_requests = 0
        
        for i in range(num_requests):
            try:
                response = requests.post(
                    f"{self.api_url}/predict",
                    json=test_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    
            except Exception as e:
                failed_requests += 1
                print(f"Request {i+1} failed: {e}")
            
            if delay > 0:
                time.sleep(delay)
            
            # Print progress
            if (i + 1) % 10 == 0:
                print(f"  Completed {i+1}/{num_requests} requests")
        
        return successful_requests, failed_requests
    
    def test_memory_leak(self):
        """Test for memory leaks with sustained load"""
        print("Testing for Memory Leaks")
        print("=" * 50)
        
        baseline = self.get_memory_usage()
        print(f"Baseline Memory Usage: {baseline['process_memory_mb']:.1f} MB")
        
        # Start monitoring
        monitor_thread = self.start_monitoring(120)  # Monitor for 2 minutes
        
        # Make sustained requests
        print("Making 200 requests with 0.5s intervals...")
        successful, failed = self.make_requests(200, 0.5)
        
        # Force garbage collection
        gc.collect()
        time.sleep(2)
        
        # Stop monitoring
        self.stop_monitoring()
        monitor_thread.join()
        
        # Get final memory
        final = self.get_memory_usage()
        
        # Analyze results
        print(f"\nMemory Leak Analysis:")
        print(f"   Baseline Memory: {baseline['process_memory_mb']:.1f} MB")
        print(f"   Final Memory: {final['process_memory_mb']:.1f} MB")
        print(f"   Memory Increase: {final['process_memory_mb'] - baseline['process_memory_mb']:.1f} MB")
        print(f"   Successful Requests: {successful}")
        print(f"   Failed Requests: {failed}")
        
        memory_increase = final['process_memory_mb'] - baseline['process_memory_mb']
        if memory_increase > 50:
            print(f"Warning: Potential memory leak detected ({memory_increase:.1f} MB increase)")
        else:
            print(f"No significant memory leak detected")
        
        # Analyze memory samples
        if self.memory_samples:
            memory_values = [sample['process_memory_mb'] for sample in self.memory_samples]
            max_memory = max(memory_values)
            min_memory = min(memory_values)
            
            print(f"\nMemory Usage During Test:")
            print(f"   Maximum: {max_memory:.1f} MB")
            print(f"   Minimum: {min_memory:.1f} MB")
            print(f"   Range: {max_memory - min_memory:.1f} MB")
    
    def test_batch_memory_usage(self):
        """Test memory usage with batch requests"""
        print("\nTesting Batch Request Memory Usage")
        print("=" * 50)
        
        # Test different batch sizes
        batch_sizes = [1, 5, 10, 20, 50]
        
        for batch_size in batch_sizes:
            print(f"\nTesting batch size: {batch_size}")
            
            # Create batch data
            batch_data = {
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
            
            # Get memory before request
            before = self.get_memory_usage()
            
            try:
                # Make batch request
                start_time = time.time()
                response = requests.post(
                    f"{self.api_url}/predict_batch",
                    json=batch_data,
                    timeout=30
                )
                end_time = time.time()
                
                # Get memory after request
                after = self.get_memory_usage()
                
                if response.status_code == 200:
                    memory_increase = after['process_memory_mb'] - before['process_memory_mb']
                    response_time = (end_time - start_time) * 1000
                    
                    print(f"   Success - Response time: {response_time:.1f}ms")
                    print(f"   Memory increase: {memory_increase:.1f} MB")
                    print(f"   Memory per item: {memory_increase/batch_size:.2f} MB")
                else:
                    print(f"   Failed - Status: {response.status_code}")
                    
            except Exception as e:
                print(f"   Error: {e}")
            
            # Small delay between tests
            time.sleep(1)
    
    def test_concurrent_memory_usage(self):
        """Test memory usage under concurrent load"""
        print("\nTesting Concurrent Request Memory Usage")
        print("=" * 50)
        
        import concurrent.futures
        
        def make_single_request():
            test_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            try:
                response = requests.post(
                    f"{self.api_url}/predict",
                    json=test_data,
                    timeout=5
                )
                return response.status_code == 200
            except:
                return False
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20]
        
        for concurrency in concurrency_levels:
            print(f"\nTesting {concurrency} concurrent requests")
            
            # Get memory before
            before = self.get_memory_usage()
            
            # Start monitoring
            monitor_thread = self.start_monitoring(30)
            
            # Make concurrent requests
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(make_single_request) for _ in range(concurrency * 5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            end_time = time.time()
            
            # Stop monitoring
            self.stop_monitoring()
            monitor_thread.join()
            
            # Get memory after
            after = self.get_memory_usage()
            
            # Analyze results
            successful = sum(results)
            total_time = end_time - start_time
            memory_increase = after['process_memory_mb'] - before['process_memory_mb']
            
            print(f"   Successful requests: {successful}/{len(results)}")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Memory increase: {memory_increase:.1f} MB")
            
            if self.memory_samples:
                memory_values = [sample['process_memory_mb'] for sample in self.memory_samples]
                peak_memory = max(memory_values)
                peak_increase = peak_memory - before['process_memory_mb']
                print(f"   Peak memory increase: {peak_increase:.1f} MB")
            
            time.sleep(2)  # Recovery time

def main():
    """Main function"""
    print("Memory Usage Testing for Iris ML API")
    print("=" * 60)
    
    api_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print("Error: API is not responding properly. Please start the API first.")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot connect to API at {api_url}. Please start the API first.")
        sys.exit(1)
    
    print("API is accessible")
    
    # Initialize tester
    tester = MemoryTester(api_url)
    
    try:
        # Test for memory leaks
        tester.test_memory_leak()
        
        # Test batch memory usage
        tester.test_batch_memory_usage()
        
        # Test concurrent memory usage
        tester.test_concurrent_memory_usage()
        
        print(f"\nMemory testing completed")
        print(f"\nRecommendations:")
        print(f"   - Monitor memory usage in production")
        print(f"   - Implement memory limits and monitoring")
        print(f"   - Consider batch processing for better memory efficiency")
        print(f"   - Use connection pooling to reduce memory overhead")
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        tester.stop_monitoring()
    except Exception as e:
        print(f"\nTesting failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()