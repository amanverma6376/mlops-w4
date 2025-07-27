#!/usr/bin/env python3

"""
Performance Monitoring Script for Iris ML API
Monitors system resources and API performance in real-time
"""

import time
import psutil
import requests
import json
import threading
import argparse
from datetime import datetime
from typing import Dict, List
import matplotlib.pyplot as plt
import pandas as pd
from collections import deque
import sys

class PerformanceMonitor:
    def __init__(self, api_url: str = "http://localhost:8000", monitor_duration: int = 60):
        self.api_url = api_url.rstrip('/')
        self.monitor_duration = monitor_duration
        self.monitoring = False
        
        # Data storage
        self.metrics = {
            'timestamp': deque(maxlen=1000),
            'cpu_percent': deque(maxlen=1000),
            'memory_percent': deque(maxlen=1000),
            'memory_used_gb': deque(maxlen=1000),
            'response_time_ms': deque(maxlen=1000),
            'api_status': deque(maxlen=1000),
            'requests_per_second': deque(maxlen=1000)
        }
        
        self.request_times = deque(maxlen=100)  # Store recent request times for RPS calculation
        
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_available_gb': memory.available / (1024**3)
        }
    
    def test_api_response(self) -> Dict:
        """Test API response time and status"""
        test_data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/predict",
                json=test_data,
                timeout=5
            )
            end_time = time.time()
            
            response_time_ms = (end_time - start_time) * 1000
            
            return {
                'response_time_ms': response_time_ms,
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
            
        except Exception as e:
            return {
                'response_time_ms': 0,
                'status_code': 0,
                'success': False,
                'error': str(e)
            }
    
    def calculate_rps(self) -> float:
        """Calculate requests per second based on recent requests"""
        current_time = time.time()
        
        # Remove old requests (older than 1 second)
        while self.request_times and current_time - self.request_times[0] > 1.0:
            self.request_times.popleft()
        
        return len(self.request_times)
    
    def collect_metrics(self):
        """Collect metrics in a separate thread"""
        print(f"Starting performance monitoring for {self.monitor_duration} seconds...")
        
        start_time = time.time()
        
        while self.monitoring and (time.time() - start_time) < self.monitor_duration:
            current_time = time.time()
            
            # Get system metrics
            system_metrics = self.get_system_metrics()
            
            # Test API
            api_metrics = self.test_api_response()
            
            # Calculate RPS
            if api_metrics['success']:
                self.request_times.append(current_time)
            rps = self.calculate_rps()
            
            # Store metrics
            self.metrics['timestamp'].append(current_time)
            self.metrics['cpu_percent'].append(system_metrics['cpu_percent'])
            self.metrics['memory_percent'].append(system_metrics['memory_percent'])
            self.metrics['memory_used_gb'].append(system_metrics['memory_used_gb'])
            self.metrics['response_time_ms'].append(api_metrics['response_time_ms'])
            self.metrics['api_status'].append(1 if api_metrics['success'] else 0)
            self.metrics['requests_per_second'].append(rps)
            
            # Print real-time stats
            print(f"\r{datetime.now().strftime('%H:%M:%S')} | "
                  f"CPU: {system_metrics['cpu_percent']:5.1f}% | "
                  f"MEM: {system_metrics['memory_percent']:5.1f}% | "
                  f"API: {api_metrics['response_time_ms']:6.1f}ms | "
                  f"RPS: {rps:4.1f} | "
                  f"Status: {'OK' if api_metrics['success'] else 'FAIL'}", end='')
            
            time.sleep(1)  # Collect metrics every second
        
        print(f"\nMonitoring completed")
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        self.monitoring = True
        monitor_thread = threading.Thread(target=self.collect_metrics)
        monitor_thread.daemon = True
        monitor_thread.start()
        return monitor_thread
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
    
    def generate_report(self):
        """Generate performance report"""
        if not self.metrics['timestamp']:
            print("No metrics collected")
            return
        
        print("\n" + "="*80)
        print("PERFORMANCE MONITORING REPORT")
        print("="*80)
        
        # Convert to lists for analysis
        cpu_values = list(self.metrics['cpu_percent'])
        memory_values = list(self.metrics['memory_percent'])
        response_times = [rt for rt in self.metrics['response_time_ms'] if rt > 0]
        api_status = list(self.metrics['api_status'])
        rps_values = list(self.metrics['requests_per_second'])
        
        # System Resource Analysis
        print(f"\nSystem Resource Analysis:")
        print(f"   CPU Usage:")
        print(f"     Average: {sum(cpu_values)/len(cpu_values):.1f}%")
        print(f"     Maximum: {max(cpu_values):.1f}%")
        print(f"     Minimum: {min(cpu_values):.1f}%")
        
        print(f"   Memory Usage:")
        print(f"     Average: {sum(memory_values)/len(memory_values):.1f}%")
        print(f"     Maximum: {max(memory_values):.1f}%")
        print(f"     Minimum: {min(memory_values):.1f}%")
        
        # API Performance Analysis
        if response_times:
            print(f"\nAPI Performance Analysis:")
            print(f"   Response Time:")
            print(f"     Average: {sum(response_times)/len(response_times):.1f}ms")
            print(f"     Maximum: {max(response_times):.1f}ms")
            print(f"     Minimum: {min(response_times):.1f}ms")
            
            sorted_times = sorted(response_times)
            p95_index = int(0.95 * len(sorted_times))
            p99_index = int(0.99 * len(sorted_times))
            
            print(f"     95th Percentile: {sorted_times[p95_index]:.1f}ms")
            print(f"     99th Percentile: {sorted_times[p99_index]:.1f}ms")
        
        # Availability Analysis
        successful_requests = sum(api_status)
        total_requests = len(api_status)
        availability = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        print(f"\nAvailability Analysis:")
        print(f"   Successful Requests: {successful_requests}/{total_requests}")
        print(f"   Availability: {availability:.2f}%")
        
        if rps_values:
            print(f"\nThroughput Analysis:")
            print(f"   Average RPS: {sum(rps_values)/len(rps_values):.1f}")
            print(f"   Maximum RPS: {max(rps_values):.1f}")
        
        print(f"\nPerformance Issues Detected:")
        issues = []
        
        if max(cpu_values) > 90:
            issues.append(f"   High CPU usage detected (max: {max(cpu_values):.1f}%)")
        
        if max(memory_values) > 90:
            issues.append(f"   High memory usage detected (max: {max(memory_values):.1f}%)")
        
        if response_times and sum(response_times)/len(response_times) > 1000:
            issues.append(f"   Slow API response times (avg: {sum(response_times)/len(response_times):.1f}ms)")
        
        if availability < 95:
            issues.append(f"   Low API availability ({availability:.1f}%)")
        
        if not issues:
            print("   No significant performance issues detected")
        else:
            for issue in issues:
                print(issue)
        
        print(f"\nRecommendations:")
        if max(cpu_values) > 80:
            print("   - Consider scaling up CPU resources or optimizing CPU-intensive operations")
        
        if max(memory_values) > 80:
            print("   - Monitor memory leaks and consider increasing available memory")
        
        if response_times and sum(response_times)/len(response_times) > 500:
            print("   - Optimize model inference time or implement caching")
        
        if availability < 99:
            print("   - Investigate API failures and implement better error handling")
    
    def save_metrics_to_csv(self, filename: str = None):
        """Save metrics to CSV file"""
        if not filename:
            filename = f"performance_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        if not self.metrics['timestamp']:
            print("No metrics to save")
            return
        
        # Convert to DataFrame
        df_data = {}
        for key, values in self.metrics.items():
            df_data[key] = list(values)
        
        # Ensure all lists have the same length
        min_length = min(len(values) for values in df_data.values())
        for key in df_data:
            df_data[key] = df_data[key][:min_length]
        
        df = pd.DataFrame(df_data)
        
        # Convert timestamp to readable format
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        df.to_csv(filename, index=False)
        print(f"Metrics saved to {filename}")
    
    def plot_metrics(self):
        """Generate performance plots"""
        if not self.metrics['timestamp']:
            print("No metrics to plot")
            return
        
        try:
            # Convert timestamps to relative time (seconds from start)
            timestamps = list(self.metrics['timestamp'])
            start_time = timestamps[0]
            relative_times = [(t - start_time) for t in timestamps]
            
            # Create subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('API Performance Monitoring Dashboard', fontsize=16)
            
            # CPU Usage
            ax1.plot(relative_times, list(self.metrics['cpu_percent']), 'b-', linewidth=2)
            ax1.set_title('CPU Usage (%)')
            ax1.set_xlabel('Time (seconds)')
            ax1.set_ylabel('CPU %')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0, 100)
            
            # Memory Usage
            ax2.plot(relative_times, list(self.metrics['memory_percent']), 'g-', linewidth=2)
            ax2.set_title('Memory Usage (%)')
            ax2.set_xlabel('Time (seconds)')
            ax2.set_ylabel('Memory %')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 100)
            
            # API Response Time
            response_times = list(self.metrics['response_time_ms'])
            ax3.plot(relative_times, response_times, 'r-', linewidth=2)
            ax3.set_title('API Response Time (ms)')
            ax3.set_xlabel('Time (seconds)')
            ax3.set_ylabel('Response Time (ms)')
            ax3.grid(True, alpha=0.3)
            
            # Requests Per Second
            ax4.plot(relative_times, list(self.metrics['requests_per_second']), 'm-', linewidth=2)
            ax4.set_title('Requests Per Second')
            ax4.set_xlabel('Time (seconds)')
            ax4.set_ylabel('RPS')
            ax4.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            plot_filename = f"performance_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            print(f"Performance plot saved to {plot_filename}")
            
            plt.show()
            
        except Exception as e:
            print(f"Error generating plots: {e}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Monitor API performance")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--duration", type=int, default=60, help="Monitoring duration in seconds")
    parser.add_argument("--save-csv", action="store_true", help="Save metrics to CSV")
    parser.add_argument("--plot", action="store_true", help="Generate performance plots")
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.url, args.duration)
    
    try:
        # Start monitoring
        monitor_thread = monitor.start_monitoring()
        
        # Wait for monitoring to complete
        monitor_thread.join()
        
        # Generate report
        monitor.generate_report()
        
        # Save metrics if requested
        if args.save_csv:
            monitor.save_metrics_to_csv()
        
        # Generate plots if requested
        if args.plot:
            monitor.plot_metrics()
            
    except KeyboardInterrupt:
        print("\nMonitoring interrupted by user")
        monitor.stop_monitoring()
    except Exception as e:
        print(f"\nMonitoring failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()