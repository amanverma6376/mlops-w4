#!/usr/bin/env python3

"""
wrk Integration Script
Compares our Python async approach with wrk benchmarking tool
"""

import subprocess
import json
import time
import sys
import os
import tempfile
from typing import Dict, Optional

class WrkIntegration:
    def __init__(self, api_url: str):
        self.api_url = api_url.rstrip('/')
        self.wrk_available = self.check_wrk_availability()
        
    def check_wrk_availability(self) -> bool:
        """Check if wrk is installed"""
        try:
            result = subprocess.run(['wrk', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def install_wrk_instructions(self):
        """Provide wrk installation instructions"""
        print("wrk is not installed. Installation instructions:")
        print("")
        print("macOS:")
        print("  brew install wrk")
        print("")
        print("Ubuntu/Debian:")
        print("  sudo apt-get install wrk")
        print("")
        print("CentOS/RHEL:")
        print("  sudo yum install wrk")
        print("")
        print("From source:")
        print("  git clone https://github.com/wg/wrk.git")
        print("  cd wrk")
        print("  make")
        print("  sudo cp wrk /usr/local/bin/")
    
    def create_lua_script(self, endpoint: str, payload: Optional[Dict] = None) -> str:
        """Create Lua script for wrk POST requests"""
        
        if payload:
            lua_script = f'''
wrk.method = "POST"
wrk.body = '{json.dumps(payload)}'
wrk.headers["Content-Type"] = "application/json"

request = function()
    return wrk.format(wrk.method, "{endpoint}")
end

response = function(status, headers, body)
    if status ~= 200 then
        print("Error: " .. status .. " - " .. body)
    end
end
'''
        else:
            lua_script = f'''
request = function()
    return wrk.format("GET", "{endpoint}")
end

response = function(status, headers, body)
    if status ~= 200 then
        print("Error: " .. status .. " - " .. body)
    end
end
'''
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as f:
            f.write(lua_script)
            return f.name
    
    def run_wrk_test(self, endpoint: str, connections: int, threads: int, 
                     duration: str, payload: Optional[Dict] = None) -> Dict:
        """Run wrk load test"""
        
        if not self.wrk_available:
            return {"error": "wrk not available"}
        
        # Create Lua script if needed
        lua_script = None
        if payload or endpoint != "/health":
            lua_script = self.create_lua_script(endpoint, payload)
        
        # Build wrk command
        cmd = [
            'wrk',
            '-t', str(threads),
            '-c', str(connections),
            '-d', duration,
            '--timeout', '30s'
        ]
        
        if lua_script:
            cmd.extend(['-s', lua_script])
        
        cmd.append(f"{self.api_url}{endpoint}")
        
        try:
            print(f"Running wrk: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Clean up Lua script
            if lua_script:
                try:
                    os.unlink(lua_script)
                except:
                    pass
            
            if result.returncode == 0:
                return self.parse_wrk_output(result.stdout)
            else:
                return {"error": f"wrk failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "wrk test timed out"}
        except Exception as e:
            return {"error": f"wrk execution error: {e}"}
    
    def parse_wrk_output(self, output: str) -> Dict:
        """Parse wrk output into structured data"""
        lines = output.strip().split('\n')
        result = {}
        
        for line in lines:
            line = line.strip()
            
            # Parse key metrics
            if 'Requests/sec:' in line:
                result['requests_per_sec'] = float(line.split(':')[1].strip())
            elif 'Transfer/sec:' in line:
                result['transfer_per_sec'] = line.split(':')[1].strip()
            elif line.startswith('Latency'):
                # Parse latency line: "Latency     1.23ms    2.34ms   10.45ms   67.89%"
                parts = line.split()
                if len(parts) >= 4:
                    result['latency_avg'] = parts[1]
                    result['latency_stdev'] = parts[2]
                    result['latency_max'] = parts[3]
            elif 'requests in' in line:
                # Parse summary line: "1000 requests in 10.00s, 2.34MB read"
                parts = line.split()
                if len(parts) >= 1:
                    result['total_requests'] = int(parts[0])
                if 'in' in line:
                    duration_part = line.split('in')[1].split(',')[0].strip()
                    result['duration'] = duration_part
            elif 'Socket errors:' in line:
                result['socket_errors'] = line.split(':')[1].strip()
            elif 'Non-2xx or 3xx responses:' in line:
                result['error_responses'] = int(line.split(':')[1].strip())
        
        return result
    
    def run_comparison_tests(self):
        """Run comparison between wrk and our Python approach"""
        
        print("wrk vs Python Async Load Testing Comparison")
        print("=" * 60)
        
        if not self.wrk_available:
            print("wrk is not available. Installing wrk will enable comparison.")
            self.install_wrk_instructions()
            return
        
        # Test configurations
        test_configs = [
            {"name": "Light Load", "connections": 10, "threads": 2, "duration": "10s"},
            {"name": "Moderate Load", "connections": 50, "threads": 4, "duration": "10s"},
            {"name": "Heavy Load", "connections": 100, "threads": 8, "duration": "10s"}
        ]
        
        # Test data for ML predictions
        test_payload = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        print(f"\nTesting API: {self.api_url}")
        print(f"Endpoint: /predict")
        print(f"Payload: {test_payload}")
        print()
        
        results = []
        
        for config in test_configs:
            print(f"Running {config['name']} test...")
            print(f"  Connections: {config['connections']}, Threads: {config['threads']}, Duration: {config['duration']}")
            
            # Run wrk test
            wrk_result = self.run_wrk_test(
                "/predict", 
                config['connections'], 
                config['threads'], 
                config['duration'],
                test_payload
            )
            
            if 'error' not in wrk_result:
                print(f"  wrk Results:")
                print(f"    Requests/sec: {wrk_result.get('requests_per_sec', 'N/A')}")
                print(f"    Avg Latency: {wrk_result.get('latency_avg', 'N/A')}")
                print(f"    Total Requests: {wrk_result.get('total_requests', 'N/A')}")
                
                results.append({
                    'config': config,
                    'wrk_result': wrk_result
                })
            else:
                print(f"  wrk Error: {wrk_result['error']}")
            
            print()
            time.sleep(2)  # Brief pause between tests
        
        # Generate comparison report
        self.generate_comparison_report(results)
    
    def generate_comparison_report(self, results):
        """Generate detailed comparison report"""
        
        if not results:
            print("No successful wrk results to analyze")
            return
        
        print("DETAILED COMPARISON ANALYSIS")
        print("=" * 60)
        
        print(f"{'Test':<15} {'Connections':<12} {'RPS':<10} {'Avg Latency':<12} {'Total Reqs':<12}")
        print("-" * 70)
        
        for result in results:
            config = result['config']
            wrk = result['wrk_result']
            
            print(f"{config['name']:<15} "
                  f"{config['connections']:<12} "
                  f"{wrk.get('requests_per_sec', 0):<10.1f} "
                  f"{wrk.get('latency_avg', 'N/A'):<12} "
                  f"{wrk.get('total_requests', 0):<12}")
        
        print()
        print("TOOL COMPARISON: wrk vs Python Async")
        print("=" * 60)
        
        print("wrk Advantages:")
        print("  + Extremely high performance (C implementation)")
        print("  + Industry standard benchmarking tool")
        print("  + Minimal resource overhead")
        print("  + Can generate massive concurrent load")
        print("  + Simple command-line interface")
        print("  + Lua scripting for custom scenarios")
        
        print("\nPython Async Advantages:")
        print("  + ML-aware testing (validates predictions)")
        print("  + Custom response analysis")
        print("  + Integrated with Python ML ecosystem")
        print("  + Flexible test scenarios")
        print("  + Better error categorization")
        print("  + Batch processing testing")
        print("  + Real-time system monitoring")
        
        print("\nRecommendations:")
        print("  • Use wrk for: Raw HTTP performance, stress testing, simple benchmarks")
        print("  • Use Python async for: ML validation, complex scenarios, integrated testing")
        print("  • Use both for: Comprehensive performance analysis")
        
        # Performance assessment
        if results:
            avg_rps = sum(r['wrk_result'].get('requests_per_sec', 0) for r in results) / len(results)
            
            print(f"\nPerformance Assessment:")
            if avg_rps > 1000:
                print(f"  Excellent performance: {avg_rps:.0f} RPS average")
            elif avg_rps > 500:
                print(f"  Good performance: {avg_rps:.0f} RPS average")
            elif avg_rps > 100:
                print(f"  Acceptable performance: {avg_rps:.0f} RPS average")
            else:
                print(f"  Performance needs improvement: {avg_rps:.0f} RPS average")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="wrk Integration and Comparison")
    parser.add_argument("--url", default="http://localhost:8000", help="API URL to test")
    parser.add_argument("--check-only", action="store_true", help="Only check if wrk is available")
    
    args = parser.parse_args()
    
    wrk_integration = WrkIntegration(args.url)
    
    if args.check_only:
        if wrk_integration.wrk_available:
            print("wrk is available and ready to use")
        else:
            print("wrk is not available")
            wrk_integration.install_wrk_instructions()
        return
    
    # Check API availability
    try:
        import requests
        response = requests.get(f"{args.url}/health", timeout=5)
        if response.status_code != 200:
            print(f"API at {args.url} is not accessible")
            sys.exit(1)
    except Exception as e:
        print(f"Cannot connect to API at {args.url}: {e}")
        sys.exit(1)
    
    # Run comparison tests
    wrk_integration.run_comparison_tests()

if __name__ == "__main__":
    main()