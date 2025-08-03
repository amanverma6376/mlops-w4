#!/usr/bin/env python3
"""
Week 8 Assignment Demo Script - Data Poisoning Analysis for IRIS Dataset

This script demonstrates:
1. Data poisoning at various levels (5%, 10%, 50%)
2. Impact on model performance
3. Detection methods effectiveness
4. Mitigation strategies

Usage:
    python week8_poisoning_demo.py [--quick] [--models MODEL1,MODEL2] [--rates RATE1,RATE2]

Examples:
    python week8_poisoning_demo.py --quick
    python week8_poisoning_demo.py --models logistic_regression,random_forest
    python week8_poisoning_demo.py --rates 0.05,0.10,0.20,0.50
"""

import argparse
import logging
import sys
import os
import time
from typing import List, Dict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from iris_poisoning_pipeline import IrisPoisoningPipeline
from data_poisoning import DataPoisoning

# Set up logging with better formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('week8_demo.log')
    ]
)
logger = logging.getLogger(__name__)

class Week8PoisoningDemo:
    """
    Comprehensive demo class for Week 8 data poisoning assignment.
    """
    
    def __init__(self, quick_mode: bool = False):
        """
        Initialize the demo.
        
        Args:
            quick_mode (bool): If True, run with reduced parameters for faster execution
        """
        self.quick_mode = quick_mode
        self.pipeline = IrisPoisoningPipeline()
        self.results_dir = "week8_demo_results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Demo parameters
        if quick_mode:
            self.poison_rates = [0.05, 0.10]  # Reduced for quick demo
            self.model_types = ['logistic_regression']  # Single model for speed
            logger.info("Running in QUICK MODE - reduced parameters for faster execution")
        else:
            self.poison_rates = [0.05, 0.10, 0.50]  # Full set as per assignment
            self.model_types = ['logistic_regression', 'random_forest']
            logger.info("Running in FULL MODE - comprehensive analysis")
    
    def set_custom_parameters(self, poison_rates: List[float] = None, 
                            model_types: List[str] = None):
        """Set custom parameters for the demo."""
        if poison_rates:
            self.poison_rates = poison_rates
            self.pipeline.poison_rates = poison_rates
        if model_types:
            self.model_types = model_types
        
        logger.info(f"Custom parameters set - Poison rates: {self.poison_rates}, Models: {self.model_types}")
    
    def display_intro(self):
        """Display introduction and overview."""
        print("\n" + "="*80)
        print("WEEK 8 ASSIGNMENT: DATA POISONING ANALYSIS FOR IRIS DATASET")
        print("="*80)
        print("""
This demo demonstrates:
- Data poisoning techniques at multiple levels
- Performance impact analysis on ML models  
- Poisoning detection methods
- Mitigation strategies and recommendations

Configuration:
""")
        print(f"Poison Rates: {[f'{r*100:.0f}%' for r in self.poison_rates]}")
        print(f"Models: {[m.replace('_', ' ').title() for m in self.model_types]}")
        print(f"Mode: {'Quick Demo' if self.quick_mode else 'Full Analysis'}")
        print("\n" + "="*80 + "\n")
    
    def create_and_analyze_datasets(self) -> Dict:
        """Create poisoned datasets and perform initial analysis."""
        logger.info("Step 1: Creating and analyzing poisoned datasets")
        print("STEP 1: Creating Poisoned Datasets")
        print("-" * 50)
        
        # Load clean data
        df = pd.read_csv("data/iris.csv")
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        print(f"Original dataset shape: {X.shape}")
        print(f"Target classes: {y.unique()}")
        
        # Create poisoned datasets
        datasets = {}
        poisoner = DataPoisoning(random_state=42)
        
        # Clean dataset
        datasets['clean'] = {
            'X': X.copy(),
            'y': y.copy(),
            'poisoned_indices': [],
            'poison_rate': 0.0,
            'description': 'Original clean dataset'
        }
        
        print(f"\nClean dataset: {len(X)} samples")
        
        # Poisoned datasets
        for rate in self.poison_rates:
            print(f"\nCreating {rate*100:.0f}% poisoned dataset...")
            
            X_poison, y_poison, poison_indices = poisoner.combined_poisoning(X, y, rate)
            
            datasets[f'{int(rate*100)}%_poisoned'] = {
                'X': X_poison,
                'y': y_poison,
                'poisoned_indices': poison_indices,
                'poison_rate': rate,
                'description': f'Dataset with {rate*100:.0f}% combined poisoning'
            }
            
            print(f"   Poisoned {len(poison_indices)} samples")
            print(f"   Feature noise + label flipping applied")
            
            # Show sample of poisoned data
            if len(poison_indices) > 0:
                sample_idx = poison_indices[0]
                print(f"   Sample poisoned index {sample_idx}:")
                print(f"      Original: {X.iloc[sample_idx].values}")
                print(f"      Poisoned: {X_poison.iloc[sample_idx].values}")
        
        return datasets
    
    def demonstrate_detection_methods(self, datasets: Dict):
        """Demonstrate poisoning detection methods."""
        logger.info("Step 2: Demonstrating detection methods")
        print("\nSTEP 2: Poisoning Detection Methods")
        print("-" * 50)
        
        poisoner = DataPoisoning(random_state=42)
        
        for dataset_name, dataset_info in datasets.items():
            if dataset_name == 'clean':
                continue
                
            print(f"\nAnalyzing {dataset_name} dataset:")
            
            X_poison = dataset_info['X']
            true_indices = set(dataset_info['poisoned_indices'])
            poison_rate = dataset_info['poison_rate']
            
            # Isolation Forest Detection
            print(f"   Isolation Forest Detection:")
            outliers_iso = poisoner.detect_outliers_isolation_forest(
                X_poison, contamination=poison_rate
            )
            detected_iso = set(np.where(outliers_iso)[0])
            
            # Calculate metrics
            tp_iso = len(detected_iso & true_indices)
            fp_iso = len(detected_iso - true_indices)
            fn_iso = len(true_indices - detected_iso)
            
            precision_iso = tp_iso / len(detected_iso) if len(detected_iso) > 0 else 0
            recall_iso = tp_iso / len(true_indices) if len(true_indices) > 0 else 0
            f1_iso = 2 * (precision_iso * recall_iso) / (precision_iso + recall_iso) if (precision_iso + recall_iso) > 0 else 0
            
            print(f"      Detected: {len(detected_iso)} samples")
            print(f"      Precision: {precision_iso:.3f} | Recall: {recall_iso:.3f} | F1: {f1_iso:.3f}")
            
            # Statistical Detection
            print(f"   Statistical Z-Score Detection:")
            outliers_stat = poisoner.statistical_detection(X_poison, threshold=2.5)
            detected_stat = set(np.where(outliers_stat)[0])
            
            tp_stat = len(detected_stat & true_indices)
            fp_stat = len(detected_stat - true_indices)
            fn_stat = len(true_indices - detected_stat)
            
            precision_stat = tp_stat / len(detected_stat) if len(detected_stat) > 0 else 0
            recall_stat = tp_stat / len(true_indices) if len(true_indices) > 0 else 0
            f1_stat = 2 * (precision_stat * recall_stat) / (precision_stat + recall_stat) if (precision_stat + recall_stat) > 0 else 0
            
            print(f"      Detected: {len(detected_stat)} samples")
            print(f"      Precision: {precision_stat:.3f} | Recall: {recall_stat:.3f} | F1: {f1_stat:.3f}")
            
            # Summary
            better_method = "Isolation Forest" if f1_iso > f1_stat else "Statistical"
            print(f"   Better method for {dataset_name}: {better_method}")
    
    def analyze_performance_impact(self, datasets: Dict) -> Dict:
        """Analyze the impact of poisoning on model performance."""
        logger.info("Step 3: Analyzing performance impact")
        print("\nSTEP 3: Performance Impact Analysis")
        print("-" * 50)
        
        performance_results = {}
        
        for model_type in self.model_types:
            print(f"\nAnalyzing {model_type.replace('_', ' ').title()} Model:")
            model_results = {}
            
            for dataset_name, dataset_info in datasets.items():
                print(f"   Training on {dataset_name}...")
                
                # Train model
                result = self.pipeline.train_model_on_dataset(
                    dataset_info['X'], dataset_info['y'], model_type, dataset_name
                )
                
                model_results[dataset_name] = {
                    'test_accuracy': result['test_accuracy'],
                    'train_accuracy': result['train_accuracy'],
                    'cv_mean': result['cv_mean'],
                    'poison_rate': dataset_info['poison_rate']
                }
                
                print(f"      Test Accuracy: {result['test_accuracy']:.4f}")
                print(f"      Train Accuracy: {result['train_accuracy']:.4f}")
                print(f"      CV Score: {result['cv_mean']:.4f} ± {result['cv_std']:.4f}")
            
            performance_results[model_type] = model_results
            
            # Calculate performance degradation
            clean_acc = model_results['clean']['test_accuracy']
            print(f"\n   Performance Degradation Analysis:")
            print(f"      Baseline (Clean): {clean_acc:.4f}")
            
            for dataset_name, result in model_results.items():
                if dataset_name == 'clean':
                    continue
                    
                poison_acc = result['test_accuracy']
                absolute_drop = clean_acc - poison_acc
                relative_drop = (absolute_drop / clean_acc) * 100
                
                print(f"      {dataset_name}: {poison_acc:.4f} "
                      f"(↓{absolute_drop:.4f}, {relative_drop:.1f}%)")
        
        return performance_results
    
    def generate_visual_analysis(self, performance_results: Dict):
        """Generate visual analysis of the results."""
        logger.info("Step 4: Generating visual analysis")
        print("\nSTEP 4: Generating Visual Analysis")
        print("-" * 50)
        
        try:
            # Prepare data for visualization
            plot_data = []
            for model_type, model_results in performance_results.items():
                for dataset_name, result in model_results.items():
                    plot_data.append({
                        'Model': model_type.replace('_', ' ').title(),
                        'Dataset': dataset_name.replace('_poisoned', '').replace('_', ' ').title(),
                        'Poison_Rate': result['poison_rate'] * 100,
                        'Test_Accuracy': result['test_accuracy'],
                        'Train_Accuracy': result['train_accuracy']
                    })
            
            df_plot = pd.DataFrame(plot_data)
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            
            # Performance vs Poison Rate
            plt.subplot(2, 2, 1)
            for model_type in self.model_types:
                model_data = df_plot[df_plot['Model'] == model_type.replace('_', ' ').title()]
                plt.plot(model_data['Poison_Rate'], model_data['Test_Accuracy'], 
                        marker='o', label=model_type.replace('_', ' ').title())
            
            plt.xlabel('Poison Rate (%)')
            plt.ylabel('Test Accuracy')
            plt.title('Model Performance vs Poison Rate')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Performance comparison bar plot
            plt.subplot(2, 2, 2)
            sns.barplot(data=df_plot, x='Dataset', y='Test_Accuracy', hue='Model')
            plt.title('Test Accuracy by Dataset')
            plt.xticks(rotation=45)
            
            # Train vs Test accuracy
            plt.subplot(2, 2, 3)
            plt.scatter(df_plot['Train_Accuracy'], df_plot['Test_Accuracy'], 
                       c=df_plot['Poison_Rate'], cmap='Reds', s=100)
            plt.xlabel('Train Accuracy')
            plt.ylabel('Test Accuracy')
            plt.title('Train vs Test Accuracy (colored by poison rate)')
            plt.colorbar(label='Poison Rate (%)')
            
            # Performance degradation
            plt.subplot(2, 2, 4)
            degradation_data = []
            for model_type in self.model_types:
                model_data = df_plot[df_plot['Model'] == model_type.replace('_', ' ').title()]
                clean_acc = model_data[model_data['Poison_Rate'] == 0]['Test_Accuracy'].iloc[0]
                
                for _, row in model_data.iterrows():
                    if row['Poison_Rate'] > 0:
                        degradation = clean_acc - row['Test_Accuracy']
                        degradation_data.append({
                            'Model': row['Model'],
                            'Poison_Rate': row['Poison_Rate'],
                            'Performance_Drop': degradation
                        })
            
            if degradation_data:
                deg_df = pd.DataFrame(degradation_data)
                sns.barplot(data=deg_df, x='Poison_Rate', y='Performance_Drop', hue='Model')
                plt.title('Performance Degradation by Poison Rate')
                plt.ylabel('Accuracy Drop')
            
            plt.tight_layout()
            
            # Save plot
            plot_file = os.path.join(self.results_dir, 'performance_analysis.png')
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            print(f"Performance analysis plot saved: {plot_file}")
            
            if not self.quick_mode:
                plt.show()
            
        except Exception as e:
            logger.warning(f"Could not generate visual analysis: {e}")
            print(f"Visual analysis skipped: {e}")
    
    def demonstrate_mitigation_strategies(self):
        """Demonstrate mitigation strategies."""
        logger.info("Step 5: Demonstrating mitigation strategies")
        print("\nSTEP 5: Mitigation Strategies")
        print("-" * 50)
        
        strategies = [
            "Detection-Based Mitigation:",
            "   - Use Isolation Forest for outlier detection",
            "   - Apply statistical Z-score analysis (threshold: 2.5-3.0)",
            "   - Monitor data distribution shifts",
            "",
            "Model-Based Mitigation:",
            "   - Use ensemble methods for robust predictions",
            "   - Apply regularization (L1/L2) to reduce overfitting",
            "   - Implement cross-validation with multiple seeds",
            "",
            "Data-Based Mitigation:",
            "   - Maintain clean validation sets",
            "   - Implement data quality checks",
            "   - Use data augmentation for diversity",
            "",
            "Monitoring-Based Mitigation:",
            "   - Track model performance in production",
            "   - Set up alerts for accuracy drops",
            "   - Regular model retraining with fresh data"
        ]
        
        for strategy in strategies:
            print(strategy)
        
        print(f"\nKey Recommendation:")
        print(f"   Implement a multi-layered defense combining detection,")
        print(f"   robust training, and continuous monitoring for best protection.")
    
    def run_comprehensive_demo(self):
        """Run the complete demonstration."""
        start_time = time.time()
        
        try:
            # Introduction
            self.display_intro()
            
            # Step 1: Create and analyze datasets
            datasets = self.create_and_analyze_datasets()
            
            # Step 2: Demonstrate detection methods
            self.demonstrate_detection_methods(datasets)
            
            # Step 3: Analyze performance impact
            performance_results = self.analyze_performance_impact(datasets)
            
            # Step 4: Generate visual analysis
            self.generate_visual_analysis(performance_results)
            
            # Step 5: Demonstrate mitigation strategies
            self.demonstrate_mitigation_strategies()
            
            # Summary
            execution_time = time.time() - start_time
            print("\n" + "="*80)
            print("WEEK 8 ASSIGNMENT DEMO COMPLETED SUCCESSFULLY!")
            print("="*80)
            print(f"Total execution time: {execution_time:.1f} seconds")
            print(f"Results saved in: {self.results_dir}/")
            print(f"MLflow tracking: ./mlflow_tracking/")
            print("\nKey Findings:")
            
            # Calculate summary statistics
            all_drops = []
            for model_type, model_results in performance_results.items():
                clean_acc = model_results['clean']['test_accuracy']
                for dataset_name, result in model_results.items():
                    if dataset_name != 'clean':
                        drop = clean_acc - result['test_accuracy']
                        all_drops.append(drop)
            
            if all_drops:
                print(f"   - Average performance drop: {np.mean(all_drops):.4f}")
                print(f"   - Maximum performance drop: {np.max(all_drops):.4f}")
                print(f"   - Poison rates tested: {[f'{r*100:.0f}%' for r in self.poison_rates]}")
            
            print(f"\nNext Steps:")
            print(f"   1. Review MLflow experiments for detailed metrics")
            print(f"   2. Analyze generated performance plots")
            print(f"   3. Implement recommended mitigation strategies")
            print("\n" + "="*80 + "\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            print(f"\nDemo failed: {e}")
            return False

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Week 8 Data Poisoning Demo for IRIS Dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python week8_poisoning_demo.py --quick
  python week8_poisoning_demo.py --models logistic_regression,random_forest
  python week8_poisoning_demo.py --rates 0.05,0.10,0.20,0.50
        """
    )
    
    parser.add_argument('--quick', action='store_true',
                       help='Run in quick mode with reduced parameters')
    parser.add_argument('--models', type=str,
                       help='Comma-separated list of models (logistic_regression,random_forest,svm)')
    parser.add_argument('--rates', type=str,
                       help='Comma-separated list of poison rates (e.g., 0.05,0.10,0.50)')
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = Week8PoisoningDemo(quick_mode=args.quick)
    
    # Set custom parameters if provided
    if args.models:
        model_types = [m.strip() for m in args.models.split(',')]
        valid_models = ['logistic_regression', 'random_forest', 'svm']
        model_types = [m for m in model_types if m in valid_models]
        if not model_types:
            print(f"No valid models specified. Valid options: {valid_models}")
            sys.exit(1)
    else:
        model_types = None
    
    if args.rates:
        try:
            poison_rates = [float(r.strip()) for r in args.rates.split(',')]
            poison_rates = [r for r in poison_rates if 0 < r <= 1.0]
            if not poison_rates:
                print("No valid poison rates specified. Rates should be between 0 and 1.")
                sys.exit(1)
        except ValueError:
            print("Invalid poison rates format. Use decimal values like 0.05,0.10,0.50")
            sys.exit(1)
    else:
        poison_rates = None
    
    # Apply custom parameters
    if model_types or poison_rates:
        demo.set_custom_parameters(poison_rates=poison_rates, model_types=model_types)
    
    # Run demo
    success = demo.run_comprehensive_demo()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()