"""
Crop Care & Management Recommendation Engine
Provides optimized planting, irrigation, fertilization, pest control advice for maximum yield
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List

MODEL_DIR = Path(__file__).parent / 'models'

# Optimized crop management protocols based on Philippine agricultural standards
CROP_MANAGEMENT_PROTOCOLS = {
    'Rice': {
        'planting_depth_cm': 2,
        'plant_spacing_cm': 20,
        'row_spacing_cm': 30,
        'irrigation_frequency_days': 2,
        'irrigation_mm': 50,
        'nitrogen_kg_ha': 120,
        'phosphorus_kg_ha': 40,
        'potassium_kg_ha': 40,
        'pest_control_interval_days': 14,
        'growth_stages': {
            'vegetative': {'days': 35, 'water_level_cm': 5},
            'reproductive': {'days': 30, 'water_level_cm': 10},
            'ripening': {'days': 30, 'water_level_cm': 2, 'drain': True}
        },
        'best_planting_months': [1, 2, 6, 7],
        'harvest_days': 115
    },
    'Corn': {
        'planting_depth_cm': 5,
        'plant_spacing_cm': 25,
        'row_spacing_cm': 75,
        'irrigation_frequency_days': 5,
        'irrigation_mm': 40,
        'nitrogen_kg_ha': 150,
        'phosphorus_kg_ha': 60,
        'potassium_kg_ha': 60,
        'pest_control_interval_days': 18,
        'growth_stages': {
            'vegetative': {'days': 40, 'irrigation_freq': 7},
            'flowering': {'days': 20, 'irrigation_freq': 3},
            'grain_fill': {'days': 30, 'irrigation_freq': 5}
        },
        'best_planting_months': [1, 5, 9],
        'harvest_days': 110
    },
    'Tomato': {
        'planting_depth_cm': 1,
        'plant_spacing_cm': 45,
        'row_spacing_cm': 90,
        'irrigation_frequency_days': 3,
        'irrigation_mm': 35,
        'nitrogen_kg_ha': 100,
        'phosphorus_kg_ha': 80,
        'potassium_kg_ha': 150,
        'pest_control_interval_days': 10,
        'best_planting_months': [10, 11, 12],
        'harvest_days': 75
    },
    'Onion': {
        'planting_depth_cm': 3,
        'plant_spacing_cm': 10,
        'row_spacing_cm': 30,
        'irrigation_frequency_days': 4,
        'irrigation_mm': 25,
        'nitrogen_kg_ha': 90,
        'phosphorus_kg_ha': 60,
        'potassium_kg_ha': 70,
        'pest_control_interval_days': 12,
        'best_planting_months': [11, 12],
        'harvest_days': 100
    },
    'Garlic': {
        'planting_depth_cm': 4,
        'plant_spacing_cm': 12,
        'row_spacing_cm': 30,
        'irrigation_frequency_days': 7,
        'irrigation_mm': 20,
        'nitrogen_kg_ha': 80,
        'phosphorus_kg_ha': 50,
        'potassium_kg_ha': 60,
        'pest_control_interval_days': 16,
        'best_planting_months': [10, 11],
        'harvest_days': 120
    }
}

WEATHER_IMPACT_ADJUSTMENT = {
    'rainfall_high': {'irrigation_reduction_pct': 70},
    'rainfall_low': {'irrigation_increase_pct': 40},
    'temperature_high': {'pest_risk_increase': 1.35},
    'humidity_high': {'fungicide_required': True},
    'typhoon_season': {'windbreak_required': True, 'early_harvest': True}
}


def load_forecast_model():
    forecast_path = MODEL_DIR / 'market_price_forecast.joblib'
    if forecast_path.exists():
        try:
            return joblib.load(forecast_path)
        except Exception as e:
            print(f"Error loading forecast model: {e}")
            return None
    return None


def get_crop_recommendations(crop: str, location: str, season: str = None,
                              current_weather: Dict = None) -> Dict:
    """
    Generate complete crop care and management recommendations for maximum yield

    Args:
        crop: Name of crop
        location: Philippine location
        season: wet/dry/transition
        current_weather: dict with rainfall_mm, temperature_c, humidity_pct

    Returns:
        Complete care schedule with optimization recommendations
    """
    protocol = CROP_MANAGEMENT_PROTOCOLS.get(crop, CROP_MANAGEMENT_PROTOCOLS['Rice'])
    month = datetime.now().month

    if season is None:
        season = 'wet' if 6 <= month <= 11 else 'dry'

    adjustments = {}

    # Apply weather based adjustments
    if current_weather:
        if current_weather.get('rainfall_mm', 0) > 250:
            adjustments['irrigation_reduction'] = 70
            adjustments['note'] = 'Reduce irrigation by 70% due to high rainfall'
        if current_weather.get('rainfall_mm', 100) < 50:
            adjustments['irrigation_increase'] = 40
            adjustments['note'] = 'Increase irrigation by 40% due to drought conditions'
        if current_weather.get('temperature_c', 28) > 33:
            adjustments['pest_risk'] = 'high'
            adjustments['pest_check_interval'] = 7
        if current_weather.get('humidity_pct', 75) > 90:
            adjustments['fungicide_needed'] = True

    # Planting recommendation
    optimal_month = min(protocol['best_planting_months'], key=lambda m: abs(m - month))
    months_until_optimal = (optimal_month - month) % 12

    return {
        'crop': crop,
        'location': location,
        'season': season,
        'recommended': {
            'planting': {
                'depth_cm': protocol['planting_depth_cm'],
                'plant_spacing_cm': protocol['plant_spacing_cm'],
                'row_spacing_cm': protocol['row_spacing_cm'],
                'optimal_planting_month': optimal_month,
                'months_until_best_planting': months_until_optimal,
                'plant_now_recommended': months_until_optimal <= 2
            },
            'irrigation': {
                'frequency_days': protocol['irrigation_frequency_days'],
                'water_volume_mm': protocol['irrigation_mm'],
                'adjustments': adjustments
            },
            'fertilization': {
                'nitrogen_kg_ha': protocol['nitrogen_kg_ha'],
                'phosphorus_kg_ha': protocol['phosphorus_kg_ha'],
                'potassium_kg_ha': protocol['potassium_kg_ha'],
                'application_schedule': 'Split into 3 equal applications: planting, 30 days, 60 days'
            },
            'pest_control': {
                'inspection_interval_days': protocol['pest_control_interval_days'],
                'recommended_products': ['Deltamethrin', 'Chlorpyrifos', 'Mancozeb'],
                'high_risk_period': 'First 45 days after planting'
            },
            'growth_stages': protocol['growth_stages'],
            'expected_harvest_days': protocol['harvest_days']
        },
        'max_yield_optimization_tips': [
            'Maintain consistent water level during critical growth stages',
            'Apply fertilizer at root zone, avoid leaf burn',
            'Monitor for pest symptoms every 7 days during wet season',
            'Harvest at optimal moisture content for maximum market price'
        ]
    }


def get_crop_schedule_timeline(crop: str) -> List[Dict]:
    """Generate day by day crop management timeline"""
    protocol = CROP_MANAGEMENT_PROTOCOLS.get(crop, CROP_MANAGEMENT_PROTOCOLS['Rice'])
    timeline = []

    # Planting day
    timeline.append({
        'day': 0,
        'stage': 'Planting',
        'actions': ['Seed sowing', 'Basal fertilizer application', 'Initial irrigation']
    })

    day = 7
    while day <= protocol['harvest_days']:
        actions = []

        if day % protocol['irrigation_frequency_days'] == 0:
            actions.append('Irrigation')

        if day % protocol['pest_control_interval_days'] == 0:
            actions.append('Pest inspection')

        if day in [30, 60]:
            actions.append('Fertilizer top dressing')

        if actions:
            timeline.append({
                'day': day,
                'actions': actions
            })

        day += 7

    timeline.append({
        'day': protocol['harvest_days'],
        'stage': 'Harvest',
        'actions': ['Stop irrigation 7 days before', 'Harvest at optimal moisture']
    })

    return timeline


if __name__ == '__main__':
    print("=" * 70)
    print("CROP CARE ADVISOR ENGINE")
    print("=" * 70)

    # Test recommendation output
    test_recommendation = get_crop_recommendations('Rice', 'Infanta')

    print(f"\n✅ Crop Care Recommendations for Rice (Infanta):")
    print(f"   Planting Depth: {test_recommendation['recommended']['planting']['depth_cm']} cm")
    print(f"   Plant Spacing: {test_recommendation['recommended']['planting']['plant_spacing_cm']} cm")
    print(f"   Irrigation: Every {test_recommendation['recommended']['irrigation']['frequency_days']} days")
    print(f"   Harvest Days: {test_recommendation['recommended']['expected_harvest_days']} days")

    print("\n✅ Crop care recommendation engine active and ready")
