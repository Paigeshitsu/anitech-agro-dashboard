import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import joblib

def load_model(model_path: Path):
    """
    Load the trained model from a joblib file.
    Returns the model package containing model and encoders.
    """
    model_package = joblib.load(model_path)
    return model_package

def predict_top_k(model_package, payload: Dict[str, object], k: int = 5) -> List[Dict[str, object]]:
    """
    Make crop predictions based on environmental conditions.
    
    Args:
        model_package: Dictionary containing model and encoders
        payload: Dictionary with keys: location, season, ph, rainfall, temperature, humidity
        k: Number of top predictions to return
    
    Returns:
        List of dictionaries with crop predictions
    """
    model = model_package['model']
    encoders = model_package['encoders']
    
    # Encode categorical variables
    location = payload.get('location', 'Laguna')
    season = payload.get('season', 'Wet')
    
    # Handle unknown values
    try:
        location_encoded = encoders['location'].transform([location])[0]
    except ValueError:
        location_encoded = 0  # Default to first location
    
    try:
        season_encoded = encoders['season'].transform([season])[0]
    except ValueError:
        season_encoded = 0  # Default to first season
    
    # Prepare input data
    input_data = {
        'location_encoded': [location_encoded],
        'season_encoded': [season_encoded],
        'ph': [float(payload.get('ph', 6.5))],
        'rainfall': [float(payload.get('rainfall', 100))],
        'temperature': [float(payload.get('temperature', 28))],
        'humidity': [float(payload.get('humidity', 80))],
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
        # Decode the class label
        crop_name = encoders['crop'].inverse_transform([classes[idx]])[0]
        
        category = "seasonal" if rank < max(1, k // 2) else "high-demand"
        predictions.append({
            "crop": crop_name,
            "score": round(float(score), 4),
            "category": category,
            "trend": "stable",
            "change_pct": 0
        })
    return predictions