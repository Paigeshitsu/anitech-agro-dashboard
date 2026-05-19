"""
Open-Meteo Weather API Integration for ML Crop Recommendations
Fetches real-time and forecast weather data to generate optimized crop advice
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import joblib

MODEL_DIR = Path(__file__).parent / 'models'


def fetch_openmeteo_weather(latitude: float = 13.1431, longitude: float = 123.7438, days_forecast: int = 14) -> Dict:
    """
    Fetch real-time and forecast weather data from Open-Meteo API
    Default coordinates: Legazpi City, Albay, Philippines
    """
    base_url = "https://api.open-meteo.com/v1/forecast"

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'hourly': ['temperature_2m', 'relative_humidity_2m', 'precipitation', 'rain', 'soil_moisture_0_to_10cm', 'wind_speed_10m'],
        'daily': ['weather_code', 'temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'rain_sum', 'relative_humidity_2m_max', 'relative_humidity_2m_min', 'wind_speed_10m_max'],
        'forecast_days': days_forecast,
        'timezone': 'Asia/Manila'
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return {
            'location': {
                'latitude': latitude,
                'longitude': longitude,
                'timezone': data['timezone']
            },
            'current': {
                'temperature_c': data['hourly']['temperature_2m'][0],
                'humidity_pct': data['hourly']['relative_humidity_2m'][0],
                'precipitation_mm': data['hourly']['precipitation'][0],
                'soil_moisture': data['hourly']['soil_moisture_0_to_10cm'][0]
            },
            'daily_forecast': [
                {
                    'date': datetime.fromisoformat(d),
                    'weather_code': wc,
                    'temp_max': tmax,
                    'temp_min': tmin,
                    'precipitation_sum': precip,
                    'rain_sum': rain,
                    'humidity_max': hmax,
                    'humidity_min': hmin,
                    'wind_speed_max': wind
                }
                for d, wc, tmax, tmin, precip, rain, hmax, hmin, wind in zip(
                    data['daily']['time'],
                    data['daily']['weather_code'],
                    data['daily']['temperature_2m_max'],
                    data['daily']['temperature_2m_min'],
                    data['daily']['precipitation_sum'],
                    data['daily']['rain_sum'],
                    data['daily'].get('relative_humidity_2m_max', [50] * len(data['daily']['time'])),
                    data['daily'].get('relative_humidity_2m_min', [40] * len(data['daily']['time'])),
                    data['daily'].get('wind_speed_10m_max', [8] * len(data['daily']['time']))
                )
            ],
            'forecast_averages': {
                'avg_temp': np.mean(data['daily']['temperature_2m_max']),
                'avg_rain': np.mean(data['daily']['rain_sum']),
                'total_precipitation_forecast': np.sum(data['daily']['precipitation_sum']),
                'wet_days': sum(1 for x in data['daily']['rain_sum'] if x > 5)
            }
        }

    except Exception as e:
        print(f"Open-Meteo API Error: {e}")
        return {}


def generate_weather_based_recommendations(crop: str, location: str, weather_data: Dict = None) -> Dict:
    """
    Generate ML-powered crop recommendations based on live Open-Meteo weather data
    """
    if weather_data is None:
        # Default to Legazpi City, Albay, Philippines
        weather_data = fetch_openmeteo_weather()

    # Load crop care advisor
    from crop_care_advisor import get_crop_recommendations

    current_weather = weather_data.get('current', {})
    forecast = weather_data.get('forecast_averages', {})

    base_recommendations = get_crop_recommendations(
        crop=crop,
        location=location,
        current_weather=current_weather
    )

    # Apply weather forecast adjustments
    adjustments = []
    irrigation_adjustment = 1.0
    pest_risk_level = 'normal'

    if forecast.get('wet_days', 0) > 7:
        adjustments.append("⚠️ High rainfall forecast - reduce irrigation by 60%")
        irrigation_adjustment = 0.4
        pest_risk_level = 'high'

    if forecast.get('avg_temp', 28) > 32:
        adjustments.append("⚠️ High temperature forecast - increase irrigation frequency")
        irrigation_adjustment = 1.3
        pest_risk_level = 'high'

    if current_weather.get('soil_moisture', 0.3) > 0.5:
        adjustments.append("✅ Soil moisture levels optimal - no irrigation needed today")
        irrigation_adjustment = 0.0

    # Load trained forecast model for price prediction
    model_path = MODEL_DIR / 'market_price_forecast.joblib'
    predicted_price = None

    if model_path.exists():
        try:
            pkg = joblib.load(model_path)
            from market_price_predictor import predict_market_price
            price_forecast = predict_market_price(crop, location)
            predicted_price = price_forecast['predicted_price_php']
        except Exception as e:
            print(f"Error loading or using market price model: {e}")
            pass

    return {
        'crop': crop,
        'location': location,
        'weather_updated': datetime.now().isoformat(),
        'current_weather': current_weather,
        'forecast_summary': forecast,
        'recommendations': base_recommendations,
        'weather_adjustments': adjustments,
        'irrigation_multiplier': irrigation_adjustment,
        'pest_risk_level': pest_risk_level,
        'predicted_market_price_php': predicted_price,
        'actionable_tips': [
            "Check soil moisture before irrigating",
            f"Pest inspection: {'every 7 days (high risk)' if pest_risk_level == 'high' else 'every 14 days'}",
            "Apply nitrogen fertilizer before predicted rainfall events"
        ]
    }


if __name__ == '__main__':
    print("=" * 70)
    print("OPEN-METEO LIVE WEATHER INTEGRATION TEST")
    print("=" * 70)

    print("\nFetching live weather data for Legazpi City, Albay...")
    weather = fetch_openmeteo_weather()

    if weather:
        print(f"\n✅ Live weather data received")
        print(f"   Current Temperature: {weather['current']['temperature_c']:.1f}°C")
        print(f"   Current Humidity: {weather['current']['humidity_pct']:.0f}%")
        print(f"   14-Day Forecast Rain: {weather['forecast_averages']['total_precipitation_forecast']:.1f} mm")
        print(f"   Expected Wet Days: {weather['forecast_averages']['wet_days']}")

        print("\n\n✅ Generating weather-optimized recommendations for Rice:")
        recs = generate_weather_based_recommendations('Rice', 'Legazpi City, Albay', weather)

        print(f"\n🌾 Rice Care Recommendations (Weather Optimized):")
        print(f"   Irrigation Multiplier: {recs['irrigation_multiplier'] * 100:.0f}%")
        print(f"   Pest Risk Level: {recs['pest_risk_level'].upper()}")

        if recs['weather_adjustments']:
            print("\n📋 Weather Adjustments:")
            for adj in recs['weather_adjustments']:
                print(f"   {adj}")

        if recs['predicted_market_price_php']:
            print(f"\n💰 Predicted Market Price: ₱{recs['predicted_market_price_php']:.2f}/kg")

        print("\n✅ Open-Meteo integration active and working")
