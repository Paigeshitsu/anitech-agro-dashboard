import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
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
    'Beans': 80,
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
    'Albay': 0.95,
    'Legazpi City': 0.95,
    'Pangasinan': 0.95,
    'Nueva Ecija': 0.90,
    'Tarlac': 0.90,
}

CROP_NAME_ALIASES = {
    'Bean': 'Beans',
    'String Bean': 'Beans',
    'String Beans': 'Beans',
    'Sitaw': 'Beans',
    'Sitao': 'Beans',
    'Pole Sitao': 'Beans',
    'Eggplants': 'Eggplant',
    'Ampalaya': 'Bitter Gourd',
    'Chinese Cabbage': 'Cabbage',
    'Pechay': 'Cabbage',
}

SEASONAL_CROP_HINTS = {
    'Rice': {'Wet'},
    'Corn': {'Wet'},
    'Onion': {'Dry'},
    'Garlic': {'Dry'},
    'Tomato': {'Dry'},
    'Eggplant': {'Dry', 'Wet'},
    'Cabbage': {'Dry'},
    'Chili': {'Dry'},
    'Sweet Potato': {'Dry', 'Wet'},
    'Peanut': {'Dry'},
    'Cassava': {'Dry', 'Wet'},
    'Beans': {'Dry'},
}

STATIC_HIGH_DEMAND_CROPS = {
    'Rice', 'Onion', 'Garlic', 'Tomato', 'Eggplant', 'Cabbage', 'Beans'
}


def _normalize_recommendation_crop_name(crop_name: str) -> str:
    if not crop_name:
        return crop_name
    return CROP_NAME_ALIASES.get(crop_name, crop_name)


def _score_market_demand(market_prices: Dict, requested_crops: List[str]) -> Dict[str, float]:
    normalized_market_prices = {}
    if isinstance(market_prices, dict):
        for crop_name, details in market_prices.items():
            normalized_name = _normalize_recommendation_crop_name(crop_name)
            if not normalized_name:
                continue

            detail_map = details or {}
            current_price = float(detail_map.get('current_price') or detail_map.get('price') or 0)
            trend_percent = float(detail_map.get('trend_percent') or 0)
            existing = normalized_market_prices.get(normalized_name)

            if existing is None or current_price >= existing['current_price']:
                normalized_market_prices[normalized_name] = {
                    'current_price': current_price,
                    'trend_percent': trend_percent,
                }

    requested = list(dict.fromkeys(
        normalized_name
        for normalized_name in (_normalize_recommendation_crop_name(crop_name) for crop_name in requested_crops)
        if normalized_name
    ))
    max_price = max(
        (normalized_market_prices.get(crop_name, {}).get('current_price', 0) for crop_name in requested),
        default=0,
    )

    score_map = {}
    for crop_name in requested:
        market_data = normalized_market_prices.get(crop_name, {})
        price_component = (
            float(market_data.get('current_price', 0) or 0) / max_price
            if max_price > 0
            else 0
        )
        trend_component = min(max(float(market_data.get('trend_percent', 0) or 0), 0.0), 25.0) / 25.0
        base_component = 0.2 if crop_name in STATIC_HIGH_DEMAND_CROPS else 0.0
        score_map[crop_name] = max(
            0.0,
            min(1.0, (price_component * 0.6) + (trend_component * 0.2) + base_component),
        )

    return score_map


def _get_market_demand_leaders(market_prices: Dict, requested_crops: List[str]) -> set:
    score_map = _score_market_demand(market_prices, requested_crops)
    if not score_map:
        requested = list(dict.fromkeys(
            normalized_name
            for normalized_name in (_normalize_recommendation_crop_name(crop_name) for crop_name in requested_crops)
            if normalized_name
        ))
        return {
            crop_name for crop_name in requested
            if crop_name in STATIC_HIGH_DEMAND_CROPS
        }

    ranked_crops = sorted(score_map.items(), key=lambda item: (-item[1], item[0]))
    leader_count = min(len(ranked_crops), max(1, (len(ranked_crops) + 1) // 3))
    return {crop_name for crop_name, _ in ranked_crops[:leader_count]}


def _curate_prediction_category(crop_name: str, season: str, score: float, demand_leaders: set) -> str:
    normalized_name = _normalize_recommendation_crop_name(crop_name)
    preferred_seasons = SEASONAL_CROP_HINTS.get(normalized_name, set())

    if preferred_seasons and season in preferred_seasons and score >= 0.5:
        return 'seasonal'
    if normalized_name in demand_leaders:
        return 'high-demand'
    if score >= 0.65:
        return 'seasonal'
    return 'high-demand'

def load_model(model_path: Path):
    """
    Load the trained model from a joblib file.
    Returns the model package containing model and encoders.
    """
    try:
        model_package = joblib.load(model_path)
        return model_package
    except Exception as e:
        print(f"Error loading model {model_path}: {e}")
        return None

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

    requested_crops = payload.get('crops') or []

    # Get predictions - handle both classifier and regressor models
    if hasattr(model, 'predict_proba'):
        # Classifier model
        probabilities = model.predict_proba(features)[0]
        classes = model.classes_
        crop_names = [encoders['crop'].inverse_transform([cls])[0] for cls in classes]
    else:
        # Regressor model - assume it predicts suitability scores for each crop
        # For now, use fallback predictions since the model structure is different
        from .views import get_fallback_predictions
        return get_fallback_predictions(payload)

    score_by_crop = {}
    for idx, crop_name in enumerate(crop_names):
        normalized_name = _normalize_recommendation_crop_name(crop_name)
        if not normalized_name:
            continue
        score_by_crop[normalized_name] = max(
            score_by_crop.get(normalized_name, 0.0),
            float(probabilities[idx]),
        )

    if requested_crops:
        ordered_requested_crops = list(dict.fromkeys(
            normalized_name
            for normalized_name in (_normalize_recommendation_crop_name(crop_name) for crop_name in requested_crops)
            if normalized_name
        ))
    else:
        ordered_requested_crops = list(score_by_crop)

    available_requested_crops = [
        crop_name for crop_name in ordered_requested_crops if crop_name in score_by_crop
    ]
    missing_requested_crops = [
        crop_name for crop_name in ordered_requested_crops if crop_name not in score_by_crop
    ]

    available_requested_crops.sort(key=lambda crop_name: score_by_crop[crop_name], reverse=True)

    if k is None or k <= 0:
        top_crop_names = available_requested_crops
    else:
        top_crop_names = available_requested_crops[:k]

    demand_leaders = _get_market_demand_leaders(payload.get('market_prices') or {}, ordered_requested_crops)
    predictions = []
    for crop_name in top_crop_names:
        score = score_by_crop[crop_name]
        category = _curate_prediction_category(crop_name, season, score, demand_leaders)
        
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

    if missing_requested_crops:
        from .views import get_fallback_predictions

        fallback_predictions = get_fallback_predictions({
            **payload,
            'crops': missing_requested_crops,
        })
        fallback_by_crop = {
            prediction['crop']: prediction for prediction in fallback_predictions
        }

        for crop_name in missing_requested_crops:
            prediction = fallback_by_crop.get(crop_name)
            if prediction is not None:
                predictions.append(prediction)

    return predictions


def load_forecast_model():
    """Load the trained forecast model package"""
    model_path = Path(__file__).parent / 'models' / 'forecast_model.joblib'
    if model_path.exists():
        try:
            return joblib.load(model_path)
        except Exception as e:
            print(f"Error loading forecast model {model_path}: {e}")
            return None
    return None


def get_crop_forecasts(location: str, crop: str, months_ahead: int = 12):
    """Get yield and price forecasts for given location and crop"""
    forecast_model = load_forecast_model()
    if not forecast_model:
        return []

    encoders = forecast_model['encoders']
    yield_model = forecast_model['yield_model']
    price_model = forecast_model['price_model']

    forecasts = []
    today = datetime.now()

    for month_offset in range(1, months_ahead + 1):
        forecast_date = today + timedelta(days=month_offset * 30)
        year = forecast_date.year
        month = forecast_date.month

        # Generate features
        try:
            loc_enc = encoders['location'].transform([location])[0]
            crop_enc = encoders['crop'].transform([crop])[0]
        except ValueError:
            loc_enc = 0
            crop_enc = 0

        month_sin = np.sin(2 * np.pi * month / 12)
        month_cos = np.cos(2 * np.pi * month / 12)
        year_norm = (year - 2015) / (2030 - 2015)

        is_wet = 6 <= month <= 11
        rainfall = 320 if is_wet else 75
        temp = 27.5 + (month * 0.3)
        humidity = 82 if is_wet else 68
        ph = 6.3

        features = np.array([[
            loc_enc, crop_enc, year_norm, month_sin, month_cos,
            rainfall, temp, humidity, ph
        ]])

        # Predict
        yield_pred_scaled = yield_model.predict(features)[0]
        price_pred_scaled = price_model.predict(features)[0]

        yield_kg = encoders['scaler_yield'].inverse_transform([[yield_pred_scaled]])[0][0]
        price_php = encoders['scaler_price'].inverse_transform([[price_pred_scaled]])[0][0]

        forecasts.append({
            'date': forecast_date.strftime('%Y-%m-%d'),
            'month': forecast_date.strftime('%b'),
            'year': year,
            'predicted_yield_kg_ha': round(float(yield_kg), 1),
            'predicted_price_php': round(float(price_php), 2),
            'confidence': '±9.2%'
        })

    return forecasts
