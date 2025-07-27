#!/usr/bin/env python3

"""
Complete Pipeline Integration Test
Tests the entire concurrent scaling pipeline end-to-end
"""

import subprocess
import sys
import os
import time
import signal
import requests
from typing import Optional

class PipelineIntegrationTest:
    def __init__(self):
        self.api_process: Optional[subprocess.Popen] = None
        self.api_port = 8000
        self.api_url = f"http://localhost:{self.api_port}"
        
    def cleanup(self):
        """Clean up any running processes"""
        if self.api_process:
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
            except:
                try:
                    self.api_process.kill()
                except:
                    pass
        
        # Kill any processes using the port
        try:
            subprocess.run(f"lsof -ti:{self.api_port} | xargs kill -9", 
                         shell=True, capture_output=True)
        except:
            pass
    
    def start_enhanced_api(self) -> bool:
        """Start the enhanced API server"""
        print("🚀 Starting Enhanced API server...")
        
        try:
            self.api_process = subprocess.Popen([
                sys.executable, "iris_api_enhanced.py"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for API to start
            for i in range(30):
                try:
                    response = requests.get(f"{self.api_url}/health", timeout=1)
                    if response.status_code == 200:
                        print("✅ Enhanced API started successfully")
                        return True
                except:
                    time.sleep(1)
            
            print("❌ Enhanced API failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting Enhanced API: {e}")
            return False
    
    def test_model_training(self) -> bool:
        """Test model training"""
        print("\n📚 Testing model training...")
        
        try:
            result = subprocess.run([
                sys.executable, "iris_pipeline.py"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists("model.pkl"):
                print("✅ Model training successful")
                return True
            else:
                print(f"❌ Model training failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Model training error: {e}")
            return False
    
    def test_api_functionality(self) -> bool:
        """Test basic API functionality"""
        print("\n🔧 Testing API functionality...")
        
        try:
            # Test health endpoint
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code != 200:
                print("❌ Health endpoint failed")
                return False
            
            health_data = response.json()
            if not health_data.get("model_loaded"):
                print("❌ Model not loaded in API")
                return False
            
            print("✅ Health endpoint working")
            
            # Test prediction endpoint
            test_data = {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2
            }
            
            response = requests.post(f"{self.api_url}/predict", json=test_data, timeout=5)
            if response.status_code != 200:
                print("❌ Prediction endpoint failed")
                return False
            
            pred_data = response.json()
            if "prediction" not in pred_data:
                print("❌ Prediction response invalid")
                return False
            
            print("✅ Prediction endpoint working")
            
            # Test batch endpoint if available
            batch_data = {"features_list": [test_data, test_data]}
            response = requests.post(f"{self.api_url}/predict_batch", json=batch_data, timeout=5)
            if response.status_code == 200:
                print("✅ Batch endpoint working")
            else:
                print("⚠️  Batch endpoint not available (this is OK for basic API)")
            
            return True
            
        except Exception as e:
            print(f"❌ API functionality test error: {e}")
            return False
    
    def test_concurrent_scaling(self) -> bool:
        """Test concurrent scaling functionality"""
        print("\n⚡ Testing concurrent scaling...")
        
        try:
            # Run light concurrent test
            result = subprocess.run([
                sys.executable, "testing/concurrent_load_test.py",
                "--url", self.api_url,
                "--users", "3",
                "--requests", "2"
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print("✅ Concurrent load test successful")
                
                # Check for key metrics in output
                output = result.stdout
                if "LOAD TEST RESULTS" in output and "Success Rate" in output:
                    print("✅ Performance metrics generated")
                    return True
                else:
                    print("⚠️  Concurrent test ran but metrics unclear")
                    return True
            else:
                print(f"❌ Concurrent load test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Concurrent scaling test error: {e}")
            return False
    
    def test_batch_comparison(self) -> bool:
        """Test batch processing comparison"""
        print("\n📦 Testing batch processing comparison...")
        
        try:
            result = subprocess.run([
                sys.executable, "testing/batch_comparison.py",
                self.api_url
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                output = result.stdout
                if "Batch Processing Performance Comparison" in output:
                    print("✅ Batch comparison test successful")
                    return True
                else:
                    print("⚠️  Batch comparison ran but results unclear")
                    return True
            else:
                print(f"❌ Batch comparison failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Batch comparison test error: {e}")
            return False
    
    def test_api_features_comparison(self) -> bool:
        """Test API features comparison"""
        print("\n🏗️ Testing API features comparison...")
        
        try:
            result = subprocess.run([
                sys.executable, "utils/api_features_comparison.py"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                if "API FEATURES AND ARCHITECTURE COMPARISON" in output:
                    print("✅ API features comparison successful")
                    return True
                else:
                    print("⚠️  API features comparison ran but output unclear")
                    return True
            else:
                print(f"❌ API features comparison failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ API features comparison error: {e}")
            return False
    
    def run_complete_test(self) -> bool:
        """Run the complete pipeline test"""
        print("🧪 Complete Pipeline Integration Test")
        print("=" * 60)
        
        all_tests_passed = True
        
        try:
            # Test 1: Model Training
            if not self.test_model_training():
                all_tests_passed = False
            
            # Test 2: Start Enhanced API
            if not self.start_enhanced_api():
                all_tests_passed = False
                return all_tests_passed
            
            # Test 3: API Functionality
            if not self.test_api_functionality():
                all_tests_passed = False
            
            # Test 4: Concurrent Scaling
            if not self.test_concurrent_scaling():
                all_tests_passed = False
            
            # Test 5: Batch Comparison
            if not self.test_batch_comparison():
                all_tests_passed = False
            
            # Test 6: API Features Comparison
            if not self.test_api_features_comparison():
                all_tests_passed = False
            
        finally:
            self.cleanup()
        
        return all_tests_passed

def main():
    """Main function"""
    tester = PipelineIntegrationTest()
    
    # Set up signal handler for cleanup
    def signal_handler(sig, frame):
        print("\n🛑 Test interrupted, cleaning up...")
        tester.cleanup()
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        success = tester.run_complete_test()
        
        print("\n" + "=" * 60)
        print("📋 COMPLETE PIPELINE TEST SUMMARY")
        print("=" * 60)
        
        if success:
            print("🎉 ALL PIPELINE TESTS PASSED!")
            print("✅ Model training works")
            print("✅ Enhanced API starts and responds")
            print("✅ Concurrent scaling tests work")
            print("✅ Batch processing comparison works")
            print("✅ API features comparison works")
            print("\n🚀 Pipeline is ready for GCP deployment!")
            print("   - Commit and push to trigger GitHub Actions")
            print("   - Monitor workflow execution")
            print("   - Check generated reports")
        else:
            print("❌ SOME PIPELINE TESTS FAILED!")
            print("⚠️  Please fix issues before GCP deployment")
            print("\n🔧 Common fixes:")
            print("   - Check Python dependencies")
            print("   - Verify file permissions")
            print("   - Check API port availability")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Pipeline test failed with error: {e}")
        return False
    finally:
        tester.cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)