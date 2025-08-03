# Week 8 Assignment Demo Instructions

## Quick Start Guide

### For Immediate Demo (Recommended)

```bash
# Quick demo (5-10 minutes)
python3 week8_poisoning_demo.py --quick

# Full demo (15-20 minutes)
python3 week8_poisoning_demo.py
```

### Prerequisites

1. **Python Environment**: Python 3.8+ required
2. **Dependencies**: Install if needed:
   ```bash
   pip install -r requirements-poisoning.txt
   ```
3. **Data**: The IRIS dataset will be created automatically if not present

## Demo Options

### Option 1: Local Execution (Best for Live Demo)

**Advantages:**
- Immediate results and real-time feedback
- Interactive visual plots that can be shown
- Complete control over parameters
- Can pause and explain each step

**Commands:**
```bash
# Quick demo with default settings
python3 week8_poisoning_demo.py --quick

# Full analysis with all poison rates and models
python3 week8_poisoning_demo.py

# Custom parameters
python3 week8_poisoning_demo.py --models logistic_regression,random_forest --rates 0.05,0.10,0.50
```

### Option 2: GitHub Actions CI/CD

**Advantages:**
- Shows integration with MLOps pipeline
- Demonstrates scalability across environments
- Provides downloadable artifacts and reports
- Good for remote/asynchronous presentation

**How to Run:**
1. Go to GitHub repository → Actions tab
2. Select "Week 8 Data Poisoning Demo" workflow
3. Click "Run workflow"
4. Configure parameters:
   - Quick mode: `true` for fast demo
   - Poison rates: `0.05,0.10` for quick or `0.05,0.10,0.50` for full
   - Models: `logistic_regression` for quick or `logistic_regression,random_forest` for full

## What the Demo Shows

### 1. Data Poisoning Implementation
- **Feature Noise**: Random Gaussian noise injection
- **Label Flipping**: Random target label changes
- **Combined Attacks**: Realistic mixed poisoning scenarios
- **Configurable Rates**: 5%, 10%, 50% as per assignment requirements

### 2. Performance Impact Analysis
- **Model Training**: On clean vs. poisoned datasets
- **Performance Metrics**: Accuracy, cross-validation scores
- **Degradation Analysis**: Quantified impact measurement
- **Visual Analysis**: Performance plots and comparisons

### 3. Detection Methods
- **Isolation Forest**: Machine learning-based outlier detection
- **Statistical Methods**: Z-score based anomaly detection
- **Accuracy Evaluation**: Precision, recall, F1-score metrics
- **Method Comparison**: Best approach identification

### 4. Mitigation Strategies
- **Detection-Based**: Automated outlier identification
- **Model-Based**: Robust training techniques
- **Data-Based**: Quality assurance and validation
- **Monitoring-Based**: Production surveillance

## Expected Results

### Performance Impact (Typical Values)
| Poison Rate | Accuracy Drop | Relative Impact |
|-------------|---------------|-----------------|
| 5%          | 0.00-0.05     | 0-5%           |
| 10%         | 0.05-0.15     | 5-15%          |
| 50%         | 0.15-0.30     | 15-30%         |

### Detection Performance
- **Isolation Forest**: 60-80% F1-score depending on poison rate
- **Statistical Method**: 40-70% F1-score with threshold tuning
- **Combined Approach**: Best overall detection accuracy

## Files Generated

### Demo Results
```
week8_demo_results/
├── performance_analysis.png    # Visual performance comparison
└── week8_demo.log             # Detailed execution log
```

### Pipeline Results (if running full pipeline)
```
poisoning_results/
├── poisoning_experiment_YYYYMMDD_HHMMSS.json  # Detailed results
├── poisoning_summary_report_YYYYMMDD_HHMMSS.md # Summary report
└── *.png                                       # Additional visualizations
```

### MLflow Tracking
```
mlflow_tracking/
├── mlflow.db                  # Experiment database
└── artifacts/                 # Model artifacts and logs
```

## Key Talking Points for Demo

### 1. Problem Statement
- "Data poisoning is a critical security threat in ML pipelines"
- "Small amounts of poisoned data can significantly impact model performance"
- "We need both detection and mitigation strategies"

### 2. Technical Implementation
- "Combined poisoning attacks are more realistic than single-type attacks"
- "Detection methods have trade-offs between precision and recall"
- "Multiple defense layers provide better protection"

### 3. Results and Insights
- "Performance degradation scales with poison rate"
- "Some models are naturally more robust than others"
- "Early detection is crucial for maintaining model integrity"

### 4. Practical Recommendations
- "Implement automated data quality checks"
- "Use ensemble methods for natural robustness"
- "Monitor production performance continuously"

## Troubleshooting

### Common Issues

1. **Import Errors**:
   ```bash
   pip install -r requirements-poisoning.txt
   ```

2. **Python Command Not Found**:
   - Use `python3` instead of `python`
   - Ensure Python 3.8+ is installed

3. **Data Not Found**:
   - Script automatically creates IRIS dataset
   - Ensure write permissions in current directory

4. **MLflow Database Errors**:
   - Delete `mlflow_tracking/` directory and re-run
   - Check disk space availability

### Validation Test
```bash
# Run this to validate setup
python3 test_week8_setup.py
```

## Integration with Existing Pipeline

### Non-Disruptive Design
- Original `iris_pipeline.py` unchanged
- Original `iris_pipeline_mlflow.py` unchanged
- All existing tests continue to work
- New functionality is purely additive

### Extension Architecture
- `IrisPoisoningPipeline` extends `IrisMLflowPipeline`
- Modular design allows independent usage
- Compatible with existing MLflow setup

## Success Metrics

After running the demo, you should have:

- **Functional Implementation**: All poisoning types working  
- **Performance Analysis**: Clear impact demonstration  
- **Detection Methods**: Two working approaches with metrics  
- **Mitigation Strategies**: Practical recommendations  
- **Visual Results**: Performance plots and comparisons  
- **MLflow Integration**: Experiment tracking and logging  
- **Documentation**: Comprehensive analysis reports  

## Next Steps After Demo

1. **Review MLflow UI**:
   ```bash
   mlflow ui --backend-store-uri sqlite:///mlflow_tracking/mlflow.db
   ```

2. **Analyze Results**: Check generated reports and visualizations

3. **Implement Mitigation**: Apply recommended strategies to production

4. **Extend Analysis**: Try different models, poison rates, or detection methods

---

**Total Demo Time**: 5-10 minutes (quick) or 15-20 minutes (full)  
**Preparation Time**: < 5 minutes  
**Requirements**: Python 3.8+, basic ML libraries