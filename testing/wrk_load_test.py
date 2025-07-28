#!/usr/bin/env python3

"""
wrk Load Test Script
Runs wrk benchmarking tests and compares results
"""

import subprocess
import sys
import argparse
import json
import re

def run_wrk_test(url, connections, duration, threads=None):
    """Run a wrk test and parse results"""
    if threads is None:
        threads = min(connections // 10, 12)  # Reasonable thread count
    
    cmd = [
        'wrk',
        f'-t{threads}',
        f'-c{connections}',
        f'-d{duration}s',
        '--timeout', '30s',
        f'{url}/health'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
        if result.returncode == 0:
            return parse_wrk_output(result.stdout)
        else:
            return {"error": f"wrk failed: {result.stderr}"}
    except subprocess.TimeoutExpired:
        return {"error": "wrk test timed out"}
    except Exception as e:
        return {"error": f"wrk test failed: {e}"}

def parse_wrk_output(output):
    """Parse wrk output to extract metrics"""
    metrics = {}
    
    # Extract requests per second
    rps_match = re.search(r'Requests/sec:\s+(\d+\.?\d*)', output)
    if rps_match:
        metrics['requests_per_sec'] = float(rps_match.group(1))
    
    # Extract latency statistics
    latency_match = re.search(r'Latency\s+(\d+\.?\d*\w*)\s+(\d+\.?\d*\w*)\s+(\d+\.?\d*\w*)\s+(\d+\.?\d*\w*)', output)
    if latency_match:
        metrics['latency_avg'] = latency_match.group(1)
        metrics['latency_stdev'] = latency_match.group(2)
        metrics['latency_max'] = latency_match.group(3)
        metrics['latency_stdev_pct'] = latency_match.group(4)
    
    # Extract total requests
    requests_match = re.search(r'(\d+) requests in', output)
    if requests_match:
        metrics['total_requests'] = int(requests_match.group(1))
    
    # Extract transfer rate
    transfer_match = re.search(r'Transfer/sec:\s+(\d+\.?\d*\w*)', output)
    if transfer_match:
        metrics['transfer_per_sec'] = transfer_match.group(1)
    
    return metrics

def run_wrk_comparison(api_url):
    """Run comprehensive wrk comparison tests"""
    
    print("wrk Benchmarking Comparison")
    print("=" * 40)
    print(f"API URL: {api_url}")
    print()
    
    # Test configurations matching the user requirements
    test_configs = [
        {"name": "Light Load", "connections": 25, "duration": 10},
        {"name": "Medium Load", "connections": 50, "duration": 10},
        {"name": "Heavy Load", "connections": 100, "duration": 10}
    ]
    
    results = []
    
    for config in test_configs:
        print(f"Running {config['name']} test ({config['connections']} connections, {config['duration']}s)...")
        
        result = run_wrk_test(
            api_url, 
            config['connections'], 
            config['duration']
        )
        
        result['test_name'] = config['name']
        result['connections'] = config['connections']
        results.append(result)
        
        if 'error' in result:
            print(f"  Error: {result['error']}")
        else:
            print(f"  Requests/sec: {result.get('requests_per_sec', 'N/A')}")
            print(f"  Avg Latency: {result.get('latency_avg', 'N/A')}")
            print(f"  Total Requests: {result.get('total_requests', 'N/A')}")
        print()
    
    # Generate comparison table
    print("wrk Benchmarking Results Summary")
    print("=" * 50)
    print(f"{'Test':<12} {'Connections':<12} {'RPS':<10} {'Avg Latency':<12} {'Total Req':<10}")
    print("-" * 60)
    
    for result in results:
        if 'error' not in result:
            print(f"{result['test_name']:<12} "
                  f"{result['connections']:<12} "
                  f"{result.get('requests_per_sec', 0):<10.1f} "
                  f"{result.get('latency_avg', 'N/A'):<12} "
                  f"{result.get('total_requests', 0):<10}")
        else:
            print(f"{result['test_name']:<12} "
                  f"{result['connections']:<12} "
                  f"{'ERROR':<10} "
                  f"{'ERROR':<12} "
                  f"{'ERROR':<10}")
    
    # Performance analysis
    print(f"\nPerformance Analysis:")
    successful_results = [r for r in results if 'error' not in r and 'requests_per_sec' in r]
    
    if successful_results:
        max_rps = max(r['requests_per_sec'] for r in successful_results)
        avg_rps = sum(r['requests_per_sec'] for r in successful_results) / len(successful_results)
        
        print(f"  Maximum RPS: {max_rps:.1f}")
        print(f"  Average RPS: {avg_rps:.1f}")
        
        # Find best performing test
        best_test = max(successful_results, key=lambda x: x['requests_per_sec'])
        print(f"  Best Performance: {best_test['test_name']} with {best_test['requests_per_sec']:.1f} RPS")
        
        # Performance assessment
        if avg_rps > 1000:
            print("  Assessment: EXCELLENT performance")
        elif avg_rps > 500:
            print("  Assessment: GOOD performance")
        elif avg_rps > 100:
            print("  Assessment: ACCEPTABLE performance")
        else:
            print("  Assessment: NEEDS IMPROVEMENT")
    else:
        print("  No successful tests to analyze")
    
    print(f"\nwrk benchmarking completed")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="wrk Load Testing for API")
    parser.add_argument("--url", required=True, help="API URL to test")
    
    args = parser.parse_args()
    
    # Check if wrk is available
    try:
        subprocess.run(['wrk', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: wrk is not installed or not available in PATH")
        print("Please install wrk: https://github.com/wg/wrk")
        sys.exit(1)
    
    # Run the comparison
    try:
        run_wrk_comparison(args.url)
    except KeyboardInterrupt:
        print("\nwrk testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"wrk testing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()