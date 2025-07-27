#!/usr/bin/env python3

"""
Pipeline Files Verification Script
Verifies all required files are in place for the GCP pipeline
"""

import os
import sys

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print(f"FOUND {description}: {filepath}")
        return True
    else:
        print(f"MISSING {description}: {filepath}")
        return False

def main():
    """Main verification function"""
    print("🔍 Verifying Pipeline Files for GCP Deployment")
    print("=" * 60)
    
    all_files_present = True
    
    # Core API files
    print("\n📁 Core API Files:")
    files_to_check = [
        ("iris_api.py", "Basic API"),
        ("iris_api_enhanced.py", "Enhanced API"),
        ("iris_pipeline.py", "Model Training"),
        ("Dockerfile", "Docker Configuration"),
        ("requirements.txt", "Python Dependencies")
    ]
    
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_files_present = False
    
    # Testing files
    print("\n🧪 Testing Files:")
    testing_files = [
        ("testing/gcp_concurrent_scaling_test.py", "GCP Concurrent Scaling Test"),
        ("testing/gcp_api_comparison.py", "GCP API Comparison"),
        ("testing/batch_comparison.py", "Batch Processing Test"),
        ("testing/concurrent_load_test.py", "Concurrent Load Test"),
        ("testing/test_memory.py", "Memory Test"),
        ("testing/test_concurrent_scaling.py", "Concurrent Scaling Test"),
        ("testing/wrk_load_test.py", "wrk Load Test"),
        ("testing/api_comparison.py", "API Comparison"),
        ("testing/test_api_endpoints.py", "API Endpoints Test"),
        ("testing/test_local_setup.py", "Local Setup Test")
    ]
    
    for filepath, description in testing_files:
        if not check_file_exists(filepath, description):
            all_files_present = False
    
    # Utility files
    print("\n🛠️ Utility Files:")
    util_files = [
        ("utils/api_features_comparison.py", "API Features Comparison"),
        ("utils/generate_final_report.py", "Final Report Generator")
    ]
    
    for filepath, description in util_files:
        if not check_file_exists(filepath, description):
            all_files_present = False
    
    # Infrastructure files
    print("\n🏗️ Infrastructure Files:")
    infra_files = [
        (".github/workflows/test_pipeline.yml", "GitHub Actions Workflow"),
        ("k8s/deployment.yaml", "Kubernetes Deployment"),
        ("data/iris.csv", "Dataset")
    ]
    
    for filepath, description in infra_files:
        if not check_file_exists(filepath, description):
            all_files_present = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 60)
    
    if all_files_present:
        print("🎉 ALL FILES PRESENT!")
        print("✅ Pipeline is ready for GCP deployment")
        print("✅ GitHub Actions workflow should run successfully")
        print("\n🚀 Next Steps:")
        print("   1. Commit and push changes to trigger GitHub Actions")
        print("   2. Monitor the workflow execution")
        print("   3. Check the generated reports and artifacts")
    else:
        print("❌ SOME FILES ARE MISSING!")
        print("⚠️  Please ensure all required files are in place")
        print("\n🔧 To fix missing files:")
        print("   - Check if files were moved to different locations")
        print("   - Recreate missing files if necessary")
        print("   - Verify file permissions")
    
    return all_files_present

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)