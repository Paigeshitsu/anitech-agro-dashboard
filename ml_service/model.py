import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import joblib

def load_model(model_path: Path):
    return joblib.load(model_path)

def predict_top_k(model, payload: Dict[str, object], k: int = 5) -> List[Dict[str, object]]:
    # Optimization: Use a localized dictionary for faster DataFrame creation
    # If the model allows, passing a 2D numpy array is even faster.
    input_data = {
        "location": [payload["location"]],
        "season": [payload["season"]],
        "ph": [float(payload["ph"])],
        "rainfall": [float(payload["rainfall"])],
        "temperature": [float(payload["temperature"])],
        "humidity": [float(payload["humidity"])],
    }
    
    features = pd.DataFrame(input_data)

    # Get probabilities
    probabilities = model.predict_proba(features)[0]
    classes = model.classes_

    # Optimized sorting using argsort for larger class sets
    top_indices = np.argsort(probabilities)[::-1][:k]
    
    predictions = []
    for rank, idx in enumerate(top_indices):
        score = probabilities[idx]
        category = "seasonal" if rank < max(1, k // 2) else "high-demand"
        predictions.append({
            "crop": str(classes[idx]),
            "score": round(float(score), 4),
            "category": category,
        })
    return predictions