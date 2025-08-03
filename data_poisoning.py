"""
Data Poisoning Module for IRIS Dataset - Week 8 Assignment
This module implements various data poisoning techniques and detection methods.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, List
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, classification_report
import warnings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPoisoning:
    """
    Class to implement various data poisoning attacks and detection methods.
    """
    
    def __init__(self, random_state: int = 42):
        """
        Initialize the DataPoisoning class.
        
        Args:
            random_state (int): Random state for reproducibility
        """
        self.random_state = random_state
        np.random.seed(random_state)
        
    def random_noise_poisoning(self, X: pd.DataFrame, y: pd.Series, 
                              poison_rate: float) -> Tuple[pd.DataFrame, pd.Series, List[int]]:
        """
        Inject random noise into feature values at specified poison rate.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target labels
            poison_rate (float): Percentage of data to poison (0.0 to 1.0)
            
        Returns:
            Tuple of (poisoned_X, original_y, poisoned_indices)
        """
        logger.info(f"Applying random noise poisoning at {poison_rate*100}% rate")
        
        X_poisoned = X.copy()
        n_samples = len(X)
        n_poison = int(n_samples * poison_rate)
        
        # Randomly select indices to poison
        poison_indices = np.random.choice(n_samples, n_poison, replace=False)
        
        # For each feature, add random noise scaled to the feature's range
        for col in X.columns:
            feature_min, feature_max = X[col].min(), X[col].max()
            feature_range = feature_max - feature_min
            
            # Add noise scaled to 20-50% of the feature range
            noise_scale = np.random.uniform(0.2, 0.5) * feature_range
            noise = np.random.normal(0, noise_scale, n_poison)
            
            X_poisoned.iloc[poison_indices, X.columns.get_loc(col)] += noise
        
        logger.info(f"Poisoned {n_poison} samples out of {n_samples} total samples")
        return X_poisoned, y.copy(), poison_indices.tolist()
    
    def label_flipping_poisoning(self, X: pd.DataFrame, y: pd.Series, 
                                poison_rate: float) -> Tuple[pd.DataFrame, pd.Series, List[int]]:
        """
        Flip labels randomly at specified poison rate.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target labels
            poison_rate (float): Percentage of labels to flip (0.0 to 1.0)
            
        Returns:
            Tuple of (original_X, poisoned_y, poisoned_indices)
        """
        logger.info(f"Applying label flipping poisoning at {poison_rate*100}% rate")
        
        y_poisoned = y.copy()
        n_samples = len(y)
        n_poison = int(n_samples * poison_rate)
        
        # Randomly select indices to poison
        poison_indices = np.random.choice(n_samples, n_poison, replace=False)
        
        # Get unique labels for flipping
        unique_labels = y.unique()
        
        # Flip labels randomly
        for idx in poison_indices:
            current_label = y_poisoned.iloc[idx]
            # Choose a different label randomly
            possible_labels = [label for label in unique_labels if label != current_label]
            y_poisoned.iloc[idx] = np.random.choice(possible_labels)
        
        logger.info(f"Flipped {n_poison} labels out of {n_samples} total samples")
        return X.copy(), y_poisoned, poison_indices.tolist()
    
    def combined_poisoning(self, X: pd.DataFrame, y: pd.Series, 
                          poison_rate: float, noise_ratio: float = 0.7) -> Tuple[pd.DataFrame, pd.Series, List[int]]:
        """
        Apply both feature noise and label flipping poisoning.
        
        Args:
            X (pd.DataFrame): Feature matrix
            y (pd.Series): Target labels
            poison_rate (float): Total percentage of data to poison (0.0 to 1.0)
            noise_ratio (float): Ratio of poisoning to apply as noise vs label flipping
            
        Returns:
            Tuple of (poisoned_X, poisoned_y, poisoned_indices)
        """
        logger.info(f"Applying combined poisoning at {poison_rate*100}% rate "
                   f"({noise_ratio*100}% noise, {(1-noise_ratio)*100}% label flipping)")
        
        n_samples = len(X)
        n_poison = int(n_samples * poison_rate)
        n_noise = int(n_poison * noise_ratio)
        n_flip = n_poison - n_noise
        
        # Randomly select indices for each type of poisoning
        all_indices = np.arange(n_samples)
        np.random.shuffle(all_indices)
        
        noise_indices = all_indices[:n_noise]
        flip_indices = all_indices[n_noise:n_noise + n_flip]
        
        X_poisoned = X.copy()
        y_poisoned = y.copy()
        
        # Apply noise poisoning
        if n_noise > 0:
            for col in X.columns:
                feature_min, feature_max = X[col].min(), X[col].max()
                feature_range = feature_max - feature_min
                noise_scale = np.random.uniform(0.2, 0.5) * feature_range
                noise = np.random.normal(0, noise_scale, n_noise)
                X_poisoned.iloc[noise_indices, X.columns.get_loc(col)] += noise
        
        # Apply label flipping
        if n_flip > 0:
            unique_labels = y.unique()
            for idx in flip_indices:
                current_label = y_poisoned.iloc[idx]
                possible_labels = [label for label in unique_labels if label != current_label]
                y_poisoned.iloc[idx] = np.random.choice(possible_labels)
        
        all_poisoned_indices = np.concatenate([noise_indices, flip_indices]).tolist()
        
        logger.info(f"Applied noise to {n_noise} samples and label flipping to {n_flip} samples")
        return X_poisoned, y_poisoned, all_poisoned_indices
    
    def detect_outliers_isolation_forest(self, X: pd.DataFrame, 
                                       contamination: float = 0.1) -> np.ndarray:
        """
        Detect potential poisoned samples using Isolation Forest.
        
        Args:
            X (pd.DataFrame): Feature matrix
            contamination (float): Expected proportion of outliers
            
        Returns:
            np.ndarray: Boolean mask of detected outliers (True = outlier/potentially poisoned)
        """
        logger.info(f"Detecting outliers using Isolation Forest with contamination={contamination}")
        
        # Standardize features for better outlier detection
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Apply Isolation Forest
        iso_forest = IsolationForest(contamination=contamination, random_state=self.random_state)
        outlier_predictions = iso_forest.fit_predict(X_scaled)
        
        # Convert to boolean mask (True = outlier)
        outlier_mask = outlier_predictions == -1
        
        logger.info(f"Detected {np.sum(outlier_mask)} potential outliers out of {len(X)} samples")
        return outlier_mask
    
    def statistical_detection(self, X: pd.DataFrame, threshold: float = 3.0) -> np.ndarray:
        """
        Detect outliers using statistical methods (Z-score).
        
        Args:
            X (pd.DataFrame): Feature matrix
            threshold (float): Z-score threshold for outlier detection
            
        Returns:
            np.ndarray: Boolean mask of detected outliers
        """
        logger.info(f"Detecting outliers using Z-score with threshold={threshold}")
        
        # Calculate Z-scores for each feature
        z_scores = np.abs((X - X.mean()) / X.std())
        
        # Mark samples as outliers if any feature has Z-score > threshold
        outlier_mask = (z_scores > threshold).any(axis=1)
        
        logger.info(f"Detected {np.sum(outlier_mask)} potential outliers using Z-score method")
        return outlier_mask
    
    def evaluate_poisoning_impact(self, clean_X: pd.DataFrame, clean_y: pd.Series,
                                 poisoned_X: pd.DataFrame, poisoned_y: pd.Series,
                                 model_class, **model_kwargs) -> Dict:
        """
        Evaluate the impact of poisoning on model performance.
        
        Args:
            clean_X, clean_y: Clean dataset
            poisoned_X, poisoned_y: Poisoned dataset
            model_class: Model class to train
            **model_kwargs: Model parameters
            
        Returns:
            Dict: Performance comparison results
        """
        logger.info("Evaluating poisoning impact on model performance")
        
        results = {}
        
        # Split both datasets
        X_clean_train, X_clean_test, y_clean_train, y_clean_test = train_test_split(
            clean_X, clean_y, test_size=0.2, random_state=self.random_state, stratify=clean_y
        )
        
        X_poison_train, X_poison_test, y_poison_train, y_poison_test = train_test_split(
            poisoned_X, poisoned_y, test_size=0.2, random_state=self.random_state, 
            stratify=poisoned_y
        )
        
        # Train on clean data
        clean_model = model_class(**model_kwargs)
        clean_model.fit(X_clean_train, y_clean_train)
        
        clean_train_acc = accuracy_score(y_clean_train, clean_model.predict(X_clean_train))
        clean_test_acc = accuracy_score(y_clean_test, clean_model.predict(X_clean_test))
        
        # Train on poisoned data
        poison_model = model_class(**model_kwargs)
        poison_model.fit(X_poison_train, y_poison_train)
        
        poison_train_acc = accuracy_score(y_poison_train, poison_model.predict(X_poison_train))
        poison_test_acc = accuracy_score(y_poison_test, poison_model.predict(X_poison_test))
        
        # Cross-evaluation: poisoned model on clean data
        poison_on_clean_acc = accuracy_score(y_clean_test, poison_model.predict(X_clean_test))
        
        results = {
            'clean_model': {
                'train_accuracy': clean_train_acc,
                'test_accuracy': clean_test_acc,
                'model': clean_model
            },
            'poisoned_model': {
                'train_accuracy': poison_train_acc,
                'test_accuracy': poison_test_acc,
                'test_on_clean_data': poison_on_clean_acc,
                'model': poison_model
            },
            'performance_drop': {
                'train_accuracy_drop': clean_train_acc - poison_train_acc,
                'test_accuracy_drop': clean_test_acc - poison_test_acc,
                'clean_data_accuracy_drop': clean_test_acc - poison_on_clean_acc
            }
        }
        
        logger.info(f"Clean model test accuracy: {clean_test_acc:.4f}")
        logger.info(f"Poisoned model test accuracy: {poison_test_acc:.4f}")
        logger.info(f"Poisoned model on clean data: {poison_on_clean_acc:.4f}")
        logger.info(f"Performance drop: {clean_test_acc - poison_test_acc:.4f}")
        
        return results
    
    def create_poisoned_datasets(self, X: pd.DataFrame, y: pd.Series, 
                               poison_rates: List[float]) -> Dict:
        """
        Create multiple poisoned datasets with different poison rates.
        
        Args:
            X (pd.DataFrame): Clean feature matrix
            y (pd.Series): Clean target labels
            poison_rates (List[float]): List of poison rates to apply
            
        Returns:
            Dict: Dictionary containing poisoned datasets for each rate
        """
        logger.info(f"Creating poisoned datasets for rates: {[f'{r*100}%' for r in poison_rates]}")
        
        datasets = {'clean': {'X': X.copy(), 'y': y.copy(), 'poisoned_indices': []}}
        
        for rate in poison_rates:
            logger.info(f"\n--- Creating {rate*100}% poisoned dataset ---")
            
            # Use combined poisoning for more realistic attack
            X_poison, y_poison, poison_indices = self.combined_poisoning(X, y, rate)
            
            datasets[f'{int(rate*100)}%'] = {
                'X': X_poison,
                'y': y_poison,
                'poisoned_indices': poison_indices,
                'poison_rate': rate
            }
        
        return datasets

def main():
    """
    Main function to demonstrate data poisoning capabilities.
    """
    # Load clean IRIS dataset
    logger.info("Loading clean IRIS dataset")
    df = pd.read_csv("data/iris.csv")
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    
    # Initialize poisoning module
    poisoner = DataPoisoning(random_state=42)
    
    # Create poisoned datasets at different rates
    poison_rates = [0.05, 0.10, 0.50]  # 5%, 10%, 50%
    datasets = poisoner.create_poisoned_datasets(X, y, poison_rates)
    
    # Demonstrate outlier detection
    logger.info("\n--- Demonstrating Outlier Detection ---")
    for rate_name, data in datasets.items():
        if rate_name == 'clean':
            continue
            
        logger.info(f"\nAnalyzing {rate_name} poisoned dataset:")
        
        # Isolation Forest detection
        outliers_iso = poisoner.detect_outliers_isolation_forest(
            data['X'], contamination=data['poison_rate']
        )
        
        # Statistical detection
        outliers_stat = poisoner.statistical_detection(data['X'], threshold=2.5)
        
        # Calculate detection accuracy
        true_positives_iso = len(set(data['poisoned_indices']) & set(np.where(outliers_iso)[0]))
        true_positives_stat = len(set(data['poisoned_indices']) & set(np.where(outliers_stat)[0]))
        
        precision_iso = true_positives_iso / np.sum(outliers_iso) if np.sum(outliers_iso) > 0 else 0
        recall_iso = true_positives_iso / len(data['poisoned_indices']) if len(data['poisoned_indices']) > 0 else 0
        
        precision_stat = true_positives_stat / np.sum(outliers_stat) if np.sum(outliers_stat) > 0 else 0
        recall_stat = true_positives_stat / len(data['poisoned_indices']) if len(data['poisoned_indices']) > 0 else 0
        
        logger.info(f"Isolation Forest - Precision: {precision_iso:.3f}, Recall: {recall_iso:.3f}")
        logger.info(f"Statistical Method - Precision: {precision_stat:.3f}, Recall: {recall_stat:.3f}")

if __name__ == "__main__":
    main()