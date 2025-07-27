# MLOps Concurrent Inference Pipeline

## Project Structure

```
├── scripts/                    # Shell scripts only
│   ├── demo_concurrent_pipeline.sh    # Main demo script
│   ├── demo_full_pipeline.sh          # Full pipeline demo
│   ├── deploy_k8s.sh                  # Kubernetes deployment
│   └── redeploy.sh                    # Redeployment script
├── testing/                    # All testing scripts
│   ├── concurrent_load_test.py        # Concurrent load testing
│   ├── test_concurrent_scaling.py     # Comprehensive scaling tests
│   ├── api_comparison.py              # API performance comparison
│   ├── batch_comparison.py            # Batch vs single request testing
│   ├── gcp_concurrent_scaling_test.py # GCP-optimized testing
│   ├── gcp_api_comparison.py          # GCP API analysis
│   ├── wrk_load_test.py               # wrk benchmarking integration
│   ├── test_api_endpoints.py          # API endpoint testing
│   ├── test_memory.py                 # Memory usage analysis
│   └── test_local_setup.py            # Local setup validation
├── performance/                # Performance monitoring
│   └── performance_monitor.py         # Real-time performance monitoring
├── utils/                      # Utility scripts
│   ├── api_features_comparison.py     # API feature comparison
│   └── generate_final_report.py       # Report generation
├── iris_api.py                 # Basic API implementation
├── iris_api_enhanced.py        # Enhanced concurrent API
├── iris_pipeline.py            # Model training
└── Dockerfile                  # Container configuration
```

## Quick Start

### Run Complete Demo
```bash
./scripts/demo_concurrent_pipeline.sh
```

### Test Local Setup
```bash
python3 testing/test_local_setup.py
```

### Run Individual Tests
```bash
# Concurrent load testing
python3 testing/concurrent_load_test.py --users 10 --requests 10

# Performance monitoring
python3 performance/performance_monitor.py --duration 60

# API comparison
python3 testing/api_comparison.py
```

## GCP Deployment

The GitHub Actions workflow automatically:
1. Trains the model with MLflow
2. Builds Docker image
3. Deploys to GKE
4. Runs concurrent scaling tests
5. Generates performance reports

## Key Features

- **Concurrent Processing**: Enhanced API with async/await and thread pools
- **Comprehensive Testing**: Multiple testing approaches including wrk integration
- **Performance Monitoring**: Real-time metrics and bottleneck analysis
- **GCP Integration**: Automated deployment and testing on Google Cloud
- **Production Ready**: Scalable architecture with monitoring and error handling