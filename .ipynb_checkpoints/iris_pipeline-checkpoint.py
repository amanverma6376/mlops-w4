# iris_pipeline.py

import pandas as pd
from sklearn.linear_model import LogisticRegression
import joblib

def train_model():
    # Load IRIS dataset from CSV
    df = pd.read_csv("data/iris.csv")

    # Assuming last column is target (species)
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]

    # Train a simple Logistic Regression model
    model = LogisticRegression(max_iter=200)
    model.fit(X, y)

    # Save model
    joblib.dump(model, "model.pkl")
    print("✅ Model trained and saved as model.pkl")

if __name__ == "__main__":
    train_model()
