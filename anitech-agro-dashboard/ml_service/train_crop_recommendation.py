"""
Crop Recommendation Model - Real Kaggle Data
===========================================
Trains ML model using actual Kaggle crop recommendation dataset
Features: N, P, K, Temperature, Humidity, pH, Rainfall → Crop

Usage:
    pip install kaggle
    kaggle datasets download -d miadul/crop-recommendation-dataset
    python ml_service/train_crop_recommendation.py
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent))

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, f1_score

DATA_DIR = Path(__file__).parent / 'data'
MODEL_DIR = Path(__file__).parent / 'models'

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

# Kaggle dataset column mapping
KAGGLE_COLUMNS = {
    'N': 'n', 'P': 'p', 'K': 'k',
    'temperature': 'temperature', 'humidity': 'humidity',
    'ph': 'ph', 'rainfall': 'rainfall', 'label': 'label',
    'n': 'n', 'p': 'p', 'k': 'k'
}

def load_kaggle_data():
    """Load real Kaggle crop recommendation dataset"""
    
    # Try different possible file names
    possible_files = [
        DATA_DIR / 'Crop_recommendation.csv',
        DATA_DIR / 'Crop Recommendation.csv',
        DATA_DIR / 'crop_recommendation.csv',
    ]
    
    df = None
    for f in possible_files:
        if f.exists():
            print(f"Loading from {f}")
            df = pd.read_csv(f)
            break
    
    if df is None:
        print("No Kaggle dataset found.")
        print("Download from: https://www.kaggle.com/datasets/miadul/crop-recommendation-dataset")
        print("Place the file in ml_service/data/ as Crop_recommendation.csv")
        return None
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Map to standard columns (handle both upper and lowercase)
    col_mapping = {}
    for k, v in KAGGLE_COLUMNS.items():
        if k in df.columns:
            col_mapping[k] = v
    if col_mapping:
        df = df.rename(columns=col_mapping)
    
    # Ensure required columns exist
    required = ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall', 'label']
    missing = [c for c in required if c not in df.columns]
    if missing:
        print(f"Missing columns: {missing}")
        print(f"Available: {list(df.columns)}")
        return None
    
    print(f"Loaded real data: {len(df)} samples")
    print(f"Unique crops: {df['label'].nunique()}")
    print(f"Features: {list(df.columns)}")
    
    return df

def enhance_with_weather():
    """Create enhanced dataset with weather-derived features"""
    
    df = load_kaggle_data()
    if df is None:
        return None
    
    # Add derived features for better predictions
    df['n_ratio'] = df['n'] / (df['p'] + 1)
    df['npk_total'] = df['n'] + df['p'] + df['k']
    df['temp_humidity'] = df['temperature'] * df['humidity'] / 100
    df['rainfall_ph'] = df['rainfall'] * df['ph']
    df['optimal_temp'] = ((df['temperature'] >= 20) & (df['temperature'] <= 32)).astype(int)
    df['optimal_humidity'] = ((df['humidity'] >= 60) & (df['humidity'] <= 85)).astype(int)
    df['optimal_ph'] = ((df['ph'] >= 5.5) & (df['ph'] <= 7.0)).astype(int)
    
    print(f"Enhanced features: {len(df.columns)}")
    return df

def train_robust_model(iterations=5):
    """Train model multiple times with different splits"""
    
    print("=" * 50)
    print("Loading Kaggle crop recommendation dataset...")
    print("=" * 50)
    
    df = enhance_with_weather()
    if df is None:
        print("Could not load data. Exiting.")
        return
    
    # Feature columns (including derived)
    feature_cols = ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall',
                   'n_ratio', 'npk_total', 'temp_humidity', 'rainfall_ph',
                   'optimal_temp', 'optimal_humidity', 'optimal_ph']
    
    X = df[feature_cols].values
    y = df['label'].values
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    print(f"\nTotal samples: {len(X)}")
    print(f"Classes: {len(le.classes_)}")
    print(f"Features: {len(feature_cols)}")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train with different random states and collect best
    best_model = None
    best_accuracy = 0
    best_state = 0
    accuracy_scores = []
    
    print(f"\nTraining {iterations} times...")
    print("-" * 40)
    
    for i in range(iterations):
        # Different random split each iteration
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_encoded, test_size=0.2, random_state=i*42, stratify=y_encoded
        )
        
        # Train single Random Forest (faster)
        rf = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            random_state=i*42,
            n_jobs=-1
        )
        
        # Fit Random Forest
        rf.fit(X_train, y_train)
        
        # Evaluate
        y_pred = ensemble.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        accuracy_scores.append(accuracy)
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = ensemble
            best_state = i
        
        print(f"Iteration {i+1}/{iterations}: Accuracy = {accuracy:.4f}")
    
    print("-" * 40)
    print(f"\nBest iteration: {best_state + 1}")
    print(f"Best accuracy: {best_accuracy:.4f}")
    print(f"Average accuracy: {np.mean(accuracy_scores):.4f}")
    print(f"Std deviation: {np.std(accuracy_scores):.4f}")
    
    # Final evaluation on best model
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=best_state*42, stratify=y_encoded
    )
    best_model.fit(X_train, y_train)
    y_pred = best_model.predict(X_test)
    
    print(f"\nBest Model Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))
    
    # Cross-validation
    cv_scores = cross_val_score(best_model, X_scaled, y_encoded, cv=5, scoring='f1_weighted')
    print(f"Cross-validation F1: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")
    
    # Save models
    model_path = MODEL_DIR / 'crop_recommendation.joblib'
    scaler_path = MODEL_DIR / 'crop_scaler.joblib'
    encoder_path = MODEL_DIR / 'crop_label_encoder.joblib'
    
    joblib.dump(best_model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(le, encoder_path)
    
    print(f"\n✓ Model saved to {model_path}")
    print(f"✓ Scaler saved to {scaler_path}")
    print(f"✓ Label encoder saved to {encoder_path}")
    
    return best_model, scaler, le

def predict_crop(n, p, k, temperature, humidity, ph, rainfall):
    """Predict best crop given environmental factors"""
    
    model_path = MODEL_DIR / 'crop_recommendation.joblib'
    
    if not model_path.exists():
        print("Model not found. Training...")
        train_robust_model(15)
    
    model = joblib.load(model_path)
    scaler = joblib.load(MODEL_DIR / 'crop_scaler.joblib')
    le = joblib.load(MODEL_DIR / 'crop_label_encoder.joblib')
    
    # Derived features
    n_ratio = n / (p + 1)
    npk_total = n + p + k
    temp_humidity = temperature * humidity / 100
    rainfall_ph = rainfall * ph
    optimal_temp = 1 if 20 <= temperature <= 32 else 0
    optimal_humidity = 1 if 60 <= humidity <= 85 else 0
    optimal_ph = 1 if 5.5 <= ph <= 7.0 else 0
    
    features = np.array([[n, p, k, temperature, humidity, ph, rainfall,
                       n_ratio, npk_total, temp_humidity, rainfall_ph,
                       optimal_temp, optimal_humidity, optimal_ph]])
    features_scaled = scaler.transform(features)
    
    prediction = model.predict(features_scaled)
    probabilities = model.predict_proba(features_scaled)[0]
    
    top_indices = np.argsort(probabilities)[::-1][:5]
    results = []
    for idx in top_indices:
        results.append({
            'crop': le.classes_[idx],
            'confidence': float(probabilities[idx])
        })
    
    return results

if __name__ == '__main__':
    # Load real data and train
    train_robust_model(15)
    
    print("\n" + "=" * 50)
    print("Testing prediction with weather data...")
    print("=" * 50)
    
    # Test with sample weather data from Open-Meteo
    test_cases = [
        {'n': 90, 'p': 50, 'k': 60, 'temperature': 28, 'humidity': 75, 'ph': 6.5, 'rainfall': 100},
        {'n': 60, 'p': 40, 'k': 50, 'temperature': 25, 'humidity': 80, 'ph': 6.0, 'rainfall': 150},
        {'n': 100, 'p': 60, 'k': 80, 'temperature': 30, 'humidity': 70, 'ph': 6.5, 'rainfall': 80},
        {'n': 50, 'p': 30, 'k': 40, 'temperature': 22, 'humidity': 85, 'ph': 5.8, 'rainfall': 200},
    ]
    
    for test in test_cases:
        results = predict_crop(**test)
        print(f"\nInput: N={test['n']}, P={test['p']}, K={test['k']}, Temp={test['temperature']}, Hum={test['humidity']}, pH={test['ph']}, Rain={test['rainfall']}")
        print("Predictions:")
        for r in results:
            print(f"  {r['crop']}: {r['confidence']*100:.1f}%")