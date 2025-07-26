#!/usr/bin/env python3

"""
API Testing Script for Iris ML Model API
Tests all endpoints to ensure proper functionality
"""

import requests
import json
import sys
import time
from typing import Dict, Any

class IrisAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed"] += 1
            print(f"✅ {test_name}: PASSED {message}")
        else:
            self.results["failed"] += 1
            self.results["errors"].append(f"{test_name}: {message}")
            print(f"❌ {test_name}: FAILED {message}")
    
    def test_root_endpoint(self) -> bool:
        """Test root endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Iris ML Model API" in data["message"]:
                    self.log_result("Root Endpoint", True, f"Status: {response.status_code}")
                    return True
            self.log_result("Root Endpoint", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Root Endpoint", False, f"Exception: {str(e)}")
            return False
    
    def test_health_endpoint(self) -> bool:
        """Test health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                if "status" in data and "model_loaded" in data:
                    status = "healthy" if data.get("model_loaded") else "unhealthy"
                    self.log_result("Health Check", True, f"Status: {status}")
                    return True
            self.log_result("Health Check", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {str(e)}")
            return False
    
    def test_predict_endpoint(self) -> bool:
        """Test prediction endpoint with valid data"""
        try:
            test_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            response = self.session.post(
                f"{self.base_url}/predict",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "prediction" in data and "confidence" in data:
                    pred = data["prediction"]
                    conf = data["confidence"]
                    self.log_result("Prediction", True, f"Predicted: {pred}, Confidence: {conf:.3f}")
                    return True
            self.log_result("Prediction", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Prediction", False, f"Exception: {str(e)}")
            return False
    
    def test_predict_batch_endpoint(self) -> bool:
        """Test batch prediction endpoint"""
        try:
            test_data = [
                {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2},
                {"sepal_length": 6.2, "sepal_width": 3.4, "petal_length": 5.4, "petal_width": 2.3},
                {"sepal_length": 5.9, "sepal_width": 3.0, "petal_length": 5.1, "petal_width": 1.8}
            ]
            
            response = self.session.post(
                f"{self.base_url}/predict_batch",
                json=test_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) == 3:
                    predictions = [item["prediction"] for item in data]
                    self.log_result("Batch Prediction", True, f"Predictions: {predictions}")
                    return True
            self.log_result("Batch Prediction", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Batch Prediction", False, f"Exception: {str(e)}")
            return False
    
    def test_model_info_endpoint(self) -> bool:
        """Test model info endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/model_info")
            if response.status_code == 200:
                data = response.json()
                if "model_type" in data and "model_loaded" in data:
                    model_type = data["model_type"]
                    self.log_result("Model Info", True, f"Model Type: {model_type}")
                    return True
            self.log_result("Model Info", False, f"Status: {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Model Info", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_prediction(self) -> bool:
        """Test prediction with invalid data"""
        try:
            invalid_data = {
                "sepal_length": "invalid",
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            response = self.session.post(
                f"{self.base_url}/predict",
                json=invalid_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Should return 422 for validation error
            if response.status_code == 422:
                self.log_result("Invalid Data Handling", True, "Properly rejected invalid data")
                return True
            else:
                self.log_result("Invalid Data Handling", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Invalid Data Handling", False, f"Exception: {str(e)}")
            return False
    
    def test_openapi_docs(self) -> bool:
        """Test OpenAPI documentation endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_result("API Documentation", True, "Swagger UI accessible")
                return True
            else:
                self.log_result("API Documentation", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Documentation", False, f"Exception: {str(e)}")
            return False
    
    def test_performance(self) -> bool:
        """Basic performance test"""
        try:
            test_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            # Test multiple requests
            times = []
            for _ in range(10):
                start_time = time.time()
                response = self.session.post(
                    f"{self.base_url}/predict",
                    json=test_data,
                    headers={"Content-Type": "application/json"}
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    times.append(end_time - start_time)
                else:
                    self.log_result("Performance Test", False, f"Request failed: {response.status_code}")
                    return False
            
            avg_time = sum(times) / len(times)
            max_time = max(times)
            
            if avg_time < 1.0:  # Should respond within 1 second on average
                self.log_result("Performance Test", True, f"Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
                return True
            else:
                self.log_result("Performance Test", False, f"Too slow - Avg: {avg_time:.3f}s")
                return False
                
        except Exception as e:
            self.log_result("Performance Test", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting API Tests...")
        print("=" * 50)
        
        # Basic connectivity
        print("\n📡 Testing Basic Connectivity:")
        self.test_root_endpoint()
        self.test_health_endpoint()
        
        # Core functionality
        print("\n🎯 Testing Core Functionality:")
        self.test_predict_endpoint()
        self.test_predict_batch_endpoint()
        self.test_model_info_endpoint()
        
        # Error handling
        print("\n🛡️ Testing Error Handling:")
        self.test_invalid_prediction()
        
        # Documentation
        print("\n📚 Testing Documentation:")
        self.test_openapi_docs()
        
        # Performance
        print("\n⚡ Testing Performance:")
        self.test_performance()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        
        if self.results['failed'] > 0:
            print(f"\n❌ Failed Tests:")
            for error in self.results['errors']:
                print(f"  - {error}")
            return False
        else:
            print(f"\n🎉 ALL TESTS PASSED! API is ready for production.")
            return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Iris API endpoints")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--wait", type=int, default=0, help="Wait time in seconds before starting tests")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds for API to start...")
        time.sleep(args.wait)
    
    tester = IrisAPITester(args.url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 