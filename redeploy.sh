#!/bin/bash

echo "🔄 Redeploying with updated memory limits and minimal dependencies..."

# Delete existing deployment to force recreation
kubectl delete deployment iris-api -n iris-mlops --ignore-not-found=true

# Wait a moment for cleanup
sleep 5

# Apply updated deployment
kubectl apply -f k8s/deployment.yaml -n iris-mlops

echo "📊 Checking deployment status..."
kubectl get deployments -n iris-mlops
kubectl get pods -n iris-mlops

echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/iris-api -n iris-mlops --timeout=600s

echo "🔍 Checking pod status..."
kubectl get pods -n iris-mlops -o wide

echo "📋 Getting pod logs..."
kubectl logs -l app=iris-api -n iris-mlops --tail=20

echo "🌐 Service status..."
kubectl get services -n iris-mlops