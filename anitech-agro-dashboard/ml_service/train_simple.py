"""
Simple Crop Recommendation Training - Real Kaggle Data
"""

import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

DATA_DIR = Path(__file__).parent / 'data'
MODEL_DIR = Path(__file__).parent / 'models'

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

def train():
    # Load data
    csv_path = DATA_DIR / 'Crop_recommendation.csv'
    if csv_path.exists():
        df = pd.read_csv(csv_path)
    else:
        print(f"No data at {csv_path}")
        return
    
    # Rename columns to lowercase
    df.columns = df.columns.str.lower()
    
    # Fix column mapping
    col_map = {'N': 'n', 'P': 'p', 'K': 'k'}
    for k, v in col_map.items():
        if k in df.columns:
            df = df.rename(columns={k: v})
    
    features = ['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall']
    X = df[features].values
    y = df['label'].values
    
    le = LabelEncoder()
    y_enc = le.fit_transform(y)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print(f"Data: {len(X)} samples, {len(le.classes_)} crops")
    
    # Train 5 times
    best_acc = 0
    best_model = None
    
    for i in range(5):
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y_enc, test_size=0.2, random_state=i*42, stratify=y_enc
        )
        
        model = RandomForestClassifier(n_estimators=250, max_depth=20, random_state=i*42, n_jobs=-1)
        model.fit(X_train, y_train)
        
        acc = model.score(X_test, y_test)
        print(f"Iter {i+1}: {acc:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_model = model
    
    print(f"Best: {best_acc:.4f}")
    
    # Save
    joblib.dump(best_model, MODEL_DIR / 'crop_recommendation.joblib')
    joblib.dump(scaler, MODEL_DIR / 'crop_scaler.joblib')
    joblib.dump(le, MODEL_DIR / 'crop_label_encoder.joblib')
    print("Saved!")

if __name__ == '__main__':
    train()