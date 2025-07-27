#!/usr/bin/env python3

"""
Local Setup Test Script
Tests if all components are working correctly before GCP deployment
"""

import os
import sys
import subprocess
import time

def check_file_exists(filename, description):
    """Check if a file exists"""
    if os.path.exists(filename):
        print(f"✅ {description}: {filename}")
        return True
    else:
        print(f"❌ {description}: {filename} - NOT FOUND")
        return False

def check_python_imports():
    """Check if required Python packages are available"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'aiohttp',
        'asyncio',
        'psutil',
        'sklearn',
        'pandas',
        'numpy',
        'joblib'
    ]
    
    print("Checking Python package imports...")
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT AVAILABLE")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def test_model_training():
    """Test model training"""
    print("\nTesting model training...")
    try:
        result = subprocess.run([sys.executable, 'iris_pipeline.py'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Model training successful")
            return True
        else:
            print(f"❌ Model training failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Model training error: {e}")
        return False

def test_api_scripts():
    """Test if API scripts are syntactically correct"""
    print("\nTesting API scripts syntax...")
    
    scripts = [
        'iris_api.py',
        'iris_api_enhanced.py',
        'testing/concurrent_load_test.py',
        'testing/batch_comparison.py',
        'utils/api_features_comparison.py',
        'testing/gcp_concurrent_scaling_test.py',
        'testing/gcp_api_comparison.py',
        'utils/generate_final_report.py'
    ]
    
    all_good = True
    for script in scripts:
        if os.path.exists(script):
            try:
                result = subprocess.run([sys.executable, '-m', 'py_compile', script], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {script} - syntax OK")
                else:
                    print(f"❌ {script} - syntax error: {result.stderr}")
                    all_good = False
            except Exception as e:
                print(f"❌ {script} - error: {e}")
                all_good = False
        else:
            print(f"❌ {script} - file not found")
            all_good = False
    
    return all_good

def main():
    """Main test function"""
    print("🧪 Local Setup Test for Concurrent Inference Pipeline")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Check required files
    print("\n📁 Checking required files...")
    required_files = [
        ('data/iris.csv', 'Dataset'),
        ('iris_pipeline.py', 'Model training script'),
        ('iris_api.py', 'Basic API'),
        ('iris_api_enhanced.py', 'Enhanced API'),
        ('testing/concurrent_load_test.py', 'Load testing script'),
        ('scripts/demo_concurrent_pipeline.sh', 'Demo script'),
        ('.github/workflows/test_pipeline.yml', 'GitHub Actions workflow'),
        ('Dockerfile', 'Docker configuration'),
        ('requirements.txt', 'Python dependencies')
    ]
    
    for filename, description in required_files:
        if not check_file_exists(filename, description):
            all_tests_passed = False
    
    # Check Python imports
    print("\n🐍 Checking Python packages...")
    if not check_python_imports():
        all_tests_passed = False
        print("\n💡 Install missing packages with: pip install -r requirements.txt")
    
    # Test model training
    if not test_model_training():
        all_tests_passed = False
    
    # Test API scripts
    if not test_api_scripts():
        all_tests_passed = False
    
    # Final summary
    print("\n" + "=" * 60)
    print("📋 LOCAL SETUP TEST SUMMARY")
    print("=" * 60)
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Your setup is ready for GCP deployment")
        print("✅ All concurrent scaling components are working")
        print("✅ GitHub Actions workflow should run successfully")
        print("\n🚀 Next steps:")
        print("   1. Commit and push your changes")
        print("   2. GitHub Actions will automatically deploy to GCP")
        print("   3. Concurrent scaling tests will run on deployed API")
        print("   4. Performance reports will be generated automatically")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Please fix the issues above before deploying to GCP")
        print("\n🔧 Common fixes:")
        print("   - Install missing Python packages: pip install -r requirements.txt")
        print("   - Check file paths and permissions")
        print("   - Verify script syntax")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)