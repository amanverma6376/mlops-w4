#!/bin/bash

# Build and Deploy Script for Iris API
# This script builds the Docker image and deploys to Kubernetes

set -e

# Configuration variables
PROJECT_ID="citric-aleph-461515-j9"
IMAGE_NAME="iris-api"
IMAGE_TAG="latest"
NAMESPACE="iris-mlops"
GCR_HOSTNAME="gcr.io"

echo "Building and Deploying Iris API"
echo "==================================="

# Check if model exists, if not train it
if [ ! -f "model.pkl" ]; then
    echo "Training model (model.pkl not found)..."
    python3 iris_pipeline.py || python iris_pipeline.py
    echo "Model trained successfully!"
fi

# Configure Docker for GCR
echo "Configuring Docker for GCR..."
gcloud auth configure-docker

# Build Docker image
echo "🐳 Building Docker image..."
FULL_IMAGE_NAME="$GCR_HOSTNAME/$PROJECT_ID/$IMAGE_NAME:$IMAGE_TAG"
docker build -t $FULL_IMAGE_NAME .
echo "Docker image built: $FULL_IMAGE_NAME"

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push $FULL_IMAGE_NAME
echo "Image pushed successfully!"

# Update Kubernetes deployment with new image
echo "Updating Kubernetes deployment..."
sed -i.bak "s|gcr.io/citric-aleph-461515-j9/iris-api:latest|$FULL_IMAGE_NAME|g" k8s/deployment.yaml

# Apply Kubernetes manifests
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/deployment.yaml -n $NAMESPACE

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/iris-api -n $NAMESPACE --timeout=300s

# Get deployment status
echo "Deployment status:"
kubectl get deployments -n $NAMESPACE
echo ""
kubectl get pods -n $NAMESPACE
echo ""
kubectl get services -n $NAMESPACE

# Test the API
echo ""
echo "Testing the API..."

# Wait for external IP
echo "⏳ Waiting for external IP (this may take a few minutes)..."
for i in {1..30}; do
    EXTERNAL_IP=$(kubectl get service iris-api-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
        echo "External IP found: $EXTERNAL_IP"
        break
    fi
    echo "Waiting for external IP... ($i/30)"
    sleep 10
done

if [ ! -z "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
    echo ""
    echo "🌐 API is accessible at:"
    echo "- Health Check: http://$EXTERNAL_IP/health"
    echo "- API Documentation: http://$EXTERNAL_IP/docs"
    echo "- Prediction Endpoint: http://$EXTERNAL_IP/predict"
    
    echo ""
    echo "Testing health endpoint..."
    curl -s http://$EXTERNAL_IP/health | jq '.' || echo "Health check response received"
    
    echo ""
    echo "Testing prediction endpoint..."
    curl -X POST http://$EXTERNAL_IP/predict \
        -H "Content-Type: application/json" \
        -d '{"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}' \
        -s | jq '.' || echo "Prediction response received"
        
else
    echo "External IP not available yet. The service is still provisioning."
    echo "   Check status with: kubectl get services -n $NAMESPACE"
fi

echo ""
echo "Deployment completed successfully!"
echo ""
echo "Useful commands:"
echo "- Check pods: kubectl get pods -n $NAMESPACE"
echo "- Check services: kubectl get services -n $NAMESPACE"
echo "- Check logs: kubectl logs -l app=iris-api -n $NAMESPACE"
echo "- Scale deployment: kubectl scale deployment iris-api --replicas=5 -n $NAMESPACE"
echo ""
echo "🧹 To clean up:"
echo "- Delete deployment: kubectl delete -f k8s/deployment.yaml -n $NAMESPACE"
echo "- Delete cluster: gcloud container clusters delete iris-k8s-cluster --zone=us-central1-a" 