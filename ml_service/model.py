import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List
import joblib

# Base retail prices per kg for different crops (in PHP)
# These are approximate retail prices in the Philippines
BASE_RETAIL_PRICES = {
    'Rice': 50,
    'Corn': 35,
    'Tomato': 80,
    'Eggplant': 60,
    'Onion': 120,
    'Garlic': 200,
    'Cabbage': 45,
    'Bell Pepper': 90,
    'Chili': 100,
    'Squash': 30,
    'Bean': 70,
    'Mung Bean': 85,
    'Peanut': 150,
    'Sweet Potato': 40,
    'Cassava': 35,
}

# Season price multipliers (prices tend to be higher in dry season for some crops)
SEASON_MULTIPLIERS = {
    'Wet': 1.0,
    'Dry': 1.15,  # Prices tend to be 15% higher in dry season
}

# Location price multipliers (urban areas tend to have higher prices)
LOCATION_MULTIPLIERS = {
    'Manila': 1.25,
    'Cebu': 1.15,
    'Davao': 1.10,
    'Laguna': 1.05,
    'Bicol': 0.95,
    'Pangasinan': 0.95,
    'Nueva Ecija': 0.90,
    'Tarlac': 0.90,
}

def load_model(model_path: Path):
    """
    Load the trained model from a joblib file.
    Returns the model package containing model and encoders.
    """
    model_package = joblib.load(model_path)
    return model_package

def predict_crop_price(crop_name: str, season: str, location: str, demand_score: float) -> float:
    """
    Predict retail price for a crop based on various factors.
    
    Args:
        crop_name: Name of the crop
        season: Current season (Wet/Dry)
        location: Location name
        demand_score: Demand/suitability score (0-1)
    
    Returns:
        Predicted retail price per kg in PHP
    """
    # Get base price for the crop
    base_price = BASE_RETAIL_PRICES.get(crop_name, 50)  # Default to 50 if crop not found
    
    # Apply season multiplier
    season_mult = SEASON_MULTIPLIERS.get(season, 1.0)
    
    # Apply location multiplier
    location_mult = LOCATION_MULTIPLIERS.get(location, 1.0)
    
    # Apply demand factor (higher demand = higher price)
    # demand_score is 0-1, we convert it to a multiplier of 0.8 to 1.3
    demand_mult = 0.8 + (demand_score * 0.5)
    
    # Calculate final price with some randomness for realism
    import random
    random_factor = random.uniform(0.95, 1.05)  # +/- 5% randomness
    
    predicted_price = base_price * season_mult * location_mult * demand_mult * random_factor
    
    # Round to 2 decimal places
    return round(predicted_price, 2)


def predict_top_k(model_package, payload: Dict[str, object], k: int = 5) -> List[Dict[str, object]]:
    """
    Make crop predictions based on environmental conditions.
    
    Args:
        model_package: Dictionary containing model and encoders
        payload: Dictionary with keys: location, season, ph, rainfall, temperature, humidity
        k: Number of top predictions to return
    
    Returns:
        List of dictionaries with crop predictions including predicted prices
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
        
        # Predict price based on crop, season, location, and demand
        predicted_price = predict_crop_price(
            crop_name=crop_name,
            season=season,
            location=location,
            demand_score=float(score)
        )
        
        predictions.append({
            "crop": crop_name,
            "score": round(float(score), 4),
            "category": category,
            "trend": "stable",
            "change_pct": 0,
            "price": predicted_price
        })
    return predictions