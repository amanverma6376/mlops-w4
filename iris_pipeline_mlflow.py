import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import optuna
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MLflow configuration
PROJECT_ID = "citric-aleph-461515-j9"
BUCKET_NAME = "mlops-course-citric-aleph-461515-j9-unique"

class IrisMLflowPipeline:
    def __init__(self):
        self.setup_mlflow()
        
    def setup_mlflow(self):

        mlflow_dir = "./mlflow_tracking"
        os.makedirs(mlflow_dir, exist_ok=True)
        

        tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
        mlflow.set_tracking_uri(tracking_uri)
        

        experiment_name = "iris-hyperparameter-tuning"
        artifact_location = f"gs://{BUCKET_NAME}/mlflow-artifacts"
        
        try:
            # Try to get existing experiment
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                # Create new experiment with GCS artifact location
                mlflow.create_experiment(
                    name=experiment_name,
                    artifact_location=artifact_location
                )
            mlflow.set_experiment(experiment_name)
            logger.info(f"MLflow experiment '{experiment_name}' set up successfully")
        except Exception as e:
            logger.warning(f"Could not set artifact location to GCS: {e}")
            # Clean up any corrupted database and retry
            try:
                import shutil
                import os
                if os.path.exists('./mlflow_tracking'):
                    shutil.rmtree('./mlflow_tracking')
                    logger.info("Cleaned corrupted MLflow database")
                
                # Reinitialize MLflow tracking
                mlflow_dir = "./mlflow_tracking"
                os.makedirs(mlflow_dir, exist_ok=True)
                tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
                mlflow.set_tracking_uri(tracking_uri)
                
                # Create experiment with fallback
                mlflow.set_experiment(experiment_name)
                logger.info(f"MLflow experiment '{experiment_name}' initialized with clean database")
            except Exception as retry_error:
                logger.error(f"Failed to initialize MLflow even after cleanup: {retry_error}")
                # Final fallback - use default tracking
                mlflow.set_experiment(experiment_name)
        
    def load_data(self):
        """Load and prepare the Iris dataset."""
        try:
            df = pd.read_csv("data/iris.csv")
            X = df.iloc[:, :-1]  # Features
            y = df.iloc[:, -1]   # Target
            

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            logger.info(f"Data loaded successfully. Shape: {df.shape}")
            return X_train, X_test, y_train, y_test, X, y
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def objective_logistic_regression(self, trial, X_train, y_train):
        C = trial.suggest_float('C', 0.01, 100.0, log=True)
        max_iter = trial.suggest_int('max_iter', 100, 1000)
        solver = trial.suggest_categorical('solver', ['liblinear', 'lbfgs'])
        

        model = LogisticRegression(
            C=C,
            max_iter=max_iter,
            solver=solver,
            random_state=42
        )
        

        scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        return scores.mean()
    
    def objective_random_forest(self, trial, X_train, y_train):

        n_estimators = trial.suggest_int('n_estimators', 10, 200)
        max_depth = trial.suggest_int('max_depth', 3, 20)
        min_samples_split = trial.suggest_int('min_samples_split', 2, 20)
        min_samples_leaf = trial.suggest_int('min_samples_leaf', 1, 10)
        

        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            random_state=42
        )
        

        scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        return scores.mean()
    
    def objective_svm(self, trial, X_train, y_train):
        C = trial.suggest_float('C', 0.01, 100.0, log=True)
        kernel = trial.suggest_categorical('kernel', ['linear', 'rbf', 'poly'])
        gamma = trial.suggest_categorical('gamma', ['scale', 'auto'])
        

        model = SVC(
            C=C,
            kernel=kernel,
            gamma=gamma,
            random_state=42
        )
        

        scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        return scores.mean()
    
    def tune_hyperparameters(self, X_train, y_train, model_type='logistic_regression', n_trials=50):

        logger.info(f"Starting hyperparameter tuning for {model_type}")
        

        if model_type == 'logistic_regression':
            objective = lambda trial: self.objective_logistic_regression(trial, X_train, y_train)
        elif model_type == 'random_forest':
            objective = lambda trial: self.objective_random_forest(trial, X_train, y_train)
        elif model_type == 'svm':
            objective = lambda trial: self.objective_svm(trial, X_train, y_train)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        

        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        
        logger.info(f"Best parameters for {model_type}: {study.best_params}")
        logger.info(f"Best CV score: {study.best_value:.4f}")
        
        return study.best_params, study.best_value
    
    def train_and_log_model(self, model_type, best_params, X_train, X_test, y_train, y_test, X, y):
        
        with mlflow.start_run(run_name=f"{model_type}_best_model"):

            if model_type == 'logistic_regression':
                model = LogisticRegression(**best_params, random_state=42)
            elif model_type == 'random_forest':
                model = RandomForestClassifier(**best_params, random_state=42)
            elif model_type == 'svm':
                model = SVC(**best_params, random_state=42)
            

            model.fit(X_train, y_train)
            

            train_predictions = model.predict(X_train)
            test_predictions = model.predict(X_test)
            

            train_accuracy = accuracy_score(y_train, train_predictions)
            test_accuracy = accuracy_score(y_test, test_predictions)
            

            mlflow.log_params(best_params)
            mlflow.log_param("model_type", model_type)
            

            mlflow.log_metric("train_accuracy", train_accuracy)
            mlflow.log_metric("test_accuracy", test_accuracy)
            
            signature = infer_signature(X_train, train_predictions)
            mlflow.sklearn.log_model(
                model, 
                "model",
                signature=signature,
                input_example=X_train.iloc[:5]
            )
            
            report = classification_report(y_test, test_predictions, output_dict=True)
            mlflow.log_dict(report, "classification_report.json")
            
            model_filename = f"{model_type}_model.pkl"
            joblib.dump(model, model_filename)
            mlflow.log_artifact(model_filename)
            
            run_id = mlflow.active_run().info.run_id
            logger.info(f"Model logged with run_id: {run_id}")
            logger.info(f"Train accuracy: {train_accuracy:.4f}")
            logger.info(f"Test accuracy: {test_accuracy:.4f}")
            
            return model, run_id, test_accuracy
    
    def run_experiment(self):
        logger.info("Starting Iris ML Pipeline with MLflow")
        
        X_train, X_test, y_train, y_test, X, y = self.load_data()
        

        models = ['logistic_regression', 'random_forest', 'svm']
        best_model = None
        best_accuracy = 0
        best_run_id = None
        
        results = {}
        
        for model_type in models:
            logger.info(f"\n=== Tuning {model_type.upper()} ===")
            
            best_params, best_cv_score = self.tune_hyperparameters(
                X_train, y_train, model_type, n_trials=30
            )
            
            model, run_id, test_accuracy = self.train_and_log_model(
                model_type, best_params, X_train, X_test, y_train, y_test, X, y
            )
            
            results[model_type] = {
                'best_params': best_params,
                'cv_score': best_cv_score,
                'test_accuracy': test_accuracy,
                'run_id': run_id
            }
            
            if test_accuracy > best_accuracy:
                best_accuracy = test_accuracy
                best_model = model
                best_run_id = run_id
        

        with mlflow.start_run(run_name="model_comparison"):
            for model_type, result in results.items():
                mlflow.log_metric(f"{model_type}_test_accuracy", result['test_accuracy'])
                mlflow.log_metric(f"{model_type}_cv_score", result['cv_score'])
            
            mlflow.log_metric("best_accuracy", best_accuracy)
            mlflow.log_param("best_model_run_id", best_run_id)
        
        joblib.dump(best_model, "model.pkl")
        logger.info(f"\n=== EXPERIMENT COMPLETE ===")
        logger.info(f"Best model accuracy: {best_accuracy:.4f}")
        logger.info(f"Best model run_id: {best_run_id}")
        
        return results

def main():
    """Main function to run the pipeline."""
    pipeline = IrisMLflowPipeline()
    results = pipeline.run_experiment()
    return results

if __name__ == "__main__":
    main()