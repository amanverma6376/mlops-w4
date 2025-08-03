"""
Extended IRIS Pipeline with Data Poisoning Analysis - Week 8 Assignment
This module extends the existing MLflow pipeline to include data poisoning experiments.
"""

import pandas as pd
import numpy as np
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

from data_poisoning import DataPoisoning
from iris_pipeline_mlflow import IrisMLflowPipeline

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IrisPoisoningPipeline(IrisMLflowPipeline):
    """
    Extended pipeline that includes data poisoning experiments and analysis.
    Inherits from the existing IrisMLflowPipeline to maintain compatibility.
    """
    
    def __init__(self):
        super().__init__()
        self.poisoner = DataPoisoning(random_state=42)
        self.poison_rates = [0.05, 0.10, 0.50]  # 5%, 10%, 50%
        self.results_dir = "poisoning_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def setup_poisoning_experiment(self, experiment_name: str = "iris-poisoning-analysis"):
        """
        Set up MLflow experiment specifically for poisoning analysis.
        """
        mlflow_dir = "./mlflow_tracking"
        os.makedirs(mlflow_dir, exist_ok=True)
        
        tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
        mlflow.set_tracking_uri(tracking_uri)
        
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment is None:
                mlflow.create_experiment(name=experiment_name)
            mlflow.set_experiment(experiment_name)
            logger.info(f"MLflow experiment '{experiment_name}' set up successfully")
        except Exception as e:
            logger.warning(f"Could not set up experiment: {e}")
            mlflow.set_experiment(experiment_name)
    
    def create_poisoned_datasets(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Create poisoned datasets at different rates for experimentation.
        """
        logger.info("Creating poisoned datasets for experimentation")
        
        datasets = {
            'clean': {
                'X': X.copy(),
                'y': y.copy(),
                'poisoned_indices': [],
                'poison_rate': 0.0,
                'description': 'Original clean dataset'
            }
        }
        
        for rate in self.poison_rates:
            logger.info(f"Creating {rate*100}% poisoned dataset")
            
            # Use combined poisoning (both feature noise and label flipping)
            X_poison, y_poison, poison_indices = self.poisoner.combined_poisoning(X, y, rate)
            
            datasets[f'{int(rate*100)}%_poisoned'] = {
                'X': X_poison,
                'y': y_poison,
                'poisoned_indices': poison_indices,
                'poison_rate': rate,
                'description': f'Dataset with {rate*100}% combined poisoning (noise + label flipping)'
            }
        
        return datasets
    
    def detect_poisoning(self, X: pd.DataFrame, poison_rate: float) -> Dict:
        """
        Apply poisoning detection methods to a dataset.
        """
        logger.info(f"Applying poisoning detection methods")
        
        detection_results = {}
        
        # Isolation Forest detection
        outliers_iso = self.poisoner.detect_outliers_isolation_forest(
            X, contamination=min(poison_rate * 1.5, 0.5)  # Slightly higher than expected
        )
        detection_results['isolation_forest'] = {
            'outliers_detected': np.sum(outliers_iso),
            'outlier_indices': np.where(outliers_iso)[0].tolist(),
            'detection_rate': np.sum(outliers_iso) / len(X)
        }
        
        # Statistical detection (Z-score)
        outliers_stat = self.poisoner.statistical_detection(X, threshold=2.5)
        detection_results['statistical'] = {
            'outliers_detected': np.sum(outliers_stat),
            'outlier_indices': np.where(outliers_stat)[0].tolist(),
            'detection_rate': np.sum(outliers_stat) / len(X)
        }
        
        return detection_results
    
    def evaluate_detection_accuracy(self, detection_results: Dict, 
                                  true_poisoned_indices: List[int]) -> Dict:
        """
        Evaluate the accuracy of poisoning detection methods.
        """
        evaluation = {}
        
        for method, results in detection_results.items():
            detected_indices = set(results['outlier_indices'])
            true_indices = set(true_poisoned_indices)
            
            # Calculate metrics
            true_positives = len(detected_indices & true_indices)
            false_positives = len(detected_indices - true_indices)
            false_negatives = len(true_indices - detected_indices)
            true_negatives = len(detection_results) - true_positives - false_positives - false_negatives
            
            precision = true_positives / len(detected_indices) if len(detected_indices) > 0 else 0
            recall = true_positives / len(true_indices) if len(true_indices) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            evaluation[method] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'true_positives': true_positives,
                'false_positives': false_positives,
                'false_negatives': false_negatives
            }
        
        return evaluation
    
    def train_model_on_dataset(self, X: pd.DataFrame, y: pd.Series, 
                             model_type: str = 'logistic_regression',
                             dataset_name: str = 'unknown') -> Dict:
        """
        Train a model on a specific dataset and return performance metrics.
        """
        logger.info(f"Training {model_type} on {dataset_name} dataset")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Create model with basic parameters (for speed)
        if model_type == 'logistic_regression':
            model = LogisticRegression(max_iter=1000, random_state=42)
        elif model_type == 'random_forest':
            model = RandomForestClassifier(n_estimators=100, random_state=42)
        elif model_type == 'svm':
            model = SVC(random_state=42)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        # Train model
        model.fit(X_train, y_train)
        
        # Calculate metrics
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        
        train_accuracy = accuracy_score(y_train, train_pred)
        test_accuracy = accuracy_score(y_test, test_pred)
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        cv_mean = cv_scores.mean()
        cv_std = cv_scores.std()
        
        results = {
            'model': model,
            'train_accuracy': train_accuracy,
            'test_accuracy': test_accuracy,
            'cv_mean': cv_mean,
            'cv_std': cv_std,
            'classification_report': classification_report(y_test, test_pred, output_dict=True),
            'X_train': X_train,
            'X_test': X_test,
            'y_train': y_train,
            'y_test': y_test,
            'test_predictions': test_pred
        }
        
        return results
    
    def run_poisoning_experiment(self, model_types: List[str] = ['logistic_regression']):
        """
        Run comprehensive poisoning experiment with multiple datasets and models.
        """
        logger.info("Starting comprehensive data poisoning experiment")
        
        # Set up experiment
        self.setup_poisoning_experiment()
        
        # Load clean data
        X_train, X_test, y_train, y_test, X, y = self.load_data()
        
        # Create poisoned datasets
        datasets = self.create_poisoned_datasets(X, y)
        
        # Store all results
        experiment_results = {
            'timestamp': datetime.now().isoformat(),
            'datasets': {},
            'models': {},
            'detection_analysis': {},
            'performance_comparison': {},
            'mitigation_analysis': {}
        }
        
        # Train models on each dataset
        for dataset_name, dataset_info in datasets.items():
            logger.info(f"\n=== Analyzing {dataset_name} dataset ===")
            
            dataset_results = {
                'description': dataset_info['description'],
                'poison_rate': dataset_info['poison_rate'],
                'poisoned_indices': dataset_info['poisoned_indices'],
                'models': {},
                'detection_results': {},
                'detection_evaluation': {}
            }
            
            # Apply detection methods (for poisoned datasets)
            if dataset_name != 'clean':
                detection_results = self.detect_poisoning(
                    dataset_info['X'], dataset_info['poison_rate']
                )
                dataset_results['detection_results'] = detection_results
                
                # Evaluate detection accuracy
                detection_evaluation = self.evaluate_detection_accuracy(
                    detection_results, dataset_info['poisoned_indices']
                )
                dataset_results['detection_evaluation'] = detection_evaluation
            
            # Train models
            for model_type in model_types:
                with mlflow.start_run(run_name=f"{model_type}_{dataset_name}"):
                    # Train model
                    model_results = self.train_model_on_dataset(
                        dataset_info['X'], dataset_info['y'], model_type, dataset_name
                    )
                    
                    # Log to MLflow
                    mlflow.log_param("dataset_type", dataset_name)
                    mlflow.log_param("model_type", model_type)
                    mlflow.log_param("poison_rate", dataset_info['poison_rate'])
                    mlflow.log_param("data_shape", dataset_info['X'].shape)
                    
                    mlflow.log_metric("train_accuracy", model_results['train_accuracy'])
                    mlflow.log_metric("test_accuracy", model_results['test_accuracy'])
                    mlflow.log_metric("cv_mean", model_results['cv_mean'])
                    mlflow.log_metric("cv_std", model_results['cv_std'])
                    
                    # Log detection metrics (for poisoned datasets)
                    if dataset_name != 'clean' and 'detection_evaluation' in dataset_results:
                        for method, metrics in dataset_results['detection_evaluation'].items():
                            mlflow.log_metric(f"detection_{method}_precision", metrics['precision'])
                            mlflow.log_metric(f"detection_{method}_recall", metrics['recall'])
                            mlflow.log_metric(f"detection_{method}_f1", metrics['f1_score'])
                    
                    # Save model
                    signature = infer_signature(model_results['X_train'], model_results['test_predictions'])
                    mlflow.sklearn.log_model(
                        model_results['model'], 
                        "model",
                        signature=signature,
                        input_example=model_results['X_train'].iloc[:5]
                    )
                    
                    # Log classification report
                    mlflow.log_dict(model_results['classification_report'], 
                                   f"classification_report_{dataset_name}.json")
                    
                    # Store results
                    dataset_results['models'][model_type] = {
                        'train_accuracy': model_results['train_accuracy'],
                        'test_accuracy': model_results['test_accuracy'],
                        'cv_mean': model_results['cv_mean'],
                        'cv_std': model_results['cv_std'],
                        'mlflow_run_id': mlflow.active_run().info.run_id
                    }
            
            experiment_results['datasets'][dataset_name] = dataset_results
        
        # Performance comparison analysis
        experiment_results['performance_comparison'] = self.analyze_performance_impact(
            experiment_results, model_types
        )
        
        # Generate mitigation recommendations
        experiment_results['mitigation_analysis'] = self.generate_mitigation_recommendations(
            experiment_results
        )
        
        # Save comprehensive results
        results_file = os.path.join(self.results_dir, f"poisoning_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(results_file, 'w') as f:
            json.dump(experiment_results, f, indent=2, default=str)
        
        logger.info(f"Experiment results saved to {results_file}")
        
        # Generate summary report
        self.generate_summary_report(experiment_results)
        
        return experiment_results
    
    def analyze_performance_impact(self, experiment_results: Dict, model_types: List[str]) -> Dict:
        """
        Analyze the performance impact of poisoning across datasets and models.
        """
        logger.info("Analyzing performance impact of data poisoning")
        
        analysis = {
            'baseline_performance': {},
            'performance_degradation': {},
            'summary_statistics': {}
        }
        
        # Get baseline (clean) performance
        clean_results = experiment_results['datasets']['clean']
        for model_type in model_types:
            analysis['baseline_performance'][model_type] = clean_results['models'][model_type]
        
        # Calculate performance degradation
        for dataset_name, dataset_results in experiment_results['datasets'].items():
            if dataset_name == 'clean':
                continue
                
            poison_rate = dataset_results['poison_rate']
            analysis['performance_degradation'][dataset_name] = {
                'poison_rate': poison_rate,
                'models': {}
            }
            
            for model_type in model_types:
                clean_acc = clean_results['models'][model_type]['test_accuracy']
                poison_acc = dataset_results['models'][model_type]['test_accuracy']
                
                degradation = {
                    'absolute_drop': clean_acc - poison_acc,
                    'relative_drop': (clean_acc - poison_acc) / clean_acc * 100,
                    'clean_accuracy': clean_acc,
                    'poisoned_accuracy': poison_acc
                }
                
                analysis['performance_degradation'][dataset_name]['models'][model_type] = degradation
        
        # Summary statistics
        all_drops = []
        for dataset_name in analysis['performance_degradation']:
            for model_type in model_types:
                drop = analysis['performance_degradation'][dataset_name]['models'][model_type]['absolute_drop']
                all_drops.append(drop)
        
        if all_drops:
            analysis['summary_statistics'] = {
                'mean_performance_drop': np.mean(all_drops),
                'max_performance_drop': np.max(all_drops),
                'min_performance_drop': np.min(all_drops),
                'std_performance_drop': np.std(all_drops)
            }
        
        return analysis
    
    def generate_mitigation_recommendations(self, experiment_results: Dict) -> Dict:
        """
        Generate recommendations for mitigating data poisoning attacks.
        """
        logger.info("Generating mitigation recommendations")
        
        recommendations = {
            'detection_method_analysis': {},
            'data_validation_strategies': [],
            'model_robustness_techniques': [],
            'monitoring_recommendations': []
        }
        
        # Analyze detection method effectiveness
        detection_performance = {}
        for dataset_name, dataset_results in experiment_results['datasets'].items():
            if 'detection_evaluation' in dataset_results and dataset_results['detection_evaluation']:
                poison_rate = dataset_results['poison_rate']
                for method, metrics in dataset_results['detection_evaluation'].items():
                    if method not in detection_performance:
                        detection_performance[method] = []
                    detection_performance[method].append({
                        'poison_rate': poison_rate,
                        'f1_score': metrics['f1_score'],
                        'precision': metrics['precision'],
                        'recall': metrics['recall']
                    })
        
        recommendations['detection_method_analysis'] = detection_performance
        
        # Data validation strategies
        recommendations['data_validation_strategies'] = [
            "Implement statistical outlier detection using Z-score analysis (threshold: 2.5-3.0)",
            "Use Isolation Forest for anomaly detection with contamination rate based on expected threat level",
            "Establish data quality checks including feature range validation",
            "Implement cross-validation with multiple random seeds to detect inconsistencies",
            "Use ensemble methods for more robust predictions",
            "Maintain historical data distributions for comparison"
        ]
        
        # Model robustness techniques
        recommendations['model_robustness_techniques'] = [
            "Use regularization techniques (L1/L2) to reduce overfitting to poisoned samples",
            "Implement ensemble methods that can tolerate some poisoned training data",
            "Use robust loss functions that are less sensitive to outliers",
            "Apply data augmentation to increase training data diversity",
            "Implement adversarial training with known attack patterns",
            "Use cross-validation to detect unusual performance patterns"
        ]
        
        # Monitoring recommendations
        recommendations['monitoring_recommendations'] = [
            "Monitor model performance degradation in production",
            "Implement real-time outlier detection on incoming data",
            "Track data distribution shifts using statistical tests",
            "Set up alerts for unusual accuracy drops or prediction patterns",
            "Maintain separate validation sets that are known to be clean",
            "Regularly retrain models with fresh, validated data"
        ]
        
        return recommendations
    
    def generate_summary_report(self, experiment_results: Dict):
        """
        Generate a comprehensive summary report of the poisoning experiment.
        """
        logger.info("Generating summary report")
        
        report_file = os.path.join(self.results_dir, f"poisoning_summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        with open(report_file, 'w') as f:
            f.write("# Data Poisoning Analysis Report - Week 8 Assignment\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Executive Summary\n\n")
            f.write("This report presents the results of a comprehensive data poisoning analysis on the IRIS dataset, ")
            f.write("including the impact of various poisoning rates and effectiveness of detection methods.\n\n")
            
            # Dataset Analysis
            f.write("## Dataset Analysis\n\n")
            for dataset_name, dataset_info in experiment_results['datasets'].items():
                f.write(f"### {dataset_name.replace('_', ' ').title()}\n")
                f.write(f"- **Description:** {dataset_info['description']}\n")
                f.write(f"- **Poison Rate:** {dataset_info['poison_rate']*100:.1f}%\n")
                if dataset_info['poisoned_indices']:
                    f.write(f"- **Poisoned Samples:** {len(dataset_info['poisoned_indices'])}\n")
                f.write("\n")
            
            # Performance Impact
            f.write("## Performance Impact Analysis\n\n")
            if 'performance_comparison' in experiment_results:
                perf = experiment_results['performance_comparison']
                
                if 'summary_statistics' in perf and perf['summary_statistics']:
                    stats = perf['summary_statistics']
                    f.write("### Summary Statistics\n")
                    f.write(f"- **Mean Performance Drop:** {stats['mean_performance_drop']:.4f}\n")
                    f.write(f"- **Maximum Performance Drop:** {stats['max_performance_drop']:.4f}\n")
                    f.write(f"- **Minimum Performance Drop:** {stats['min_performance_drop']:.4f}\n")
                    f.write(f"- **Standard Deviation:** {stats['std_performance_drop']:.4f}\n\n")
                
                f.write("### Detailed Performance Degradation\n\n")
                for dataset_name, degradation in perf.get('performance_degradation', {}).items():
                    f.write(f"#### {dataset_name.replace('_', ' ').title()}\n")
                    f.write(f"**Poison Rate:** {degradation['poison_rate']*100:.1f}%\n\n")
                    
                    for model_type, metrics in degradation['models'].items():
                        f.write(f"- **{model_type.replace('_', ' ').title()}:**\n")
                        f.write(f"  - Clean Accuracy: {metrics['clean_accuracy']:.4f}\n")
                        f.write(f"  - Poisoned Accuracy: {metrics['poisoned_accuracy']:.4f}\n")
                        f.write(f"  - Absolute Drop: {metrics['absolute_drop']:.4f}\n")
                        f.write(f"  - Relative Drop: {metrics['relative_drop']:.1f}%\n\n")
            
            # Detection Analysis
            f.write("## Poisoning Detection Analysis\n\n")
            detection_summary = {}
            for dataset_name, dataset_info in experiment_results['datasets'].items():
                if 'detection_evaluation' in dataset_info and dataset_info['detection_evaluation']:
                    for method, metrics in dataset_info['detection_evaluation'].items():
                        if method not in detection_summary:
                            detection_summary[method] = []
                        detection_summary[method].append({
                            'dataset': dataset_name,
                            'poison_rate': dataset_info['poison_rate'],
                            **metrics
                        })
            
            for method, results in detection_summary.items():
                f.write(f"### {method.replace('_', ' ').title()} Detection\n\n")
                for result in results:
                    f.write(f"- **{result['dataset']} ({result['poison_rate']*100:.1f}% poisoned):**\n")
                    f.write(f"  - Precision: {result['precision']:.3f}\n")
                    f.write(f"  - Recall: {result['recall']:.3f}\n")
                    f.write(f"  - F1-Score: {result['f1_score']:.3f}\n\n")
            
            # Mitigation Recommendations
            f.write("## Mitigation Recommendations\n\n")
            if 'mitigation_analysis' in experiment_results:
                mitigation = experiment_results['mitigation_analysis']
                
                f.write("### Data Validation Strategies\n\n")
                for strategy in mitigation.get('data_validation_strategies', []):
                    f.write(f"- {strategy}\n")
                f.write("\n")
                
                f.write("### Model Robustness Techniques\n\n")
                for technique in mitigation.get('model_robustness_techniques', []):
                    f.write(f"- {technique}\n")
                f.write("\n")
                
                f.write("### Monitoring Recommendations\n\n")
                for recommendation in mitigation.get('monitoring_recommendations', []):
                    f.write(f"- {recommendation}\n")
                f.write("\n")
            
            # Conclusions
            f.write("## Key Findings and Conclusions\n\n")
            f.write("1. **Impact of Poisoning:** Data poisoning shows measurable impact on model performance, ")
            f.write("with higher poison rates leading to greater accuracy degradation.\n\n")
            
            f.write("2. **Detection Effectiveness:** Both Isolation Forest and statistical methods show promise ")
            f.write("for detecting poisoned samples, with varying effectiveness based on poison rate.\n\n")
            
            f.write("3. **Mitigation Strategies:** A combination of detection methods, robust training techniques, ")
            f.write("and continuous monitoring provides the best defense against data poisoning attacks.\n\n")
            
            f.write("4. **Recommendations:** Implement multi-layered defense including data validation, ")
            f.write("anomaly detection, and robust model training practices.\n\n")
        
        logger.info(f"Summary report generated: {report_file}")
        return report_file

def main():
    """
    Main function to run the comprehensive poisoning experiment.
    """
    pipeline = IrisPoisoningPipeline()
    
    # Run experiment with multiple models for comprehensive analysis
    model_types = ['logistic_regression', 'random_forest']  # Reduced for demo
    
    results = pipeline.run_poisoning_experiment(model_types)
    
    logger.info("="*60)
    logger.info("POISONING EXPERIMENT COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    
    return results

if __name__ == "__main__":
    main()