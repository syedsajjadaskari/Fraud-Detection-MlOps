import joblib
import pandas as pd

from functools import lru_cache
from pathlib import Path

MODEL_PATH = (Path(__file__).resolve().parent
    / "models"/"fraud_model_v1.joblib")

@lru_cache(maxsize=1)
def load_model():
    return joblib.load(MODEL_PATH)

def predict_fraud(features):

    artifact = load_model()
    model = artifact['model']
    columns = artifact['features']
    threshold = artifact['threshold']
    X = pd.DataFrame([{
        name: features.get(name) for name in columns }])
   
    probability = float(
       model.predict_proba(X)[0][1]
   )
    prediction = int(probability> threshold)

    return {
        "fraud_score": probability,
        "is_suspicious": prediction,
        "model_version": artifact["version"]
    }

if __name__ == "__main__":
    test_transaction = {
        "amount": 5000,
        "txn_count_5m": 5,
        "amount_sum_1h": 90000,
        "amount_ratio": 40,
        "city_changed": 1
    }
    results = predict_fraud(test_transaction)
    print("Predcition ", results)
    
