# IRIS Fairness and Explainability Analysis Guide

## Overview

This guide explains how to use the automated fairness and explainability analysis for the IRIS dataset, which includes:

- **Dataset Enhancement**: Adds random location attribute for bias analysis
- **Fairness Analysis**: Uses fairlearn to detect bias between location groups
- **Explainability**: Uses SHAP to explain virginica class predictions
- **Automated CI/CD**: Integrated GitHub Actions workflow

## Quick Start

### Local Execution

```bash
# Install dependencies
pip install -r requirements-fairness.txt

# Run the complete analysis
python iris_fairness_analysis.py
```

Results will be saved in `fairness_results/` directory.

### GitHub Actions Workflow

The analysis can be run automatically via GitHub Actions:

1. **Go to Actions tab** in your GitHub repository
2. **Select "IRIS Fairness and Explainability Analysis"**
3. **Click "Run workflow"**
4. **Configure options** (optional):
   - Random seed for reproducibility
   - Models to analyze
   - Enable/disable plot generation
   - Skip SHAP analysis for faster execution

## Workflow Configuration

The GitHub Actions workflow supports these inputs:

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `random_seed` | Random seed for reproducible results | `42` | `123` |
| `models` | Models to analyze (comma-separated) | `logistic_regression,random_forest` | `logistic_regression` |
| `generate_plots` | Generate SHAP and fairness plots | `true` | `false` |
| `skip_shap` | Skip SHAP analysis (faster execution) | `false` | `true` |

## Triggers

The workflow runs automatically on:

- **Manual trigger**: Via GitHub Actions UI
- **Push to `fairness-analysis` branch**
- **Pull requests** affecting fairness-related files

## Generated Artifacts

### 1. Enhanced Dataset
- `data/iris_with_location.csv` - Original IRIS data + location attribute

### 2. Fairness Analysis
- `fairness_results/fairness_metrics_*.png` - Fairness visualizations by model
- `fairness_results/analysis_report.md` - Comprehensive analysis report

### 3. SHAP Explainability
- `fairness_results/shap_summary_virginica.png` - SHAP summary plot
- `fairness_results/shap_importance_virginica.png` - Feature importance
- `fairness_results/shap_force_plot_sample_*.png` - Individual explanations
- `fairness_results/shap_explanation.txt` - Simple explanations

### 4. Reports
- `FAIRNESS_ANALYSIS_SUMMARY.md` - GitHub Actions summary report

## Understanding the Results

### Fairness Metrics

- **Demographic Parity Difference**: Measures selection rate difference between groups
  - `< 0.1`: Good (low bias)
  - `≥ 0.1`: Concern (notable bias)

- **Equalized Odds Difference**: Measures error rate difference between groups
  - `< 0.1`: Good (similar error rates)
  - `≥ 0.1`: Concern (different error rates)

### SHAP Plots

- **Summary Plot**: Shows feature importance and impact direction
  - Red dots (high values) → push toward virginica
  - Blue dots (low values) → push away from virginica

- **Importance Plot**: Ranking of features by average importance
  - Longer bars = more important for virginica classification

- **Force Plots**: Individual prediction explanations
  - Shows how each feature contributes to specific predictions

## Integration with Existing Pipeline

The fairness analysis integrates seamlessly with your existing MLOps pipeline:

1. **Non-destructive**: Doesn't modify existing code or data
2. **Parallel execution**: Runs alongside existing workflows
3. **Artifact separation**: Results saved in dedicated directory
4. **Independent dependencies**: Uses separate requirements file

## Best Practices

1. **Reproducibility**: Use fixed random seeds for consistent results
2. **Documentation**: Check generated explanations for interpretability
3. **Monitoring**: Run analysis regularly to detect bias drift
4. **Integration**: Include fairness checks in your CI/CD pipeline

## Troubleshooting

### Common Issues

1. **SHAP plots fail**: Set `skip_shap: true` for faster execution
2. **Memory issues**: Reduce model complexity or dataset size
3. **Plot generation errors**: Set `generate_plots: false`

### Getting Help

- Check workflow logs in GitHub Actions
- Review generated reports in `fairness_results/`
- Examine error messages in CI/CD pipeline

## Next Steps

- **Customize thresholds**: Adjust fairness thresholds for your use case
- **Add more sensitive attributes**: Extend analysis to other demographic features
- **Integrate with monitoring**: Set up alerts for fairness violations
- **Automate actions**: Trigger model retraining when bias is detected

## Files Structure

```
.
├── iris_fairness_analysis.py          # Main analysis script
├── requirements-fairness.txt          # Fairness-specific dependencies
├── .github/workflows/fairness_analysis.yml  # GitHub Actions workflow
├── fairness_results/                  # Generated analysis outputs (gitignored)
│   ├── analysis_report.md             # Main report
│   ├── shap_explanation.txt           # SHAP explanations
│   ├── *.png                         # Visualizations
│   └── ...
└── data/
    ├── iris.csv                      # Original dataset
    └── iris_with_location.csv        # Enhanced dataset (generated)
```

This fairness analysis ensures responsible AI deployment with transparency, accountability, and bias monitoring! 🎯
