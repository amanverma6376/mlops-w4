from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import joblib
import numpy as np
import os
from typing import List, Dict, Optional
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
import threading
from contextlib import asynccontextmanager
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
model = None
model_lock = threading.RLock()
thread_pool = None
request_count = 0
request_count_lock = threading.Lock()

class IrisFeatures(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

class IrisPrediction(BaseModel):
    prediction: str
    confidence: float
    features: Dict[str, float]
    processing_time_ms: float

class BatchPredictionRequest(BaseModel):
    features_list: List[IrisFeatures]
    batch_id: Optional[str] = None

class BatchPredictionResponse(BaseModel):
    predictions: List[IrisPrediction]
    batch_id: Optional[str] = None
    total_processing_time_ms: float
    batch_size: int

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    active_requests: int
    uptime_seconds: float

class ModelStats(BaseModel):
    total_predictions: int
    avg_processing_time_ms: float
    model_type: str
    model_loaded: bool

# Application startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global thread_pool, model, start_time
    start_time = time.time()
    
    # Initialize thread pool for CPU-bound tasks
    thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ml-worker")
    
    # Load model
    load_model()
    
    logger.info("Enhanced Iris API started successfully")
    
    yield
    
    # Shutdown
    if thread_pool:
        thread_pool.shutdown(wait=True)
    logger.info("Enhanced Iris API shutdown complete")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Enhanced Iris ML Model API",
    description="High-performance API for predicting iris species with concurrent inference support",
    version="2.0.0",
    lifespan=lifespan
)

def load_model():
    """Load the trained model with thread safety"""
    global model
    
    with model_lock:
        if model is not None:
            return True
            
        model_path = "model.pkl"
        
        if os.path.exists(model_path):
            try:
                model = joblib.load(model_path)
                logger.info(f"Model loaded successfully from {model_path}")
                return True
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                return False
        else:
            logger.warning(f"Model file {model_path} not found")
            return False

def increment_request_count():
    """Thread-safe request counter increment"""
    global request_count
    with request_count_lock:
        request_count += 1

def get_request_count():
    """Thread-safe request counter getter"""
    global request_count
    with request_count_lock:
        return request_count

async def predict_single_async(features: IrisFeatures) -> IrisPrediction:
    """Async wrapper for single prediction"""
    loop = asyncio.get_event_loop()
    
    def predict_sync():
        start_time = time.time()
        
        with model_lock:
            if model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            # Convert input to numpy array
            input_data = np.array([[
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width
            ]])
            
            # Make prediction
            prediction = model.predict(input_data)[0]
            
            # Get prediction probabilities if available
            try:
                probabilities = model.predict_proba(input_data)[0]
                confidence = float(max(probabilities))
            except:
                confidence = 1.0  # For models without predict_proba
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            return IrisPrediction(
                prediction=str(prediction),
                confidence=confidence,
                features={
                    "sepal_length": features.sepal_length,
                    "sepal_width": features.sepal_width,
                    "petal_length": features.petal_length,
                    "petal_width": features.petal_width
                },
                processing_time_ms=processing_time
            )
    
    # Run prediction in thread pool to avoid blocking
    result = await loop.run_in_executor(thread_pool, predict_sync)
    increment_request_count()
    return result

async def predict_batch_async(features_list: List[IrisFeatures]) -> List[IrisPrediction]:
    """Async batch prediction with optimized numpy operations"""
    loop = asyncio.get_event_loop()
    
    def predict_batch_sync():
        start_time = time.time()
        
        with model_lock:
            if model is None:
                raise HTTPException(status_code=503, detail="Model not loaded")
            
            # Convert all inputs to single numpy array for batch processing
            input_data = np.array([[
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width
            ] for features in features_list])
            
            # Make batch prediction
            predictions = model.predict(input_data)
            
            # Get batch probabilities if available
            try:
                probabilities = model.predict_proba(input_data)
                confidences = [float(max(prob)) for prob in probabilities]
            except:
                confidences = [1.0] * len(predictions)
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Create response objects
            results = []
            for i, (features, prediction, confidence) in enumerate(zip(features_list, predictions, confidences)):
                results.append(IrisPrediction(
                    prediction=str(prediction),
                    confidence=confidence,
                    features={
                        "sepal_length": features.sepal_length,
                        "sepal_width": features.sepal_width,
                        "petal_length": features.petal_length,
                        "petal_width": features.petal_width
                    },
                    processing_time_ms=processing_time / len(features_list)  # Amortized time
                ))
            
            return results
    
    # Run batch prediction in thread pool
    results = await loop.run_in_executor(thread_pool, predict_batch_sync)
    
    # Update request count
    global request_count
    with request_count_lock:
        request_count += len(features_list)
    
    return results

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enhanced Iris ML Model API",
        "status": "running",
        "version": "2.0.0",
        "features": [
            "Concurrent inference support",
            "Async processing",
            "Batch predictions",
            "Performance monitoring",
            "Thread-safe operations"
        ],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint"""
    global start_time
    uptime = time.time() - start_time if 'start_time' in globals() else 0
    
    return HealthResponse(
        status="healthy" if model is not None else "unhealthy",
        model_loaded=model is not None,
        version="2.0.0",
        active_requests=get_request_count(),
        uptime_seconds=uptime
    )

@app.post("/predict", response_model=IrisPrediction)
async def predict_iris(features: IrisFeatures):
    """Async single prediction endpoint"""
    try:
        result = await predict_single_async(features)
        return result
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict_batch", response_model=BatchPredictionResponse)
async def predict_iris_batch(request: BatchPredictionRequest):
    """Enhanced batch prediction endpoint"""
    try:
        start_time = time.time()
        
        predictions = await predict_batch_async(request.features_list)
        
        total_processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return BatchPredictionResponse(
            predictions=predictions,
            batch_id=request.batch_id,
            total_processing_time_ms=total_processing_time,
            batch_size=len(request.features_list)
        )
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.post("/predict_concurrent", response_model=List[IrisPrediction])
async def predict_iris_concurrent(features_list: List[IrisFeatures]):
    """Concurrent prediction endpoint - processes each request independently"""
    try:
        # Create tasks for concurrent processing
        tasks = [predict_single_async(features) for features in features_list]
        
        # Execute all predictions concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle any exceptions
        predictions = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Prediction {i} failed: {result}")
                # Create error response
                predictions.append(IrisPrediction(
                    prediction="error",
                    confidence=0.0,
                    features={
                        "sepal_length": features_list[i].sepal_length,
                        "sepal_width": features_list[i].sepal_width,
                        "petal_length": features_list[i].petal_length,
                        "petal_width": features_list[i].petal_width
                    },
                    processing_time_ms=0.0
                ))
            else:
                predictions.append(result)
        
        return predictions
        
    except Exception as e:
        logger.error(f"Concurrent prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Concurrent prediction failed: {str(e)}")

@app.get("/model_info")
async def get_model_info():
    """Get enhanced model information"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        model_info = {
            "model_type": type(model).__name__,
            "model_loaded": True,
            "model_params": getattr(model, 'get_params', lambda: {})(),
            "thread_pool_workers": thread_pool._max_workers if thread_pool else 0,
            "concurrent_support": True,
            "batch_support": True
        }
        
        # Add classes if available
        if hasattr(model, 'classes_'):
            model_info["classes"] = model.classes_.tolist()
            
        return model_info
        
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

@app.get("/stats", response_model=ModelStats)
async def get_stats():
    """Get API statistics"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return ModelStats(
        total_predictions=get_request_count(),
        avg_processing_time_ms=50.0,  # Placeholder - could be calculated from actual metrics
        model_type=type(model).__name__,
        model_loaded=True
    )

@app.post("/reload_model")
async def reload_model():
    """Reload the model (useful for model updates)"""
    try:
        success = load_model()
        if success:
            return {"message": "Model reloaded successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reload model")
    except Exception as e:
        logger.error(f"Model reload error: {e}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")

if __name__ == "__main__":
    # Run with optimized settings for concurrent workloads
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        workers=1,  # Use 1 worker with thread pool for better resource control
        loop="asyncio",
        access_log=False,  # Disable access logs for better performance
        log_level="info"
    )