#!/usr/bin/env python3
"""
Quick test script to verify Week 8 poisoning setup works correctly.
This script performs basic validation of all components.
"""

import sys
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing module imports...")
    
    try:
        import pandas as pd
        import numpy as np
        import sklearn
        logger.info("Core ML packages imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import core packages: {e}")
        return False
    
    try:
        from data_poisoning import DataPoisoning
        from iris_poisoning_pipeline import IrisPoisoningPipeline
        logger.info("Week 8 modules imported successfully")
    except ImportError as e:
        logger.error(f"Failed to import Week 8 modules: {e}")
        return False
    
    return True

def test_data_availability():
    """Test that IRIS dataset is available."""
    logger.info("Testing data availability...")
    
    try:
        import pandas as pd
        from sklearn.datasets import load_iris
        
        # Check if CSV exists
        if os.path.exists("data/iris.csv"):
            df = pd.read_csv("data/iris.csv")
            logger.info(f"IRIS CSV found with shape: {df.shape}")
        else:
            # Create it from sklearn
            logger.info("Creating IRIS dataset...")
            os.makedirs("data", exist_ok=True)
            iris = load_iris()
            df = pd.DataFrame(iris.data, columns=iris.feature_names)
            df['species'] = iris.target_names[iris.target]
            df.to_csv('data/iris.csv', index=False)
            logger.info(f"IRIS CSV created with shape: {df.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"Data availability test failed: {e}")
        return False

def test_poisoning_basic():
    """Test basic poisoning functionality."""
    logger.info("Testing basic poisoning functionality...")
    
    try:
        from data_poisoning import DataPoisoning
        import pandas as pd
        
        # Load data
        df = pd.read_csv("data/iris.csv")
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        # Initialize poisoner
        poisoner = DataPoisoning(random_state=42)
        
        # Test random noise poisoning
        X_poison, y_poison, indices = poisoner.random_noise_poisoning(X, y, 0.1)
        logger.info(f"Random noise poisoning: {len(indices)} samples poisoned")
        
        # Test label flipping
        X_clean, y_flip, indices = poisoner.label_flipping_poisoning(X, y, 0.1)
        logger.info(f"Label flipping: {len(indices)} labels flipped")
        
        # Test detection
        outliers = poisoner.detect_outliers_isolation_forest(X_poison, contamination=0.1)
        logger.info(f"Outlier detection: {sum(outliers)} outliers detected")
        
        return True
        
    except Exception as e:
        logger.error(f"Basic poisoning test failed: {e}")
        traceback.print_exc()
        return False

def test_pipeline_basic():
    """Test basic pipeline functionality."""
    logger.info("Testing basic pipeline functionality...")
    
    try:
        from iris_poisoning_pipeline import IrisPoisoningPipeline
        import pandas as pd
        
        # Initialize pipeline
        pipeline = IrisPoisoningPipeline()
        
        # Load data (using the pipeline method)
        X_train, X_test, y_train, y_test, X, y = pipeline.load_data()
        logger.info(f"Data loaded: {X.shape}")
        
        # Test dataset creation
        datasets = pipeline.create_poisoned_datasets(X, y)
        logger.info(f"Datasets created: {list(datasets.keys())}")
        
        # Test model training on clean data (quick test)
        result = pipeline.train_model_on_dataset(X, y, 'logistic_regression', 'test')
        logger.info(f"Model training: accuracy = {result['test_accuracy']:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        traceback.print_exc()
        return False

def test_demo_script():
    """Test that demo script can be imported and basic functionality works."""
    logger.info("Testing demo script...")
    
    try:
        # Test import
        sys.path.append('.')
        from week8_poisoning_demo import Week8PoisoningDemo
        
        # Initialize demo
        demo = Week8PoisoningDemo(quick_mode=True)
        logger.info("Demo script imported and initialized successfully")
        
        # Test dataset creation (without running full demo)
        import pandas as pd
        df = pd.read_csv("data/iris.csv")
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        datasets = demo.create_and_analyze_datasets()
        logger.info(f"Demo dataset creation: {len(datasets)} datasets created")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo script test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests and provide summary."""
    logger.info("="*60)
    logger.info("WEEK 8 ASSIGNMENT SETUP VALIDATION")
    logger.info("="*60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Availability", test_data_availability),
        ("Basic Poisoning", test_poisoning_basic),
        ("Pipeline Functionality", test_pipeline_basic),
        ("Demo Script", test_demo_script)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            logger.error(f"{test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = 0
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        logger.info(f"{test_name}: {status}")
        if success:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("\nALL TESTS PASSED! Week 8 setup is ready.")
        logger.info("\nYou can now run:")
        logger.info("  python week8_poisoning_demo.py --quick")
        logger.info("  python week8_poisoning_demo.py")
        logger.info("  python iris_poisoning_pipeline.py")
        return True
    else:
        logger.error(f"\n{len(tests) - passed} test(s) failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)