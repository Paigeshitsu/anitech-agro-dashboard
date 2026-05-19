"""
Advanced Market Price Predictor with Disaster & Pest Outbreak Support
Handles seasonality, natural disasters, pest outbreaks and market shocks
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Directories
DATA_DIR = Path(__file__).parent / 'data'
MODEL_DIR = Path(__file__).parent / 'models'

# Impact factors for market shocks
DISASTER_IMPACT = {
    'typhoon': 1.45,
    'flood': 1.38,
    'drought': 1.52,
    'earthquake': 1.25,
    'volcano': 1.60,
    'none': 1.0
}

PEST_OUTBREAK_IMPACT = {
    'armyworm': 1.55,
    'locust': 1.80,
    'blast': 1.40,
    'mosaic_virus': 1.35,
    'aphids': 1.28,
    'none': 1.0
}

SEASON_PRICE_MULTIPLIER = {
    'wet': 0.88, 'Wet': 0.88,
    'dry': 1.22, 'Dry': 1.22,
    'transition': 1.05, 'Transition': 1.05,
    'Dry Season': 1.22, 'Wet Season': 0.88
}

# Weather impact factors - high rainfall/temp/humidity can DECREASE prices (abundant supply)
WEATHER_PRICE_IMPACT = {
    'high_rainfall': 0.85,  # Heavy rain = abundant harvest = lower prices
    'low_rainfall': 1.15,   # Drought = scarcity = higher prices
    'normal_rainfall': 1.0,
    'high_temp': 0.95,     # Heat can damage crops but also speed growth
    'low_temp': 1.05,      # Cold = slower growth = higher prices
    'normal_temp': 1.0,
    'high_humidity': 0.90, # High humidity can cause disease = lower quality = lower prices
    'low_humidity': 1.05,  # Dry = pest issues = higher prices
    'normal_humidity': 1.0
}

CROP_HISTORICAL_BASE_PRICES = {
    'Rice': 47, 'Corn': 33, 'Tomato': 76, 'Eggplant': 56,
    'Onion': 112, 'Garlic': 185, 'Cabbage': 42, 'Bell Pepper': 87,
    'Chili': 97, 'Squash': 29, 'Bean': 68, 'Mung Bean': 83,
    'Peanut': 148, 'Sweet Potato': 39, 'Cassava': 34
}

CROP_NAME_ALIASES = {
    'commercial milled rice': 'Rice',
    'rice (commercial milled)': 'Rice',
    'red onion': 'Onion',
    'string beans': 'Bean',
    'string bean': 'Bean',
    'chinese cabbage': 'Cabbage',
    'pechay': 'Cabbage',
    'kalabasa': 'Squash',
    'talong': 'Eggplant',
    'sitao': 'Bean',
    'ampalaya': 'Ampalaya',
    'watermelon': 'Watermelon',
    'melon': 'Melon',
    'calamansi': 'Calamansi',
}

LOCATION_NAME_ALIASES = {
    'legazpi city': 'Bicol',
    'legazpi': 'Bicol',
    'naga city': 'Bicol',
    'naga': 'Bicol',
    'bicol region': 'Bicol',
}


def generate_enhanced_training_data():
    """Generate training data including disasters, pests and season shocks"""
    print("Generating enhanced training dataset with market shock factors...")

    locations = ['Infanta', 'Laguna', 'Bicol', 'Quezon', 'Nueva Ecija', 'Pangasinan']
    crops = list(CROP_HISTORICAL_BASE_PRICES.keys())
    disasters = list(DISASTER_IMPACT.keys())
    pests = list(PEST_OUTBREAK_IMPACT.keys())

    historical_data = []
    start_year = 2015
    current_year = datetime.now().year

    for year in range(start_year, current_year + 1):
        for month in range(1, 13):
            for location in locations:
                for crop in crops[:10]:

                    is_wet_season = 6 <= month <= 11
                    season = 'wet' if is_wet_season else 'dry' if (month <= 3 or month >= 11) else 'transition'

                    # Random disaster events (12% chance per month)
                    disaster = np.random.choice(disasters, p=[0.04, 0.03, 0.03, 0.01, 0.01, 0.88])
                    pest_outbreak = np.random.choice(pests, p=[0.03, 0.02, 0.03, 0.02, 0.03, 0.87])

                    # Base weather
                    rainfall = 310 if is_wet_season else 72 + (year % 5 * 11)
                    temperature = 27.3 + (month * 0.3) - (year % 4 * 0.2)
                    humidity = 81 if is_wet_season else 67
                    soil_ph = 6.1 + np.random.normal(0, 0.4)

                    # Calculate base yield
                    base_yields = {
                        'Rice': 4150 if is_wet_season else 3750,
                        'Corn': 3550 if is_wet_season else 2850,
                        'Tomato': 12400, 'Eggplant': 10900,
                        'Onion': 9400, 'Garlic': 7100,
                        'Cabbage': 14900, 'Bell Pepper': 9700,
                        'Chili': 8200, 'Squash': 7800
                    }

                    year_growth = 1 + ((year - start_year) * 0.017)
                    yield_variance = np.random.normal(1, 0.11)

                    # Apply disaster / pest impact on yield
                    disaster_yield_factor = 1 / DISASTER_IMPACT[disaster] if disaster != 'none' else 1.0
                    pest_yield_factor = 1 / PEST_OUTBREAK_IMPACT[pest_outbreak] if pest_outbreak != 'none' else 1.0

                    yield_kg = base_yields.get(crop, 3500) * year_growth * yield_variance * disaster_yield_factor * pest_yield_factor

                    # Calculate price
                    base_price = CROP_HISTORICAL_BASE_PRICES[crop]
                    season_mult = SEASON_PRICE_MULTIPLIER[season]
                    disaster_mult = DISASTER_IMPACT[disaster]
                    pest_mult = PEST_OUTBREAK_IMPACT[pest_outbreak]
                    price_variance = np.random.normal(1, 0.13)

                    final_price = base_price * season_mult * disaster_mult * pest_mult * price_variance

                    historical_data.append({
                        'date': datetime(year, month, 15),
                        'year': year,
                        'month': month,
                        'location': location,
                        'crop': crop,
                        'season': season,
                        'disaster_event': disaster,
                        'pest_outbreak': pest_outbreak,
                        'rainfall_mm': rainfall + np.random.normal(0, 38),
                        'temperature_c': temperature + np.random.normal(0, 1.1),
                        'humidity_pct': humidity + np.random.normal(0, 5),
                        'soil_ph': np.clip(soil_ph, 4.8, 7.8),
                        'yield_kg_ha': round(yield_kg, 1),
                        'market_price_php': round(final_price, 2)
                    })

    df = pd.DataFrame(historical_data)
    print(f"Generated {len(df)} enhanced training records")
    return df


def load_past_training_datasets():
    """Load past training datasets supplied in ml_service/data and merge them with synthetic examples."""
    past_datasets = []

    csv_paths = [
        DATA_DIR / 'training_data_sample.csv',
        DATA_DIR / 'bantay_presyo_region_v_legazpi_naga_ml.csv',
    ]

    for csv_path in csv_paths:
        if not csv_path.exists():
            print(f"No historical training dataset found at {csv_path}")
            continue

        print(f"Loading past dataset from {csv_path}")
        df = pd.read_csv(csv_path)

        if df.empty:
            continue

        if 'price_per_kg' in df.columns:
            df = df.rename(columns={'price_per_kg': 'market_price_php'})

        if 'as_of_date' in df.columns and 'date' not in df.columns:
            df = df.rename(columns={'as_of_date': 'date'})

        if 'crop_name' in df.columns and 'crop' not in df.columns:
            df = df.rename(columns={'crop_name': 'crop'})

        if 'average_price' in df.columns and 'market_price_php' not in df.columns:
            df = df.rename(columns={'average_price': 'market_price_php'})

        if 'date' not in df.columns:
            df['date'] = datetime.now().strftime('%Y-%m-%d')

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date']).copy()

        if 'year' not in df.columns:
            df['year'] = df['date'].dt.year
        if 'month' not in df.columns:
            df['month'] = df['date'].dt.month
        if 'location' not in df.columns:
            df['location'] = 'Bicol'
        if 'crop' not in df.columns:
            continue

        df['crop'] = df['crop'].astype(str).str.strip().map(lambda value: CROP_NAME_ALIASES.get(value.lower(), value))

        if 'humidity_pct' not in df.columns and 'humidity' in df.columns:
            df['humidity_pct'] = df['humidity']

        if 'rainfall_mm' not in df.columns:
            df['rainfall_mm'] = df['month'].apply(lambda month: 310.0 if 6 <= int(month) <= 11 else 72.0)
        if 'temperature_c' not in df.columns:
            df['temperature_c'] = df['month'].apply(lambda month: 27.0 if 6 <= int(month) <= 11 else 30.0)
        if 'humidity_pct' not in df.columns:
            df['humidity_pct'] = df['month'].apply(lambda month: 81.0 if 6 <= int(month) <= 11 else 67.0)
        if 'soil_ph' not in df.columns:
            df['soil_ph'] = 6.1
        if 'yield_kg_ha' not in df.columns:
            df['yield_kg_ha'] = 3500.0
        if 'season' not in df.columns:
            df['season'] = df['month'].apply(lambda m: 'wet' if 6 <= int(m) <= 11 else 'dry')

        df['disaster_event'] = df.get('disaster_event', 'none')
        df['pest_outbreak'] = df.get('pest_outbreak', 'none')

        df = df[[
            'date', 'year', 'month', 'location', 'crop', 'season',
            'disaster_event', 'pest_outbreak', 'rainfall_mm', 'temperature_c',
            'humidity_pct', 'soil_ph', 'yield_kg_ha', 'market_price_php'
        ]].copy()

        past_datasets.append(df)

    if not past_datasets:
        print("No past training datasets found. Falling back to synthetic generation.")
        return None

    merged = pd.concat(past_datasets, ignore_index=True)
    print(f"Loaded {len(merged)} records from past datasets")
    return merged


def train_advanced_price_model():
    """Train advanced model that accounts for disasters and pests"""
    df = load_past_training_datasets()
    if df is None or df.empty:
        df = generate_enhanced_training_data()
    else:
        # Use synthetic data to fill any coverage gaps while preserving historical datasets
        synthetic = generate_enhanced_training_data()
        df = pd.concat([df, synthetic.sample(frac=0.4, random_state=42)], ignore_index=True)

    # Encode categorical fields
    encoders = {}

    for col in ['location', 'crop', 'season', 'disaster_event', 'pest_outbreak']:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col])
        encoders[col] = le

    # Time features
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['year_norm'] = (df['year'] - df['year'].min()) / (df['year'].max() - df['year'].min())

    feature_cols = [
        'location_encoded', 'crop_encoded', 'season_encoded',
        'disaster_event_encoded', 'pest_outbreak_encoded',
        'year_norm', 'month_sin', 'month_cos',
        'rainfall_mm', 'temperature_c', 'humidity_pct', 'soil_ph'
    ]

    X = df[feature_cols]
    y = df['market_price_php']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=42)

    # Train GradientBoosting model optimized for price shocks
    price_model = GradientBoostingRegressor(
        n_estimators=350,
        max_depth=10,
        learning_rate=0.06,
        subsample=0.82,
        random_state=42,
        n_jobs=-1
    )

    price_model.fit(X_train, y_train)

    # Evaluate
    y_pred = price_model.predict(X_test)
    model_r2 = r2_score(y_test, y_pred)

    print(f"\nAdvanced Price Model R^2 Score: {model_r2:.5f}")
    print(f"Model trained with disaster and pest outbreak support")

    # Save model
    model_package = {
        'model': price_model,
        'encoders': encoders,
        'feature_cols': feature_cols,
        'disaster_factors': DISASTER_IMPACT,
        'pest_factors': PEST_OUTBREAK_IMPACT,
        'season_factors': SEASON_PRICE_MULTIPLIER,
        'training_date': datetime.now().isoformat(),
        'version': '2.0.0'
    }

    output_path = MODEL_DIR / 'market_price_forecast.joblib'
    joblib.dump(model_package, output_path, compress=3)
    print(f"\nAdvanced market price model saved to {output_path}")

    return model_package


def predict_market_price(crop: str, location: str, season: str = None,
                         disaster: str = 'none', pest: str = 'none', months_ahead: int = 1,
                         weather_data: dict = None):
    """
    Predict market price with support for disasters, pest outbreaks, and current weather data

    Args:
        crop: Name of crop
        location: Philippine location
        season: wet/dry/transition (auto detected if None)
        disaster: typhoon/flood/drought/earthquake/volcano/none
        pest: armyworm/locust/blast/mosaic_virus/aphids/none
        months_ahead: Forecast months into future
        weather_data: Current weather data from Open-Meteo API

    Returns:
        Predicted market price in PHP per kg
    """
    model_path = MODEL_DIR / 'market_price_forecast.joblib'
    original_crop = crop
    crop = CROP_NAME_ALIASES.get(str(crop).strip().lower(), crop)
    location = LOCATION_NAME_ALIASES.get(str(location).strip().lower(), location)

    if not model_path.exists():
        print("Training new advanced market price model first...")
        model_package = train_advanced_price_model()
    else:
        try:
            model_package = joblib.load(model_path)
        except Exception as e:
            print(f"Error loading market price model: {e}")
            print("Training new model...")
            model_package = train_advanced_price_model()

    model = model_package['model']
    encoders = model_package['encoders']

    forecast_date = datetime.now() + timedelta(days=months_ahead * 30)
    month = forecast_date.month
    year = forecast_date.year

    if season is None:
        if 6 <= month <= 11:
            season = 'wet'
        elif month <= 3 or month >= 11:
            season = 'dry'
        else:
            season = 'transition'

    # Use real weather data if provided, otherwise use seasonal defaults
    if weather_data:
        rainfall = weather_data.get('rainfall', 310 if season == 'wet' else 72)
        temperature = weather_data.get('temperature', 27.3 + (month * 0.3))
        humidity = weather_data.get('humidity', 81 if season == 'wet' else 67)
    else:
        rainfall = 310 if season == 'wet' else 72
        temperature = 27.3 + (month * 0.3)
        humidity = 81 if season == 'wet' else 67

    # Encode inputs
    def safe_encode(encoder, value):
        try:
            return encoders[encoder].transform([value])[0]
        except ValueError:
            return 0

    features = np.array([[
        safe_encode('location', location),
        safe_encode('crop', crop),
        safe_encode('season', season),
        safe_encode('disaster_event', disaster),
        safe_encode('pest_outbreak', pest),
        (year - 2015) / 15,
        np.sin(2 * np.pi * month / 12),
        np.cos(2 * np.pi * month / 12),
        rainfall,
        temperature,
        humidity,
        6.1  # pH (soil)
    ]])

    predicted_price = model.predict(features)[0]

    return {
        'crop': original_crop,
        'location': location,
        'forecast_date': forecast_date.strftime('%Y-%m-%d'),
        'season': season,
        'disaster_event': disaster,
        'pest_outbreak': pest,
        'predicted_price_php': round(float(predicted_price), 2),
        'base_normal_price': round(CROP_HISTORICAL_BASE_PRICES.get(crop, 50) * SEASON_PRICE_MULTIPLIER[season], 2),
        'weather_used': {
            'rainfall_mm': rainfall,
            'temperature_c': temperature,
            'humidity_percent': humidity
        }
    }


if __name__ == '__main__':
    print("=" * 70)
    print("ADVANCED MARKET PRICE PREDICTOR TRAINING")
    print("=" * 70)
    train_advanced_price_model()

    # Test predictions with different scenarios
    print("\n" + "=" * 70)
    print("EXAMPLE FORECASTS (Infanta, Rice):")
    print("-" * 70)

    scenarios = [
        ('normal conditions', 'none', 'none'),
        ('during typhoon', 'typhoon', 'none'),
        ('armyworm outbreak', 'none', 'armyworm'),
        ('typhoon + locust outbreak', 'typhoon', 'locust')
    ]

    for desc, disaster, pest in scenarios:
        result = predict_market_price('Rice', 'Infanta', disaster=disaster, pest=pest)
        print(f"{desc:28} | ₱{result['predicted_price_php']:5.2f}/kg | {result['price_shock_pct']:+5.1f}% change")
