import os
import mlflow
from google.cloud import storage
import sqlite3

def setup_mlflow_gcs():
    
    PROJECT_ID = "innate-empire-468812-h0"
    BUCKET_NAME = "mlops-course-innate-empire-468812-h0-unique"
    
    mlflow_dir = "./mlflow_tracking"
    os.makedirs(mlflow_dir, exist_ok=True)
    
    tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
    
    artifact_root = f"gs://{BUCKET_NAME}/mlflow-artifacts"
    
    mlflow.set_tracking_uri(tracking_uri)
    
    try:
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(BUCKET_NAME)
        
        blob = bucket.blob('mlflow-artifacts/')
        if not blob.exists():
            blob.upload_from_string('')
            print(f"Created mlflow-artifacts directory in bucket {BUCKET_NAME}")
    except Exception as e:
        print(f"Warning: Could not create GCS directory: {e}")
    
    print(f"MLflow tracking URI set to: {tracking_uri}")
    print(f"MLflow artifact root set to: {artifact_root}")
    
    return tracking_uri, artifact_root

if __name__ == "__main__":
    setup_mlflow_gcs()