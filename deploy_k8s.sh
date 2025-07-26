# Create namespace if it doesn't exist
kubectl create namespace iris-mlops --dry-run=client -o yaml | kubectl apply -f -

# Create Docker registry secret
# Check if GCP_SA_KEY is base64 encoded or raw JSON
if echo '***************************************' | base64 -d >/dev/null 2>&1; then
  echo "GCP_SA_KEY is base64 encoded, decoding..."
  echo '***************************************' | base64 -d > /tmp/gcr-key.json
else
  echo "GCP_SA_KEY is raw JSON, using directly..."
  echo '***************************************' > /tmp/gcr-key.json
fi

kubectl create secret docker-registry gcr-json-key \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat /tmp/gcr-key.json)" \
  --docker-email=service-account@citric-aleph-461515-j9.iam.gserviceaccount.com \
  --namespace=iris-mlops --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/gcr-key.json

# Update deployment image
echo "Using Docker image: gcr.io/citric-aleph-461515-j9/iris-api:5a1fd0b526a77e18377031d37c87ea9f069401a6"
sed -i "s|gcr.io/citric-aleph-461515-j9/iris-api:latest|gcr.io/citric-aleph-461515-j9/iris-api:5a1fd0b526a77e18377031d37c87ea9f069401a6|g" k8s/deployment.yaml

# Verify the image was updated in the deployment
echo "Updated deployment.yaml:"
grep -A 5 -B 5 "image:" k8s/deployment.yaml

# Apply Kubernetes manifests
kubectl apply -f k8s/deployment.yaml -n iris-mlops

# Check deployment status
echo "Checking deployment status..."
kubectl get deployments -n iris-mlops
kubectl get pods -n iris-mlops
kubectl get events -n iris-mlops --sort-by='.lastTimestamp' | tail -10

# Wait for deployment to be ready
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/iris-api -n iris-mlops --timeout=600s

# Get service details
kubectl get services -n iris-mlops
