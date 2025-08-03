#!/bin/bash

# GKE Cluster Setup Script for Iris MLOps Pipeline
# This script sets up a Google Kubernetes Engine cluster for the demonstration

set -e

# Configuration variables
PROJECT_ID="citric-aleph-461515-j9"
CLUSTER_NAME="iris-k8s-cluster"
ZONE="us-central1-a"
REGION="us-central1"
NAMESPACE="iris-mlops"

echo "Setting up GKE Cluster for Iris MLOps Pipeline"
echo "=================================================="

# Authenticate with Google Cloud
echo "🔐 Authenticating with Google Cloud..."
gcloud auth login || echo "Already authenticated"

# Set project
echo "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required Google Cloud APIs..."
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Create GKE cluster
echo "Creating GKE cluster '$CLUSTER_NAME'..."
if gcloud container clusters describe $CLUSTER_NAME --zone=$ZONE 2>/dev/null; then
    echo "Cluster $CLUSTER_NAME already exists"
else
    gcloud container clusters create $CLUSTER_NAME \
        --zone=$ZONE \
        --num-nodes=3 \
        --machine-type=e2-medium \
        --disk-size=20GB \
        --enable-autoscaling \
        --min-nodes=1 \
        --max-nodes=5 \
        --enable-autorepair \
        --enable-autoupgrade \
        --addons=HorizontalPodAutoscaling,HttpLoadBalancing
    
    echo "GKE cluster created successfully!"
fi

# Get cluster credentials
echo "🔑 Getting cluster credentials..."
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Create namespace
echo "📦 Creating namespace '$NAMESPACE'..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Create Docker registry secret for GCR
echo "🔐 Creating Docker registry secret..."
kubectl create secret docker-registry gcr-json-key \
    --docker-server=gcr.io \
    --docker-username=_json_key \
    --docker-password="$(gcloud auth print-access-token)" \
    --docker-email=$(gcloud config get-value account) \
    --namespace=$NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Verify cluster setup
echo "Verifying cluster setup..."
echo "Cluster info:"
kubectl cluster-info

echo "Nodes:"
kubectl get nodes

echo "Namespaces:"
kubectl get namespaces

echo ""
echo "GKE Cluster setup complete!"
echo "📍 Cluster: $CLUSTER_NAME"
echo "📍 Zone: $ZONE"
echo "📍 Namespace: $NAMESPACE"
echo ""
echo "Next steps:"
echo "1. Run 'bash scripts/build_and_deploy.sh' to build and deploy the API"
echo "2. Use 'kubectl get services -n $NAMESPACE' to check service status"
echo "3. Access the API documentation at http://<EXTERNAL_IP>/docs" 