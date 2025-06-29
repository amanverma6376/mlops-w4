
import joblib
import numpy as np

def test_model_prediction():
    model = joblib.load("model.pkl")
    sample = np.array([[5.1, 3.5, 1.4, 0.2]])
    prediction = model.predict(sample)
    assert prediction[0] in model.classes_