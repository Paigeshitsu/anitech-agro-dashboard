"""
Optimized Hyperparameter Training for 98% Accuracy Target
"""
import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import GridSearchCV, KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

sys.path.insert(0, str(Path(__file__).parent.parent))
from market_price_predictor import generate_enhanced_training_data

MODEL_DIR = Path(__file__).parent / 'models'
TARGET_ACCURACY = 0.98


def optimize_hyperparameters():
    print("=" * 75)
    print("OPTIMIZED TRAINING FOR 98% ACCURACY TARGET")
    print("=" * 75)

    df = generate_enhanced_training_data()

    # Encode all categorical fields
    from sklearn.preprocessing import LabelEncoder
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

    # Hyperparameter grid optimized for maximum accuracy
    param_grid = {
        'n_estimators': [600, 800, 1000],
        'max_depth': [12, 14, 16],
        'learning_rate': [0.03, 0.04, 0.05],
        'subsample': [0.90, 0.92, 0.95],
        'colsample_bytree': [0.85, 0.88, 0.90],
        'gamma': [0.0, 0.1, 0.2]
    }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)

    model = XGBRegressor(
        min_child_weight=1,
        random_state=42,
        n_jobs=-1,
        verbosity=0
    )

    print(f"\nStarting GridSearchCV with {kf.get_n_splits()} folds...")
    print(f"Total parameter combinations: {np.prod([len(v) for v in param_grid.values()])}")

    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=kf,
        scoring='r2',
        n_jobs=-1,
        verbose=2
    )

    grid_search.fit(X, y)

    print(f"\n✅ BEST PARAMETERS FOUND:")
    print(grid_search.best_params_)
    print(f"\n✅ BEST CROSS VALIDATION SCORE: {grid_search.best_score_:.5f}")

    best_model = grid_search.best_estimator_

    # Final evaluation
    y_pred = best_model.predict(X)
    final_r2 = r2_score(y, y_pred)
    print(f"\n✅ FINAL FULL DATASET R² SCORE: {final_r2:.5f}")

    # Save optimized model
    model_package = {
        'model': best_model,
        'encoders': encoders,
        'feature_cols': feature_cols,
        'best_params': grid_search.best_params_,
        'accuracy_r2': final_r2,
        'training_date': datetime.now().isoformat()
    }

    output_path = MODEL_DIR / 'optimized_market_price_model.joblib'
    joblib.dump(model_package, output_path, compress=3)
    print(f"\n✅ Optimized model saved to: {output_path}")

    if final_r2 >= TARGET_ACCURACY:
        print(f"\n🎉 TARGET 98% ACCURACY ACHIEVED!")
    else:
        print(f"\nℹ️  Current accuracy: {final_r2*100:.2f}% (need {TARGET_ACCURACY*100:.2f}%)")

    return best_model, final_r2


if __name__ == '__main__':
    best_model, score = optimize_hyperparameters()
