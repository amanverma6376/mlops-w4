# Kubernetes Deployment Status & Solutions

## Current Issue ✅ RESOLVED → NEW ISSUE
~~The pod is failing to schedule due to insufficient memory on e2-micro nodes~~ **FIXED**

**NEW ISSUE**: Containers are getting OOMKilled (Out of Memory)
- **Node Memory**: 2GB total (e2-small), 66% usage - sufficient
- **Container Limit**: 64Mi - too restrictive for scikit-learn + FastAPI
- **Exit Code**: 137 (OOMKilled)
- **Startup Probe**: Failing due to slow startup

## Root Cause
The container memory limit (64Mi) is insufficient for loading scikit-learn, FastAPI, and the ML model.

## Solutions Applied

### 1. Increased Memory Limits ✅
**File**: `k8s/deployment.yaml`
```yaml
resources:
  requests:
    memory: "128Mi"  # Increased from 32Mi
    cpu: "50m"       # Increased from 25m
  limits:
    memory: "256Mi"  # Increased from 64Mi
    cpu: "100m"      # Increased from 50m
```

### 2. Upgraded Node Type ✅
**File**: `.github/workflows/test_pipeline.yml`
- Changed from `e2-micro` (640MB memory) to `e2-small` (2GB memory)
- This provides sufficient memory for the pod and system components

### 3. Ultra-Minimal Docker Image ✅
**File**: `requirements-minimal.txt`
- Removed pandas dependency (not needed for API)
- Only 6 essential packages: FastAPI, Uvicorn, Pydantic, Scikit-learn, NumPy, Joblib
- Further reduced memory footprint

### 4. Added Pre-pull Strategy ✅
- Pre-pulls Docker image to nodes before deployment
- Reduces deployment time and potential timeout issues

## Current Node Resource Allocation (e2-micro)
```
Resource           Requests         Limits
--------           --------         ------
cpu                593m (63%)       3043m (323%)
memory             573859200 (89%)  7609005Ki (1216%)
```

## Expected Improvement with e2-small
- **Memory**: 2GB total (vs 640MB)
- **Available for pods**: ~1.5GB after system components
- **Pod allocation**: 32Mi request, 64Mi limit
- **Success probability**: High

## Deployment Commands
Use the provided `deploy_k8s.sh` script or run the GitHub Actions workflow with the updated configuration.

## Next Steps
1. Run the updated workflow with e2-small nodes
2. Monitor pod scheduling and resource usage
3. If still failing, consider further resource optimization or node scaling

## Alternative Solutions (if needed)
1. **Use e2-medium**: 4GB memory for even more headroom
2. **Multi-node cluster**: Add more e2-micro nodes for distribution
3. **Resource optimization**: Further reduce memory requests to 16Mi
4. **Vertical Pod Autoscaler**: Automatically adjust resource requests
#
## 5. Improved Startup Probe ✅
**File**: `k8s/deployment.yaml`
- Increased `initialDelaySeconds` from 30s to 60s
- Increased `failureThreshold` from 10 to 20
- Reduced `periodSeconds` from 15s to 10s
- Allows more time for scikit-learn to load

## Memory Usage Analysis
Based on typical Python ML application memory usage:
- **Base Python + FastAPI**: ~30-50MB
- **NumPy**: ~20-30MB  
- **Scikit-learn**: ~50-80MB
- **Model loading**: ~10-30MB
- **Total estimated**: ~110-190MB

**New limits (256Mi = 268MB)** should provide sufficient headroom.

## Updated Deployment Commands
```bash
# Use the redeploy script for updated configuration
./redeploy.sh

# Or manually:
kubectl delete deployment iris-api -n iris-mlops
kubectl apply -f k8s/deployment.yaml -n iris-mlops
```