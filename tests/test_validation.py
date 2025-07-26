import pytest
import pandas as pd
import joblib
import os
import mlflow
from iris_pipeline_mlflow import IrisMLflowPipeline

class TestIrisMLflowPipeline:
    
    def setup_method(self):
        # Use local tracking for tests to avoid GCS authentication issues
        mlflow.set_tracking_uri("sqlite:///test_mlflow.db")
        mlflow.set_experiment("test-iris-pipeline")
        self.pipeline = IrisMLflowPipeline()
        # Override MLFlow setup to use local tracking
        self.pipeline.setup_mlflow = self._setup_local_mlflow
        self.pipeline.setup_mlflow()
        
    def _setup_local_mlflow(self):
        """Setup MLFlow for local testing without GCS artifacts"""
        mlflow_dir = "./test_mlflow_tracking"
        os.makedirs(mlflow_dir, exist_ok=True)
        
        tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
        mlflow.set_tracking_uri(tracking_uri)
        
        experiment_name = "test-iris-hyperparameter-tuning"
        
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                # Create new experiment with local artifact location
                mlflow.create_experiment(name=experiment_name)
            mlflow.set_experiment(experiment_name)
        except Exception as e:
            mlflow.set_experiment(experiment_name)
    
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
        
    def test_data_validation(self):
        """Test data validation functionality"""
        X_train, X_test, y_train, y_test, X, y = self.pipeline.load_data()
        
        # Test data shapes
        assert X_train.shape[1] == 4  # iris has 4 features
        assert X_test.shape[1] == 4
        assert len(y_train.unique()) == 3  # iris has 3 classes
        assert len(y_test.unique()) <= 3  # test set might not have all classes
        
        # Test data types
        assert X_train.dtypes.apply(lambda x: x.kind in 'biufc').all()  # numeric types
        assert y_train.dtype == 'object' or y_train.dtype.kind in 'biufc'
        
        # Test no missing values
        assert not X_train.isnull().any().any()
        assert not X_test.isnull().any().any()
        assert not y_train.isnull().any()
        assert not y_test.isnull().any()
        
    def teardown_method(self):
        """Clean up test artifacts"""
        import shutil
        # Clean up test MLFlow directory
        if os.path.exists("test_mlflow_tracking"):
            shutil.rmtree("test_mlflow_tracking")
        
        # Clean up test model files
        for filename in ["logistic_regression_model.pkl", "test_mlflow.db"]:
            if os.path.exists(filename):
                os.remove(filename)