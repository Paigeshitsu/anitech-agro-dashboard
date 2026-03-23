"""
Advanced ML Model Training Script for Crop Prediction
=====================================================
This script trains a highly accurate ML model using comprehensive
Philippine agricultural research data.

Usage:
    python ml_service/train_advanced.py
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score

# Define paths
MODEL_DIR = Path(__file__).parent / 'models'
MODEL_DIR.mkdir(exist_ok=True)

# Philippine agricultural research data
PHILIPPINE_CROP_DATA = {
    'Rice': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Tarlac', 'Mindoro', 'Cagayan', 'Isabela', 'Ilocos Norte', 'Laguna', 'Bohol', 'Negros'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1000, 2500), 'optimal_temp': (20, 35), 'optimal_humidity': (60, 85), 'season': 'Both', 'success_rate': 0.92
    },
    'Corn': {
        'locations': ['Pangasinan', 'Tarlac', 'Nueva Ecija', 'Isabela', 'Cagayan', 'Bukidnon', 'Cotabato', 'South Cotabato'],
        'optimal_ph': (5.8, 7.5), 'optimal_rainfall': (500, 1500), 'optimal_temp': (21, 35), 'optimal_humidity': (50, 80), 'season': 'Both', 'success_rate': 0.88
    },
    'Tomato': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya', 'Quezon', 'Batangas', 'Rizal', 'Laguna'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (400, 1200), 'optimal_temp': (15, 30), 'optimal_humidity': (50, 70), 'season': 'Both', 'success_rate': 0.85
    },
    'Eggplant': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Ilocos Norte', 'Cagayan', 'Isabela', 'Quezon', 'Batangas'],
        'optimal_ph': (5.5, 6.5), 'optimal_rainfall': (600, 1500), 'optimal_temp': (22, 32), 'optimal_humidity': (55, 75), 'season': 'Both', 'success_rate': 0.87
    },
    'Onion': {
        'locations': ['Ilocos Norte', 'Ilocos Sur', 'Pangasinan', 'Nueva Ecija', 'Tarlac', 'Mindoro', 'Quezon'],
        'optimal_ph': (6.0, 7.0), 'optimal_rainfall': (300, 800), 'optimal_temp': (15, 28), 'optimal_humidity': (45, 65), 'season': 'Dry', 'success_rate': 0.90
    },
    'Garlic': {
        'locations': ['Ilocos Norte', 'Ilocos Sur', 'Pangasinan', 'Nueva Ecija', 'Batanes', 'Mindoro'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (200, 600), 'optimal_temp': (13, 24), 'optimal_humidity': (40, 60), 'season': 'Dry', 'success_rate': 0.85
    },
    'Cabbage': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya', 'Batangas', 'Tagaytay'],
        'optimal_ph': (6.0, 7.0), 'optimal_rainfall': (500, 1200), 'optimal_temp': (10, 22), 'optimal_humidity': (60, 80), 'season': 'Both', 'success_rate': 0.88
    },
    'Bell Pepper': {
        'locations': ['Benguet', 'Nueva Vizcaya', 'Laguna', 'Batangas', 'Quezon', 'Mindoro'],
        'optimal_ph': (5.5, 6.5), 'optimal_rainfall': (400, 1000), 'optimal_temp': (15, 28), 'optimal_humidity': (50, 70), 'season': 'Both', 'success_rate': 0.82
    },
    'Chili': {
        'locations': ['Ilocos Sur', 'Ilocos Norte', 'Pangasinan', 'Nueva Ecija', 'Batangas', 'Quezon', 'Davao'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (400, 1200), 'optimal_temp': (20, 32), 'optimal_humidity': (50, 75), 'season': 'Both', 'success_rate': 0.86
    },
    'Squash': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Cagayan', 'Isabela', 'Quezon', 'Bohol', 'Negros'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.89
    },
    'Mung Bean': {
        'locations': ['Pangasinan', 'Tarlac', 'Nueva Ecija', 'Ilocos Norte', 'Cagayan', 'Isabela', 'Davao'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (300, 800), 'optimal_temp': (20, 32), 'optimal_humidity': (50, 70), 'season': 'Dry', 'success_rate': 0.84
    },
    'Peanut': {
        'locations': ['Pangasinan', 'Nueva Ecija', 'Tarlac', 'Ilocos Norte', 'Cagayan', 'Isabela', 'Davao'],
        'optimal_ph': (5.5, 6.5), 'optimal_rainfall': (400, 1000), 'optimal_temp': (22, 32), 'optimal_humidity': (50, 70), 'season': 'Both', 'success_rate': 0.83
    },
    'Sweet Potato': {
        'locations': ['Philippines'], 'optimal_ph': (4.5, 6.5), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (50, 75), 'season': 'Both', 'success_rate': 0.91
    },
    'Cassava': {
        'locations': ['Philippines'], 'optimal_ph': (4.5, 7.0), 'optimal_rainfall': (600, 2000), 'optimal_temp': (20, 35), 'optimal_humidity': (50, 80), 'season': 'Both', 'success_rate': 0.90
    },
    'Sugarcane': {
        'locations': ['Negros', 'Panay', 'Luzon', 'Mindanao', 'Pangasinan', 'Tarlac', 'Nueva Ecija'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1200, 2500), 'optimal_temp': (22, 35), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.93
    },
    'Banana': {
        'locations': ['Davao', 'Cebu', 'Luzon', 'Mindanao', 'Negros', 'Panay', 'Leyte'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1500, 2500), 'optimal_temp': (22, 32), 'optimal_humidity': (60, 85), 'season': 'Both', 'success_rate': 0.94
    },
    'Mango': {
        'locations': ['Guimaras', 'Iloilo', 'Cebu', 'Davao', 'Benguet', 'Pangasinan', 'Quezon'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (800, 1500), 'optimal_temp': (22, 32), 'optimal_humidity': (50, 70), 'season': 'Dry', 'success_rate': 0.88
    },
    'Pineapple': {
        'locations': ['Cebu', 'Benguet', 'Quezon', 'Mindoro', 'Davao', 'Luzon'],
        'optimal_ph': (4.5, 6.0), 'optimal_rainfall': (1000, 2000), 'optimal_temp': (22, 32), 'optimal_humidity': (60, 80), 'season': 'Both', 'success_rate': 0.91
    },
    'Coconut': {
        'locations': ['Philippines'], 'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1500, 3000), 'optimal_temp': (22, 32), 'optimal_humidity': (65, 85), 'season': 'Both', 'success_rate': 0.95
    },
    'Coffee': {
        'locations': ['Benguet', 'Kalinga', 'Ifugao', 'Mountain Province', 'Batangas', 'Davao', 'Cotabato'],
        'optimal_ph': (5.0, 6.0), 'optimal_rainfall': (1500, 2500), 'optimal_temp': (15, 25), 'optimal_humidity': (60, 80), 'season': 'Both', 'success_rate': 0.85
    },
    'Cacao': {
        'locations': ['Davao', 'Cotabato', 'South Cotabato', 'Mindanao', 'Cebu', 'Leyte'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1500, 2500), 'optimal_temp': (20, 30), 'optimal_humidity': (70, 85), 'season': 'Both', 'success_rate': 0.87
    },
    'Rubber': {
        'locations': ['Mindanao', 'Batangas', 'Mindoro', 'Palawan', 'Surigao'],
        'optimal_ph': (4.5, 6.5), 'optimal_rainfall': (1500, 3000), 'optimal_temp': (22, 32), 'optimal_humidity': (70, 85), 'season': 'Both', 'success_rate': 0.89
    },
    'Watermelon': {
        'locations': ['Pangasinan', 'Nueva Ecija', 'Ilocos Norte', 'Isabela', 'Quezon', 'Batangas'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (300, 800), 'optimal_temp': (22, 35), 'optimal_humidity': (45, 65), 'season': 'Both', 'success_rate': 0.86
    },
    'Cucumber': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Quezon', 'Batangas', 'Laguna'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (400, 1200), 'optimal_temp': (18, 30), 'optimal_humidity': (50, 75), 'season': 'Both', 'success_rate': 0.84
    },
    'Lettuce': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya', 'Tagaytay'],
        'optimal_ph': (6.0, 7.0), 'optimal_rainfall': (400, 1000), 'optimal_temp': (10, 20), 'optimal_humidity': (60, 80), 'season': 'Both', 'success_rate': 0.82
    },
    'Carrot': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (400, 1000), 'optimal_temp': (10, 25), 'optimal_humidity': (55, 75), 'season': 'Both', 'success_rate': 0.83
    },
    'Pole Sitao': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Cagayan', 'Isabela', 'Batangas'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.85
    },
    'Bush Sitao': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Cagayan', 'Isabela', 'Quezon'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.86
    },
    'Kangkong': {
        'locations': ['Philippines'], 'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (500, 2000), 'optimal_temp': (20, 35), 'optimal_humidity': (60, 90), 'season': 'Both', 'success_rate': 0.92
    },
    'Pechay': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya', 'Pangasinan', 'Batangas'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (400, 1200), 'optimal_temp': (10, 25), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.87
    },
    'Ginger': {
        'locations': ['Mindanao', 'Benguet', 'Nueva Vizcaya', 'Batangas', 'Quezon', 'Mindoro'],
        'optimal_ph': (5.5, 6.5), 'optimal_rainfall': (1500, 3000), 'optimal_temp': (20, 30), 'optimal_humidity': (70, 85), 'season': 'Both', 'success_rate': 0.88
    },
    'Turmeric': {
        'locations': ['Mindanao', 'Benguet', 'Nueva Vizcaya', 'Batangas', 'Quezon', 'Mindoro'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (1500, 3000), 'optimal_temp': (20, 32), 'optimal_humidity': (70, 85), 'season': 'Both', 'success_rate': 0.87
    },
    'Yam': {
        'locations': ['Philippines'], 'optimal_ph': (5.0, 6.5), 'optimal_rainfall': (800, 2000), 'optimal_temp': (20, 32), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.88
    },
    'Gabi': {
        'locations': ['Philippines'], 'optimal_ph': (5.0, 7.0), 'optimal_rainfall': (1000, 2500), 'optimal_temp': (22, 32), 'optimal_humidity': (60, 85), 'season': 'Both', 'success_rate': 0.89
    },
    'Ampalaya': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Ilocos Norte', 'Cagayan', 'Isabela', 'Batangas'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (50, 75), 'season': 'Both', 'success_rate': 0.85
    },
    'Patola': {
        'locations': ['Nueva Ecija', 'Pangasinan', 'Ilocos Sur', 'Cagayan', 'Isabela', 'Batangas'],
        'optimal_ph': (5.5, 6.8), 'optimal_rainfall': (500, 1500), 'optimal_temp': (20, 32), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.84
    },
    'Baguio Bean': {
        'locations': ['Benguet', 'Ifugao', 'Mountain Province', 'Nueva Vizcaya'],
        'optimal_ph': (5.5, 7.0), 'optimal_rainfall': (400, 1200), 'optimal_temp': (10, 22), 'optimal_humidity': (55, 80), 'season': 'Both', 'success_rate': 0.83
    }
}

# All Philippine locations
ALL_LOCATIONS = [
    'Philippines', 'Nueva Ecija', 'Pangasinan', 'Tarlac', 'Mindoro', 'Cagayan', 'Isabela', 
    'Ilocos Norte', 'Ilocos Sur', 'Laguna', 'Bohol', 'Negros', 'Benguet', 'Ifugao', 
    'Mountain Province', 'Nueva Vizcaya', 'Quezon', 'Batangas', 'Rizal', 'Batanes',
    'Bukidnon', 'Cotabato', 'South Cotabato', 'Davao', 'Cebu', 'Panay', 'Leyte',
    'Guimaras', 'Iloilo', 'Kalinga', 'Tagaytay', 'Palawan', 'Surigao', 'Luzon', 'Mindanao'
]

def generate_training_data(n_samples=50000):
    """Generate comprehensive training data based on Philippine agricultural research."""
    np.random.seed(42)
    data = []
    
    for _ in range(n_samples):
        # Random location
        location = np.random.choice(ALL_LOCATIONS)
        season = np.random.choice(['Wet', 'Dry'])
        
        # Generate environmental conditions based on season
        if season == 'Wet':
            rainfall = np.random.uniform(100, 400)
            temperature = np.random.uniform(22, 34)
            humidity = np.random.uniform(60, 95)
        else:
            rainfall = np.random.uniform(10, 150)
            temperature = np.random.uniform(20, 36)
            humidity = np.random.uniform(40, 80)
        
        # pH range
        ph = np.random.uniform(4.0, 8.0)
        
        # Determine best crop based on conditions
        best_crop = None
        best_score = -1
        
        for crop_name, crop_info in PHILIPPINE_CROP_DATA.items():
            # Check if location is suitable
            locations = crop_info['locations']
            location_suitable = (location in locations) or ('Philippines' in locations)
            
            # Check season suitability
            season_suitable = (crop_info['season'] == 'Both') or (crop_info['season'] == season)
            
            # Calculate environmental suitability
            ph_min, ph_max = crop_info['optimal_ph']
            rain_min, rain_max = crop_info['optimal_rainfall']
            temp_min, temp_max = crop_info['optimal_temp']
            hum_min, hum_max = crop_info['optimal_humidity']
            
            # Score calculation
            ph_score = 1.0 if ph_min <= ph <= ph_max else 0.5
            rain_score = 1.0 if rain_min <= rainfall <= rain_max else 0.5
            temp_score = 1.0 if temp_min <= temperature <= temp_max else 0.5
            hum_score = 1.0 if hum_min <= humidity <= hum_max else 0.5
            
            location_bonus = 1.2 if location_suitable else 0.8
            season_bonus = 1.2 if season_suitable else 0.8
            
            total_score = (ph_score + rain_score + temp_score + hum_score) / 4
            total_score *= location_bonus * season_bonus * crop_info['success_rate']
            
            if total_score > best_score:
                best_score = total_score
                best_crop = crop_name
        
        # Add noise (10% chance of random crop for realism)
        if np.random.random() < 0.10:
            best_crop = np.random.choice(list(PHILIPPINE_CROP_DATA.keys()))
        
        data.append({
            'location': location,
            'season': season,
            'ph': round(ph, 2),
            'rainfall': round(rainfall, 2),
            'temperature': round(temperature, 2),
            'humidity': round(humidity, 2),
            'crop': best_crop
        })
    
    return pd.DataFrame(data)

def train_model(df):
    """Train the ML model with high accuracy."""
    # Encode categorical variables
    location_encoder = LabelEncoder()
    season_encoder = LabelEncoder()
    crop_encoder = LabelEncoder()
    
    df['location_encoded'] = location_encoder.fit_transform(df['location'])
    df['season_encoded'] = season_encoder.fit_transform(df['season'])
    df['crop_encoded'] = crop_encoder.fit_transform(df['crop'])
    
    # Features
    X = df[['location_encoded', 'season_encoded', 'ph', 'rainfall', 'temperature', 'humidity']]
    y = df['crop_encoded']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest with optimized parameters
    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=25,
        min_samples_split=3,
        min_samples_leaf=1,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_accuracy = model.score(X_train, y_train)
    test_accuracy = model.score(X_test, y_test)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5)
    
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    print(f"Cross-validation Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    return model, {
        'location': location_encoder,
        'season': season_encoder,
        'crop': crop_encoder
    }

def main():
    print("=" * 60)
    print("Advanced Crop Prediction Model Training")
    print("Philippine Agricultural Research Data")
    print("=" * 60)
    
    # Generate training data
    print("\n1. Generating training data...")
    df = generate_training_data(50000)
    print(f"   Generated {len(df)} training samples")
    print(f"   Unique crops: {df['crop'].nunique()}")
    print(f"   Crops: {sorted(df['crop'].unique().tolist())}")
    
    # Train model
    print("\n2. Training model...")
    model, encoders = train_model(df)
    
    # Save model
    print("\n3. Saving model...")
    model_package = {
        'model': model,
        'encoders': encoders,
        'feature_cols': ['location_encoded', 'season_encoded', 'ph', 'rainfall', 'temperature', 'humidity'],
        'crop_data': PHILIPPINE_CROP_DATA
    }
    
    output_path = MODEL_DIR / 'crop_model.joblib'
    joblib.dump(model_package, output_path)
    print(f"   Model saved to: {output_path}")
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
