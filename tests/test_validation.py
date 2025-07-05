import pytest
import pandas as pd
import joblib
import os
import mlflow
from iris_pipeline_mlflow import IrisMLflowPipeline

class TestIrisMLflowPipeline:
    
    def setup_method(self):
        self.pipeline = IrisMLflowPipeline()
    
    def test_data_loading(self):
        X_train, X_test, y_train, y_test, X, y = self.pipeline.load_data()
        
        assert X_train is not None
        assert X_test is not None
        assert y_train is not None
        assert y_test is not None
        assert len(X_train) > 0
        assert len(X_test) > 0
    
    def test_hyperparameter_tuning(self):
        X_train, X_test, y_train, y_test, X, y = self.pipeline.load_data()
        
        best_params, best_score = self.pipeline.tune_hyperparameters(
            X_train, y_train, 'logistic_regression', n_trials=3
        )
        
        assert best_params is not None
        assert best_score > 0
        assert isinstance(best_params, dict)
    
    def test_model_training_and_logging(self):
        X_train, X_test, y_train, y_test, X, y = self.pipeline.load_data()
        
        test_params = {'C': 1.0, 'max_iter': 200, 'solver': 'lbfgs'}
        
        model, run_id, test_accuracy = self.pipeline.train_and_log_model(
            'logistic_regression', test_params, X_train, X_test, y_train, y_test, X, y
        )
        
        assert model is not None
        assert run_id is not None
        assert test_accuracy > 0
        assert test_accuracy <= 1.0
    
    def test_model_file_creation(self):
        X_train, X_test, y_train, y_test, X, y = self.pipeline.load_data()
        
        test_params = {'C': 1.0, 'max_iter': 200, 'solver': 'lbfgs'}
        
        self.pipeline.train_and_log_model(
            'logistic_regression', test_params, X_train, X_test, y_train, y_test, X, y
        )
        
        assert os.path.exists("logistic_regression_model.pkl")
        
        loaded_model = joblib.load("logistic_regression_model.pkl")
        assert loaded_model is not None