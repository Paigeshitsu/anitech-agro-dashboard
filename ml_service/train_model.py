"""
ML Model Training Script for Crop Prediction
============================================
This script trains a machine learning model to predict crop recommendations
based on environmental factors (location, season, pH, rainfall, temperature, humidity).

Usage:
    python ml_service/train_model.py
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to import sklearn
sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# Define the data directory
DATA_DIR = Path(__file__).parent / 'data'
MODEL_DIR = Path(__file__).parent / 'models'

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Sample training data for crop prediction
# In a production system, you would use actual historical data
def create_sample_data():
    """
    Create sample training data for crop prediction.
    Replace this with actual historical data for better predictions.
    """
    np.random.seed(42)
    
    # Define locations and seasons
    locations = ['Laguna', 'Bicol', 'Manila', 'Cebu', 'Davao', 'Pangasinan', 'Nueva Ecija', 'Tarlac']
    seasons = ['Wet', 'Dry']
    
    # Define crops suitable for Philippine climate
    crops = [
        'Rice', 'Corn', 'Tomato', 'Eggplant', 'Onion', 
        'Garlic', 'Cabbage', 'Bell Pepper', 'Chili', 'Squash',
        'Bean', 'Mung Bean', 'Peanut', 'Sweet Potato', 'Cassava'
    ]
    
    # Create synthetic training data
    n_samples = 5000
    data = []
    
    for _ in range(n_samples):
        location = np.random.choice(locations)
        season = np.random.choice(seasons)
        
        # Generate environmental conditions based on season
        if season == 'Wet':
            rainfall = np.random.uniform(150, 350)
            temperature = np.random.uniform(24, 32)
            humidity = np.random.uniform(70, 95)
        else:
            rainfall = np.random.uniform(10, 80)
            temperature = np.random.uniform(22, 35)
            humidity = np.random.uniform(50, 80)
        
        # pH typically ranges from 4.5 to 8.5 in Philippine soils
        ph = np.random.uniform(5.0, 7.5)
        
        # Determine suitable crop based on conditions (simplified rules for training)
        if ph < 5.5:
            if rainfall > 200:
                crop = np.random.choice(['Rice', 'Corn'])
            else:
                crop = np.random.choice(['Sweet Potato', 'Cassava'])
        elif ph < 6.5:
            if temperature > 28:
                crop = np.random.choice(['Corn', 'Tomato', 'Eggplant', 'Pepper'])
            else:
                crop = np.random.choice(['Cabbage', 'Lettuce', 'Bean'])
        else:
            crop = np.random.choice(['Onion', 'Garlic', 'Chili', 'Squash'])
        
        # Add some randomness/noise
        if np.random.random() < 0.1:
            crop = np.random.choice(crops)
        
        data.append({
            'location': location,
            'season': season,
            'ph': ph,
            'rainfall': rainfall,
            'temperature': temperature,
            'humidity': humidity,
            'crop': crop
        })
    
    return pd.DataFrame(data)


def preprocess_data(df):
    """
    Preprocess the training data by encoding categorical variables.
    """
    # Encode location
    location_encoder = LabelEncoder()
    df['location_encoded'] = location_encoder.fit_transform(df['location'])
    
    # Encode season
    season_encoder = LabelEncoder()
    df['season_encoded'] = season_encoder.fit_transform(df['season'])
    
    # Encode crop (target variable)
    crop_encoder = LabelEncoder()
    df['crop_encoded'] = crop_encoder.fit_transform(df['crop'])
    
    # Save encoders for inference
    encoders = {
        'location': location_encoder,
        'season': season_encoder,
        'crop': crop_encoder
    }
    
    return df, encoders


def train_model(df):
    """
    Train a Random Forest classifier for crop prediction.
    """
    # Feature columns (use encoded values)
    feature_cols = ['location_encoded', 'season_encoded', 'ph', 'rainfall', 'temperature', 'humidity']
    
    X = df[feature_cols]
    y = df['crop_encoded']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Random Forest model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_accuracy = model.score(X_train, y_train)
    test_accuracy = model.score(X_test, y_test)
    
    print(f"Training Accuracy: {train_accuracy:.4f}")
    print(f"Test Accuracy: {test_accuracy:.4f}")
    
    return model


def save_model(model, encoders, output_path):
    """
    Save the trained model along with encoders.
    """
    # Create a wrapper that includes the model and encoders
    model_package = {
        'model': model,
        'encoders': encoders,
        'feature_cols': ['location_encoded', 'season_encoded', 'ph', 'rainfall', 'temperature', 'humidity']
    }
    
    joblib.dump(model_package, output_path)
    print(f"Model saved to: {output_path}")


def main():
    print("=" * 60)
    print("Crop Prediction Model Training")
    print("=" * 60)
    
    # Create sample data
    print("\n1. Creating training data...")
    df = create_sample_data()
    print(f"   Created {len(df)} training samples")
    print(f"   Crops: {df['crop'].unique().tolist()}")
    
    # Preprocess data
    print("\n2. Preprocessing data...")
    df, encoders = preprocess_data(df)
    print("   Encoded categorical variables")
    
    # Train model
    print("\n3. Training model...")
    model = train_model(df)
    
    # Save model
    output_path = MODEL_DIR / 'crop_model.joblib'
    print(f"\n4. Saving model to {output_path}...")
    save_model(model, encoders, output_path)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)
    print(f"\nTo use the model, place '{output_path}' in the ml_service/models/ directory.")
    print("The ML prediction feature should now work in your Django application.")


if __name__ == '__main__':
    main()
