# Kubernetes Deployment Status & Solutions

## Current Issue
The pod is failing to schedule due to insufficient memory on e2-micro nodes:
- **Node Memory**: 640MB total, 573MB allocated (89% usage)
- **Available Memory**: ~67MB
- **Pod Request**: 64Mi (67MB) - too close to available memory

## Root Cause
The e2-micro instance type has insufficient memory (640MB) for running the API pod along with system components.

## Solutions Applied

### 1. Reduced Resource Requests ✅
**File**: `k8s/deployment.yaml`
```yaml
resources:
  requests:
    memory: "32Mi"  # Reduced from 64Mi
    cpu: "25m"      # Reduced from 50m
  limits:
    memory: "64Mi"  # Reduced from 128Mi
    cpu: "50m"      # Reduced from 100m
```

### 2. Upgraded Node Type ✅
**File**: `.github/workflows/test_pipeline.yml`
- Changed from `e2-micro` (640MB memory) to `e2-small` (2GB memory)
- This provides sufficient memory for the pod and system components

### 3. Optimized Docker Image ✅
**File**: `requirements-api.txt`
- Created minimal requirements file with only 7 essential packages
- Reduced image size significantly

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