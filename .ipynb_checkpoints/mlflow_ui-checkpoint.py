import subprocess
import os
import sys

def start_mlflow_ui():
    mlflow_dir = "./mlflow_tracking"
    os.makedirs(mlflow_dir, exist_ok=True)
    
    tracking_uri = f"sqlite:///{mlflow_dir}/mlflow.db"
    
    print(f"Starting MLflow UI with tracking URI: {tracking_uri}")
    print("MLflow UI will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([
            sys.executable, "-m", "mlflow", "ui",
            "--backend-store-uri", tracking_uri,
            "--host", "0.0.0.0",
            "--port", "5000"
        ])
    except KeyboardInterrupt:
        print("\nMLflow UI stopped.")

if __name__ == "__main__":
    start_mlflow_ui()