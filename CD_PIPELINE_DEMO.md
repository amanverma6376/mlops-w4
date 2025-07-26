# 🚀 Continuous Deployment Pipeline Demo Guide

## 📋 Overview

This guide demonstrates a complete **Continuous Deployment (CD) pipeline** for the IRIS ML model using:

- **CML (Continuous Machine Learning)** for reporting
- **Docker** for containerization  
- **Kubernetes** for orchestration
- **Google Cloud Platform** for infrastructure
- **GitHub Actions** for CI/CD automation

---

## 🎯 Demo Objectives

**Show a complete MLOps pipeline that:**
1. ✅ Trains and validates ML models
2. ✅ Creates a production-ready API
3. ✅ Containerizes the application with Docker
4. ✅ Deploys to Kubernetes with auto-scaling
5. ✅ Integrates with CI/CD for automated deployments
6. ✅ Provides monitoring and health checks

---

## 🛠️ Prerequisites

Before running the demo, ensure you have:

### Required Tools
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Install kubectl
gcloud components install kubectl

# Install Docker
# Follow instructions at: https://docs.docker.com/get-docker/

# Install jq for JSON processing
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

### Google Cloud Setup
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project citric-aleph-461515-j9

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

---

## 🎬 Video Demonstration Steps

### **Method 1: Complete Automated Demo**

**For a full automated demonstration:**

```bash
# Make the demo script executable
chmod +x demo_full_pipeline.sh

# Run the complete demonstration
./demo_full_pipeline.sh
```

This script will guide you through all steps with colored output perfect for video recording.

---

### **Method 2: Step-by-Step Manual Demo**

**For detailed control over each step:**

#### Step 1: Project Overview
```bash
# Show project structure
tree -I '__pycache__|*.pyc|.git|.pytest_cache' || ls -la

# Show key files
echo "Key files in our MLOps pipeline:"
ls -la *.py *.yml Dockerfile k8s/ scripts/
```

#### Step 2: Train ML Model
```bash
# Train the IRIS classification model
python iris_pipeline.py

# Verify model was created
ls -la *.pkl
```

#### Step 3: Run Tests
```bash
# Run unit tests
python -m pytest tests/ -v

# Show test coverage
python -m pytest tests/ --cov=. --cov-report=html
```

#### Step 4: Test FastAPI Locally
```bash
# Start the API (in another terminal)
python iris_api.py

# Test endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'

# View API docs at: http://localhost:8000/docs
```

#### Step 5: Setup GKE Cluster
```bash
# Run the cluster setup script
chmod +x scripts/setup_gke_cluster.sh
./scripts/setup_gke_cluster.sh
```

#### Step 6: Build and Deploy
```bash
# Build Docker image and deploy to Kubernetes
chmod +x scripts/build_and_deploy.sh
./scripts/build_and_deploy.sh
```

#### Step 7: Validate Deployment
```bash
# Check deployment status
kubectl get all -n iris-mlops

# Check service external IP
kubectl get services -n iris-mlops

# Test the deployed API
EXTERNAL_IP=$(kubectl get service iris-api-service -n iris-mlops -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$EXTERNAL_IP/health
curl http://$EXTERNAL_IP/docs
```

---

## 🔄 CI/CD Pipeline Features

### GitHub Actions Workflow
The `.github/workflows/test_pipeline.yml` includes:

**Continuous Integration:**
- ✅ Automated testing with pytest
- ✅ Data validation checks
- ✅ Model training with MLFlow
- ✅ Hyperparameter tuning

**Continuous Deployment:**
- ✅ Docker image building
- ✅ Push to Google Container Registry
- ✅ Kubernetes deployment
- ✅ API health checks
- ✅ CML report generation

**CML Reporting:**
- ✅ Test results
- ✅ Model metrics
- ✅ Deployment status
- ✅ API endpoints

---

## 🐳 Docker Configuration

### Dockerfile Features
```dockerfile
# Multi-stage build for optimization
FROM python:3.10-slim

# Security: Non-root user
USER user

# Health checks included
HEALTHCHECK --interval=30s --timeout=30s CMD curl -f http://localhost:8000/health

# Optimized for production
ENV PYTHONUNBUFFERED=1
```

### Build Commands
```bash
# Build image
docker build -t gcr.io/citric-aleph-461515-j9/iris-api:latest .

# Run locally
docker run -p 8000:8000 gcr.io/citric-aleph-461515-j9/iris-api:latest

# Push to registry
docker push gcr.io/citric-aleph-461515-j9/iris-api:latest
```

---

## ☸️ Kubernetes Configuration

### Deployment Features
- **3 replicas** for high availability
- **Resource limits** (CPU: 500m, Memory: 512Mi)
- **Health checks** (liveness, readiness, startup probes)
- **Auto-scaling** (HPA: 2-10 replicas based on CPU/memory)
- **Load balancer** service for external access

### Key Commands
```bash
# Deploy
kubectl apply -f k8s/deployment.yaml -n iris-mlops

# Scale
kubectl scale deployment iris-api --replicas=5 -n iris-mlops

# Update
kubectl set image deployment/iris-api iris-api=gcr.io/citric-aleph-461515-j9/iris-api:v2.0 -n iris-mlops

# Monitor
kubectl get pods -n iris-mlops
kubectl logs -l app=iris-api -n iris-mlops
```

---

## 📊 Monitoring & Validation

### Health Checks
```bash
# Kubernetes health checks
kubectl get pods -n iris-mlops

# API health endpoint
curl http://$EXTERNAL_IP/health
```

### Performance Testing
```bash
# Simple load test
for i in {1..10}; do
  curl -X POST http://$EXTERNAL_IP/predict \
    -H "Content-Type: application/json" \
    -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}'
done
```

### Auto-scaling Demonstration
```bash
# Generate load to trigger auto-scaling
kubectl run -i --tty load-generator --rm --image=busybox --restart=Never -- /bin/sh
# Inside the pod:
while true; do wget -q -O- http://iris-api-service.iris-mlops.svc.cluster.local/predict; done

# Watch auto-scaling in action
kubectl get hpa -n iris-mlops -w
```

---

## 🎥 Video Recording Tips

### 1. **Preparation**
- Clear terminal history: `history -c`
- Close unnecessary applications
- Use a consistent terminal theme
- Set terminal font size appropriately

### 2. **Script Structure**
```bash
# Use the demo script for consistent flow
./demo_full_pipeline.sh

# Or follow the manual steps with pauses for explanation
```

### 3. **Key Points to Highlight**
- **MLOps Pipeline**: End-to-end automation
- **Production Ready**: Health checks, scaling, monitoring
- **Cloud Native**: Kubernetes, Docker, GCP
- **CI/CD Integration**: GitHub Actions automation
- **Real API**: Working endpoints with Swagger docs

### 4. **Demo Flow (15-20 minutes)**
1. **Introduction** (2 min): Overview of what we'll build
2. **Local Development** (3 min): Model training, API testing
3. **Containerization** (2 min): Docker build and test
4. **Cloud Deployment** (5 min): GKE setup, K8s deployment
5. **CI/CD Pipeline** (3 min): GitHub Actions workflow
6. **Production Testing** (3 min): API validation, scaling
7. **Conclusion** (2 min): Summary and next steps

---

## 🧹 Cleanup

After the demonstration:

```bash
# Delete Kubernetes resources
kubectl delete -f k8s/deployment.yaml -n iris-mlops

# Delete GKE cluster
gcloud container clusters delete iris-k8s-cluster --zone=us-central1-a

# Delete Docker images
gcloud container images delete gcr.io/citric-aleph-461515-j9/iris-api --force-delete-tags

# Clean local files
rm -f *.pkl
docker system prune -f
```

---

## 🚀 Next Steps

**After the demo, you can:**
1. **Extend the model**: Add more features or algorithms
2. **Enhance monitoring**: Add Prometheus/Grafana
3. **Implement A/B testing**: Deploy multiple model versions
4. **Add data pipelines**: Integrate with data sources
5. **Security hardening**: Add authentication, HTTPS

---

## 📞 Troubleshooting

### Common Issues

**1. GKE Cluster Creation Fails**
```bash
# Check quotas
gcloud compute project-info describe --project=citric-aleph-461515-j9

# Try different zone
gcloud container clusters create iris-k8s-cluster --zone=us-west1-a
```

**2. External IP Not Available**
```bash
# Check service status
kubectl describe service iris-api-service -n iris-mlops

# Force external IP (if using minikube/local)
kubectl port-forward service/iris-api-service 8080:80 -n iris-mlops
```

**3. Docker Push Fails**
```bash
# Re-authenticate Docker
gcloud auth configure-docker
docker login gcr.io
```

---

## 📋 Checklist for Video

- [ ] All prerequisites installed
- [ ] Google Cloud project configured
- [ ] Terminal setup for recording
- [ ] Demo script tested
- [ ] Backup plans for common issues
- [ ] Clean environment (no cached files)
- [ ] Network connectivity verified
- [ ] Recording software configured

---

**🎬 Ready to record your MLOps CD pipeline demonstration!** 