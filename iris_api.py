from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
import os
from typing import List, Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Iris ML Model API",
    description="API for predicting iris species using trained ML model",
    version="1.0.0"
)

# Global model variable
model = None

class IrisFeatures(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

class IrisPrediction(BaseModel):
    prediction: str
    confidence: float
    features: Dict[str, float]

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str

def load_model():
    """Load the trained model"""
    global model
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

# Load model on startup
model_loaded = load_model()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Iris ML Model API",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if model_loaded and model is not None else "unhealthy",
        model_loaded=model_loaded and model is not None,
        version="1.0.0"
    )

@app.post("/predict", response_model=IrisPrediction)
async def predict_iris(features: IrisFeatures):
    """Predict iris species"""
    if not model_loaded or model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
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
        
        return IrisPrediction(
            prediction=str(prediction),
            confidence=confidence,
            features={
                "sepal_length": features.sepal_length,
                "sepal_width": features.sepal_width,
                "petal_length": features.petal_length,
                "petal_width": features.petal_width
            }
        )
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.post("/predict_batch", response_model=List[IrisPrediction])
async def predict_iris_batch(features_list: List[IrisFeatures]):
    """Batch prediction endpoint"""
    if not model_loaded or model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        predictions = []
        for features in features_list:
            input_data = np.array([[
                features.sepal_length,
                features.sepal_width,
                features.petal_length,
                features.petal_width
            ]])
            
            prediction = model.predict(input_data)[0]
            
            try:
                probabilities = model.predict_proba(input_data)[0]
                confidence = float(max(probabilities))
            except:
                confidence = 1.0
            
            predictions.append(IrisPrediction(
                prediction=str(prediction),
                confidence=confidence,
                features={
                    "sepal_length": features.sepal_length,
                    "sepal_width": features.sepal_width,
                    "petal_length": features.petal_length,
                    "petal_width": features.petal_width
                }
            ))
        
        return predictions
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")

@app.get("/model_info")
async def get_model_info():
    """Get model information"""
    if not model_loaded or model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        model_info = {
            "model_type": type(model).__name__,
            "model_loaded": True,
            "model_params": getattr(model, 'get_params', lambda: {})()
        }
        
        # Add classes if available
        if hasattr(model, 'classes_'):
            model_info["classes"] = model.classes_.tolist()
            
        return model_info
        
    except Exception as e:
        logger.error(f"Model info error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 