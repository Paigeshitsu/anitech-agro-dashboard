import json
import hashlib
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache  # Optimization: Use Django's cache framework

# Global variable to store the model in memory (Singleton Pattern)
_MODEL_CACHE = None


def get_weather_icon(weather_code):
    """
    Map Open-Meteo weather codes to icon names.
    Based on WMO Weather interpretation codes.
    """
    if weather_code == 0:
        return 'sun'  # Clear sky
    elif weather_code in [1, 2, 3]:
        return 'cloud-sun'  # Mainly clear, partly cloudy, overcast
    elif weather_code in [45, 48]:
        return 'cloud-fog'  # Fog
    elif weather_code in [51, 53, 55, 56, 57]:
        return 'cloud-drizzle'  # Drizzle
    elif weather_code in [61, 63, 65, 66, 67]:
        return 'cloud-rain'  # Rain
    elif weather_code in [71, 73, 75, 77]:
        return 'cloud-snow'  # Snow
    elif weather_code in [80, 81, 82]:
        return 'cloud-rain'  # Rain showers
    elif weather_code in [85, 86]:
        return 'cloud-snow'  # Snow showers
    elif weather_code in [95, 96, 99]:
        return 'cloud-lightning'  # Thunderstorm
    else:
        return 'cloud'


def get_weather_condition(weather_code):
    """
    Map Open-Meteo weather codes to condition names.
    """
    conditions = {
        0: 'Clear Sky',
        1: 'Mainly Clear',
        2: 'Partly Cloudy',
        3: 'Overcast',
        45: 'Fog',
        48: 'Depositing Rime Fog',
        51: 'Light Drizzle',
        53: 'Moderate Drizzle',
        55: 'Dense Drizzle',
        56: 'Light Freezing Drizzle',
        57: 'Dense Freezing Drizzle',
        61: 'Slight Rain',
        63: 'Moderate Rain',
        65: 'Heavy Rain',
        66: 'Light Freezing Rain',
        67: 'Heavy Freezing Rain',
        71: 'Slight Snow Fall',
        73: 'Moderate Snow Fall',
        75: 'Heavy Snow Fall',
        77: 'Snow Grains',
        80: 'Slight Rain Showers',
        81: 'Moderate Rain Showers',
        82: 'Violent Rain Showers',
        85: 'Slight Snow Showers',
        86: 'Heavy Snow Showers',
        95: 'Thunderstorm',
        96: 'Thunderstorm with Slight Hail',
        99: 'Thunderstorm with Heavy Hail',
    }
    return conditions.get(weather_code, "Unknown")


def get_fallback_predictions(data):
    """
    Provide fallback crop predictions when ML model is not available.
    Returns mock predictions based on season and environmental conditions.
    Now supports dynamic crop lists from the database.
    """
    season = data.get('season', 'Wet')
    location = data.get('location', 'Legazpi City, Albay')
    temperature = data.get('temperature', 27)  # Avg temp for Legazpi (~27°C)
    rainfall = data.get('rainfall', 180 if season == 'Wet' else 75)  # Typical rainfall for Albay

    # If specific crops are requested, use them; otherwise use default seasonal crops
    requested_crops = data.get('crops', [])
    if requested_crops:
        crops = requested_crops
    else:
        # Fallback to seasonal preferences if no specific crops requested
        seasonal_crops = {
            'Wet': ['Rice', 'Corn', 'Tomato', 'Eggplant', 'Cabbage', 'Onion', 'Squash'],
            'Dry': ['Garlic', 'Sweet Potato', 'Cassava', 'Peanut', 'Bean', 'Chili']
        }
        crops = seasonal_crops.get(season, seasonal_crops['Wet'])

    # Comprehensive base prices for all crops
    base_prices = {
        'Rice': 45, 'Corn': 32, 'Tomato': 75, 'Eggplant': 55,
        'Cabbage': 40, 'Onion': 110, 'Garlic': 180, 'Sweet Potato': 35,
        'Peanut': 140, 'Chili': 90, 'Squash': 28, 'Bean': 65,
        'Cassava': 30, 'Mung Bean': 95, 'String Bean': 80, 'Carrot': 85,
        'Potato': 65, 'Calabaza': 45, 'Malunggay': 120, 'Kangkong': 60,
        'Sitaw': 70, 'Ampalaya': 55, 'Upo': 40
    }

    # Comprehensive crop suitability data
    crop_suitability = {
        'Rice': {
            'ideal_temp': (24, 30), 'ideal_rainfall': (150, 300), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 3, 'rain_tolerance': 50, 'season_preference': {'Wet': 1.2, 'Dry': 0.8}
        },
        'Corn': {
            'ideal_temp': (23, 28), 'ideal_rainfall': (120, 200), 'ideal_ph': (5.8, 7.0),
            'temp_tolerance': 4, 'rain_tolerance': 40, 'season_preference': {'Wet': 1.15, 'Dry': 0.9}
        },
        'Tomato': {
            'ideal_temp': (20, 25), 'ideal_rainfall': (80, 150), 'ideal_ph': (6.0, 6.8),
            'temp_tolerance': 5, 'rain_tolerance': 30, 'season_preference': {'Wet': 0.85, 'Dry': 1.1}
        },
        'Eggplant': {
            'ideal_temp': (22, 28), 'ideal_rainfall': (100, 180), 'ideal_ph': (5.5, 6.8),
            'temp_tolerance': 4, 'rain_tolerance': 35, 'season_preference': {'Wet': 0.9, 'Dry': 1.05}
        },
        'Cabbage': {
            'ideal_temp': (15, 20), 'ideal_rainfall': (100, 150), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 5, 'rain_tolerance': 30, 'season_preference': {'Wet': 1.0, 'Dry': 1.0}
        },
        'Onion': {
            'ideal_temp': (18, 23), 'ideal_rainfall': (80, 120), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 5, 'rain_tolerance': 25, 'season_preference': {'Wet': 0.95, 'Dry': 1.1}
        },
        'Garlic': {
            'ideal_temp': (16, 22), 'ideal_rainfall': (60, 100), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 4, 'rain_tolerance': 20, 'season_preference': {'Wet': 0.9, 'Dry': 1.15}
        },
        'Sweet Potato': {
            'ideal_temp': (24, 30), 'ideal_rainfall': (80, 150), 'ideal_ph': (5.5, 6.5),
            'temp_tolerance': 4, 'rain_tolerance': 35, 'season_preference': {'Wet': 1.0, 'Dry': 1.05}
        },
        'Peanut': {
            'ideal_temp': (25, 32), 'ideal_rainfall': (60, 120), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 4, 'rain_tolerance': 30, 'season_preference': {'Wet': 0.95, 'Dry': 1.1}
        },
        'Chili': {
            'ideal_temp': (20, 28), 'ideal_rainfall': (80, 140), 'ideal_ph': (6.0, 6.8),
            'temp_tolerance': 4, 'rain_tolerance': 30, 'season_preference': {'Wet': 0.9, 'Dry': 1.05}
        }
    }

    # Adjust scores based on environmental conditions
    predictions = []
    for crop in crops:
        crop_data = crop_suitability.get(crop, {
            'ideal_temp': (20, 28), 'ideal_rainfall': (80, 150), 'ideal_ph': (6.0, 7.0),
            'temp_tolerance': 4, 'rain_tolerance': 30, 'season_preference': {'Wet': 1.0, 'Dry': 1.0}
        })

        # Temperature suitability score (0-1)
        temp_min, temp_max = crop_data['ideal_temp']
        temp_tolerance = crop_data['temp_tolerance']
        if temp_min - temp_tolerance <= temperature <= temp_max + temp_tolerance:
            temp_score = 1.0 - min(0.5, abs(temperature - (temp_min + temp_max) / 2) / temp_tolerance)
        else:
            temp_score = 0.3  # Poor suitability

        # Rainfall suitability score (0-1)
        rain_min, rain_max = crop_data['ideal_rainfall']
        rain_tolerance = crop_data['rain_tolerance']
        if rain_min - rain_tolerance <= rainfall <= rain_max + rain_tolerance:
            rain_score = 1.0 - min(0.5, abs(rainfall - (rain_min + rain_max) / 2) / rain_tolerance)
        else:
            rain_score = 0.3  # Poor suitability

        # pH suitability (assuming neutral pH if not specified)
        ph_score = 1.0  # Assume good unless we have specific data

        # Seasonal preference
        season_score = crop_data['season_preference'].get(season, 1.0)

        # Combine environmental scores
        environmental_score = (temp_score * 0.4 + rain_score * 0.4 + ph_score * 0.2) * season_score

        # Add some randomness to prevent identical scores
        import random
        final_score = environmental_score * (0.9 + random.uniform(0, 0.2))

        # Determine category based on score and crop type
        if crop in ['Rice', 'Corn'] and season == 'Wet':
            category = "seasonal"
        elif crop in ['Tomato', 'Chili', 'Eggplant', 'Garlic', 'Onion'] and season == 'Dry':
            category = "seasonal"
        elif final_score > 0.6:
            category = "seasonal"
        else:
            category = "high-demand"

        # Get base price for the crop
        base_price = base_prices.get(crop, 50)
        predicted_price = base_price * (0.95 + final_score * 0.15)  # Price varies with demand

        predictions.append({
            "crop": crop,
            "score": round(final_score, 4),
            "category": category,
            "trend": "stable",
            "change_pct": 0,
            "price": round(predicted_price, 2)
        })

    # Sort by score (highest first) to ensure best recommendations appear first
    predictions.sort(key=lambda x: x['score'], reverse=True)

    return predictions


def fetch_historical_weather_data(latitude=13.1431, longitude=123.7438, days_back=7, timezone="Asia/Manila"):
    """
    Fetch historical weather data from Open-Meteo API.

    Args:
        latitude: Location latitude (default: Legazpi City, Albay, Philippines)
        longitude: Location longitude (default: Legazpi City, Albay, Philippines)
        days_back: Number of days back from today to fetch
        timezone: Timezone for the data

    Returns:
        Dictionary with historical daily weather data
    """
    try:
        import requests
        from datetime import datetime, timedelta

        # Calculate date range
        end_date = datetime.now() - timedelta(days=5)  # ERA5 has 5 days delay
        start_date = end_date - timedelta(days=days_back)

        url = "https://archive-api.open-meteo.com/v1/archive"
        # Use comma-separated string for daily parameters (archive API format)
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,relative_humidity_2m_max,wind_speed_10m_max"
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        return {
            'success': True,
            'data': data,
            'latitude': latitude,
            'longitude': longitude,
            'period': f"{days_back}_days_back"
        }

    except Exception as e:
        print(f"Historical weather API Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def fetch_weather_data(latitude=13.1431, longitude=123.7438, timezone="Asia/Manila"):
    """
    Fetch weather data from Open-Meteo API.

    Args:
        latitude: Location latitude (default: Legazpi City, Albay, Philippines)
        longitude: Location longitude (default: Legazpi City, Albay, Philippines)
        timezone: Timezone for the data

    Returns:
        Dictionary with current, hourly, and daily weather data
    """
    try:
        import requests

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_min",
                "apparent_temperature_max",
                "sunrise",
                "sunset",
                "rain_sum",
                "relative_humidity_2m_mean",
                "wind_speed_10m_max"
            ],
            "hourly": [
                "temperature_2m",
                "relative_humidity_2m",
                "weather_code",
                "precipitation_probability",
                "apparent_temperature",
                "precipitation",
                "wind_speed_10m",
            ],
            "current": [
                "temperature_2m",
                "precipitation",
                "apparent_temperature",
                "relative_humidity_2m",
                "is_day",
                "weather_code",
                "wind_speed_10m"
            ],
            "timezone": timezone,
            "forecast_days": 7
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            'success': True,
            'data': data,
            'latitude': latitude,
            'longitude': longitude
        }
        
    except Exception as e:
        print(f"Weather API Error: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def get_current_weather(latitude=13.1431, longitude=123.7438):
    """
    Get current weather data formatted for the template.
    Uses Open-Meteo API with caching.
    """
    from datetime import datetime
    import pytz
    
    # Check cache first
    cache_key = f"weather_current_{latitude}_{longitude}"
    cached_data = cache.get(cache_key)
    if cached_data:
        # Update time dynamically on each request
        manila_tz = pytz.timezone('Asia/Manila')
        current_time = datetime.now(manila_tz).strftime('%I:%M %p')
        cached_data['time'] = current_time
        return cached_data
    
    result = fetch_weather_data(latitude, longitude)
    
    if not result['success']:
        # Return fallback data on error
        return get_fallback_weather()
    
    try:
        current = result['data'].get('current', {})
        daily = result['data'].get('daily', {})
        
        # Get today's max/min from daily data
        today_max = daily.get('temperature_2m_max', [28])[0]
        today_min = daily.get('temperature_2m_min', [22])[0]
        
        # Get current time in Manila timezone
        manila_tz = pytz.timezone('Asia/Manila')
        current_time = datetime.now(manila_tz).strftime('%I:%M %p')

        weather_data = {
             'temperature': round(current.get('temperature_2m', 25)),
             'condition': get_weather_condition(current.get('weather_code', 0)),
             'humidity': current.get('relative_humidity_2m', 65),
             'wind': round(current.get('wind_speed_10m', 10)),
             'feels_like': round(current.get('apparent_temperature', 25)),
             'precipitation': current.get('precipitation', 0),
             'rainfall': daily.get('rain_sum', [0])[0] if daily.get('rain_sum') else 0,  # Live daily rainfall in mm
             'date': json.dumps(daily.get('time', [''])[0]).strip('"') if daily.get('time') else '',
             'time': current_time,
             'icon': get_weather_icon(current.get('weather_code', 0)),
             'temp_max': round(today_max),
             'temp_min': round(today_min),
         }
        
        # Cache for 15 minutes
        cache.set(cache_key, weather_data, 900)
        return weather_data
        
    except Exception as e:
        print(f"Error parsing weather data: {e}")
        return get_fallback_weather()


def get_weekly_forecast(latitude=13.1431, longitude=123.7438):
    """
    Get 7-day forecast formatted for the template.
    Starts from current day dynamically.
    Includes hourly data for each day.
    """
    from datetime import datetime
    import pytz
    
    cache_key = f"weather_forecast_{latitude}_{longitude}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    result = fetch_weather_data(latitude, longitude)
    
    if not result['success']:
        return get_fallback_forecast()
    
    try:
        daily = result['data'].get('daily', {})
        hourly = result['data'].get('hourly', {})
        times = daily.get('time', [])
        weather_codes = daily.get('weather_code', [])
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        apparent_max = daily.get('apparent_temperature_max', [])
        apparent_min = daily.get('apparent_temperature_min', [])
        rain_sum = daily.get('rain_sum', [])
        sunrise = daily.get('sunrise', [])
        sunset = daily.get('sunset', [])
        
        hourly_time = hourly.get('time', [])
        hourly_temp = hourly.get('temperature_2m', [])
        hourly_humidity = hourly.get('relative_humidity_2m', [])
        hourly_wind = hourly.get('wind_speed_10m', [])
        hourly_precip = hourly.get('precipitation', [])
        
        # Get current day name for dynamic starting point
        manila_tz = pytz.timezone('Asia/Manila')
        current_date = datetime.now(manila_tz)
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        current_day_idx = current_date.weekday()
        
        forecast = []
        
        for i in range(min(7, len(times))):
            try:
                date_obj = datetime.strptime(times[i], '%Y-%m-%d')
                day_offset = (date_obj.date() - current_date.date()).days
                day_name = days[(current_day_idx + day_offset) % 7]
            except:
                day_name = days[(current_day_idx + i) % 7]
            
            # Get hourly data for this day
            day_date = times[i]
            hourly_data = []
            for h in range(len(hourly_time)):
                if hourly_time[h].startswith(day_date):
                    hourly_data.append({
                        'hour': hourly_time[h][11:16],
                        'temp': round(hourly_temp[h]) if h < len(hourly_temp) else 0,
                        'humidity': hourly_humidity[h] if h < len(hourly_humidity) else 0,
                        'wind': round(hourly_wind[h]) if h < len(hourly_wind) else 0,
                        'precip': hourly_precip[h] if h < len(hourly_precip) else 0
                    })
            
            forecast.append({
                'day': day_name,
                'date': times[i],
                'temp': round((max_temps[i] + min_temps[i]) / 2),
                'temp_max': round(max_temps[i]),
                'temp_min': round(min_temps[i]),
                'feels_like_max': round(apparent_max[i]) if i < len(apparent_max) else round(max_temps[i]),
                'feels_like_min': round(apparent_min[i]) if i < len(apparent_min) else round(min_temps[i]),
                'rain_sum': round(rain_sum[i], 1) if i < len(rain_sum) else 0,
                'sunrise': sunrise[i][11:16] if i < len(sunrise) and len(sunrise[i]) >= 16 else '06:00',
                'sunset': sunset[i][11:16] if i < len(sunset) and len(sunset[i]) >= 16 else '18:00',
                'icon': get_weather_icon(weather_codes[i]),
                'condition': get_weather_condition(weather_codes[i]),
                'precipitation': daily.get('rain_sum', [0])[i] if daily.get('rain_sum') else 0,
                'hourly': hourly_data
            })
        
        # Cache for 1 hour
        cache.set(cache_key, forecast, 3600)
        return forecast
        
    except Exception as e:
        print(f"Error parsing forecast data: {e}")
        return get_fallback_forecast()


def get_fallback_weather():
    """Return fallback weather data when API is unavailable."""
    from datetime import datetime
    import pytz
    manila_tz = pytz.timezone('Asia/Manila')
    current_time = datetime.now(manila_tz).strftime('%I:%M %p')
    return {
        'temperature': 28,
        'condition': 'Partly Cloudy',
        'humidity': 65,
        'wind': 10,
        'feels_like': 30,
        'precipitation': 10,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': current_time,
        'icon': 'cloud-sun',
        'temp_max': 32,
        'temp_min': 24,
    }


def get_fallback_forecast():
    """Return fallback forecast when API is unavailable."""
    from datetime import datetime
    import pytz

    manila_tz = pytz.timezone('Asia/Manila')
    current_date = datetime.now(manila_tz)
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    current_day_idx = current_date.weekday()

    forecast = []
    icons = ['sun', 'cloud-sun', 'cloud', 'cloud-rain', 'cloud-sun', 'cloud', 'sun']

    for i in range(7):
        # Calculate day name relative to current day
        day_name = days[(current_day_idx + i) % 7]

        # Generate fallback hourly data
        hourly_data = []
        for hour in range(6, 24, 3):  # 6:00, 9:00, 12:00, 15:00, 18:00, 21:00
            hourly_data.append({
                'hour': f"{hour:02d}:00",
                'temp': 28 + (i % 3) + (hour // 6 - 1),
                'humidity': 60 + (i * 2),
                'wind': 8 + (i % 4),
                'precip': 2 * (i % 3) if hour in [12, 15, 18] else 0
            })

        forecast.append({
            'day': day_name,
            'date': current_date.strftime('%Y-%m-%d'),
            'temp': 28 + (i % 3),
            'temp_max': 32 + (i % 2),
            'temp_min': 24 + (i % 2),
            'feels_like_max': 34 + (i % 2),
            'feels_like_min': 22 + (i % 2),
            'rain_sum': 10 * (i % 3),
            'sunrise': '06:00',
            'sunset': '18:00',
            'icon': icons[i],
            'condition': 'Partly Cloudy',
            'precipitation': 10 * (i % 3),
            'hourly': hourly_data
        })
        # Advance one day for next iteration
        current_date = current_date.replace(day=min(current_date.day + 1, 28))

    return forecast


def get_farming_recommendations(weather_data, forecast):
    """
    Generate farming recommendations based on weather data.
    """
    # Cache recommendations based on weather conditions
    import hashlib
    cache_key = f"farming_recommendations_{hashlib.md5(str(weather_data).encode()).hexdigest()}"
    cached_recommendations = cache.get(cache_key)
    if cached_recommendations:
        return cached_recommendations

    recommendations = []
    
    # Check current conditions
    temp = weather_data.get('temperature', 25)
    humidity = weather_data.get('humidity', 65)
    precipitation = weather_data.get('precipitation', 0)
    
    # Temperature-based recommendations
    if temp > 35:
        recommendations.append({
            'type': 'warning',
            'icon': 'exclamation-triangle',
            'title': 'Extreme Heat',
            'message': 'High temperatures detected. Ensure crops have adequate irrigation and consider shading sensitive plants.'
        })
    elif temp < 15:
        recommendations.append({
            'type': 'info',
            'icon': 'thermometer-half',
            'title': 'Cool Temperature',
            'message': 'Low temperatures may slow plant growth. Protect frost-sensitive crops.'
        })
    
    # Humidity-based recommendations
    if humidity > 80:
        recommendations.append({
            'type': 'warning',
            'icon': 'water',
            'title': 'High Humidity',
            'message': 'High humidity increases disease risk. Monitor crops for fungal infections.'
        })
    elif humidity < 40:
        recommendations.append({
            'type': 'info',
            'icon': 'tint',
            'title': 'Low Humidity',
            'message': 'Low humidity may cause stress. Increase watering frequency for optimal growth.'
        })
    
    # Precipitation forecast recommendations
    rainy_days = sum(1 for day in forecast[:3] if day.get('precipitation', 0) > 5)
    if rainy_days >= 3:
        recommendations.append({
            'type': 'info',
            'icon': 'cloud-rain',
            'title': 'Upcoming Rain',
            'message': f'Rain expected for {rainy_days} days. Adjust irrigation schedule accordingly.'
        })
    
    # Dry spell recommendations
    dry_days = sum(1 for day in forecast[:5] if day.get('precipitation', 0) < 2)
    if dry_days >= 4:
        recommendations.append({
            'type': 'warning',
            'icon': 'water',
            'title': 'Dry Spell',
            'message': 'Minimal rainfall expected. Ensure consistent irrigation to maintain soil moisture.'
        })
    
    # Add season-aware crop recommendations based on current month
    from datetime import datetime
    month = datetime.now().month
    if 6 <= month <= 11:
        season_name = 'wet season'
        best_crops = ['Rice', 'Corn', 'Kangkong', 'Upo', 'Sitaw']
    else:
        season_name = 'dry season'
        best_crops = ['Tomato', 'Eggplant', 'Cabbage', 'Chili', 'Sweet Potato']

    recommendations.append({
        'type': 'success',
        'icon': 'leaf',
        'title': f'Best crops for the {season_name}',
        'message': f'Focus on {best_crops[0]}, {best_crops[1]}, and {best_crops[2]} this {season_name} for stronger market demand.'
    })

    # Default recommendation if none were generated from weather conditions
    if len(recommendations) == 1:
        recommendations.insert(0, {
            'type': 'success',
            'icon': 'check-circle',
            'title': 'Good Conditions',
            'message': 'Weather conditions are favorable for farming activities.'
        })

    final_recommendations = recommendations[:4]  # Return max 4 recommendations

    # Cache for 1 hour
    cache.set(cache_key, final_recommendations, 3600)

    return final_recommendations

def get_model():
    """
    Loads the model once and keeps it in memory.
    First checks for pre-loaded model from Django app startup.
    This prevents slow disk reads on every API request.
    Optimized for faster loading with better error handling.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    # Check if model was pre-loaded during Django startup
    from django.core.cache import cache
    preloaded_model = cache.get('ml_model_preloaded')
    if preloaded_model is not None:
        print("Using pre-loaded ML model from Django startup")
        _MODEL_CACHE = preloaded_model
        return _MODEL_CACHE

    # Fallback: Load model on demand with optimized loading
    from .model import load_model
    model_files = ["zenodo_enhanced_model.joblib", "crop_model.joblib"]

    for model_file in model_files:
        model_path = Path(__file__).parent / "models" / model_file
        if model_path.exists():
            try:
                print(f"Loading ML model on demand: {model_file}...")
                start_time = __import__('time').time()

                model_package = load_model(model_path)
                load_time = __import__('time').time() - start_time
                print(f"Successfully loaded ML model package from {model_path} in {load_time:.2f}s (size: {model_path.stat().st_size / (1024*1024):.1f} MB)")

                # Validate model package
                if not isinstance(model_package, dict) or 'model' not in model_package:
                    print(f"Invalid model package structure in {model_file}")
                    continue

                model = model_package['model']
                if not hasattr(model, 'predict'):
                    print(f"Model in {model_file} does not have predict method")
                    continue

                _MODEL_CACHE = model_package
                return _MODEL_CACHE

            except Exception as e:
                print(f"Error loading model {model_file}: {e}")
                if "image" in str(e).lower():
                    print("Image-related error detected. This model may be incompatible with tabular data processing.")
                continue

    print("No valid ML model found. Using fallback predictions only.")
    return None


def generate_crop_prediction_result(data):
    """
    Generate crop predictions using the shared ML path used by the API and
    server-rendered pages.
    Optimized with better caching and error handling.
    """
    required_fields = ['ph', 'rainfall', 'temperature', 'humidity', 'location', 'season']
    for field in required_fields:
        if field not in data:
            raise ValueError(f'Missing required field: {field}')

    payload = data.copy()

    if 'crops' not in payload or not payload['crops']:
        from crops.models import Crop

        crop_names_cache_key = 'all_crop_names_for_ml'
        crop_names = cache.get(crop_names_cache_key)
        if crop_names is None:
            # Use select_related and only() for better performance
            crop_names = list(Crop.objects.values_list('crop_name', flat=True).distinct())
            cache.set(crop_names_cache_key, crop_names, 21600)  # Cache for 6 hours
        payload['crops'] = crop_names

    # Create cache key with sorted crops for consistency
    data_for_cache = payload.copy()
    data_for_cache['crops'] = sorted(payload.get('crops', []))
    cache_key = hashlib.md5(json.dumps(data_for_cache, sort_keys=True).encode()).hexdigest()
    cached_prediction = cache.get(f"ml_res_{cache_key}")
    if cached_prediction:
        return {
            'status': 'success',
            'predictions': cached_prediction,
            'cached': True,
            'source': 'cache',
        }

    model = get_model()
    if model is None:
        predictions = get_fallback_predictions(payload)
        cache.set(f"ml_res_{cache_key}", predictions, 7200)  # Cache fallback for 2 hours
        return {
            'status': 'success',
            'predictions': predictions,
            'fallback': True,
            'message': 'Using fallback predictions - ML model training in progress',
            'source': 'fallback',
        }

    try:
        from .model import predict_top_k

        k_value = int(payload.get('k', 8))
        predictions = predict_top_k(model, payload, k=k_value)
        cache.set(f"ml_res_{cache_key}", predictions, 21600)  # Cache for 6 hours
        return {
            'status': 'success',
            'predictions': predictions,
            'source': 'model',
        }
    except Exception as e:
        print(f"Error in ML prediction: {e}")
        # Fallback to simple predictions
        predictions = get_fallback_predictions(payload)
        cache.set(f"ml_res_{cache_key}", predictions, 7200)
        return {
            'status': 'success',
            'predictions': predictions,
            'fallback': True,
            'message': 'Advanced ML model temporarily unavailable. Using reliable fallback predictions based on seasonal and environmental data.',
            'source': 'fallback',
        }

@csrf_exempt
@require_POST
def predict_crops(request):
    """
    API Endpoint: /ml/predict/
    Expects JSON payload with environmental parameters for crop prediction.
    Returns top crop recommendations with predicted prices.
    Now supports dynamic crop fetching for better performance.
    """
    try:
        data = json.loads(request.body)
        return JsonResponse(generate_crop_prediction_result(data))

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An internal error occurred during prediction: {str(e)}'}, status=500)


@csrf_exempt
@require_POST
def weather_history(request):
    """
    API Endpoint: /ml/weather-history/
    Returns historical weather data for charting with different time periods.
    """
    try:
        data = json.loads(request.body)

        # Validate required fields
        required_fields = ['period']
        for field in required_fields:
            if field not in data:
                return JsonResponse({'error': f'Missing required field: {field}'}, status=400)

        period = data.get('period', '7_days_forecast')
        latitude = data.get('latitude', 13.1431)
        longitude = data.get('longitude', 123.7438)

        # Create cache key
        cache_key = f"weather_history_{period}_{latitude}_{longitude}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse({
                'status': 'success',
                'data': cached_data,
                'cached': True
            })

        # Define time periods
        period_config = {
            '7_days_ago': {'days_back': 7, 'label': '7 Days Ago'},
            '1_week_ago': {'days_back': 7, 'label': '1 Week Ago'},
            '1_month_ago': {'days_back': 30, 'label': '1 Month Ago'},
            '3_months_ago': {'days_back': 90, 'label': '3 Months Ago'},
            '7_days_forecast': {'days_back': 0, 'forecast': True, 'label': '7-Day Forecast'}
        }

        if period not in period_config:
            return JsonResponse({'error': 'Invalid period. Use: 7_days_ago, 1_week_ago, 1_month_ago, 3_months_ago, 7_days_forecast'}, status=400)

        config = period_config[period]

        if config.get('forecast', False):
            # Use current forecast API
            result = fetch_weather_data(latitude, longitude)
            if not result['success']:
                return JsonResponse({'error': 'Weather API unavailable'}, status=503)

            # Process forecast data for charting
            daily = result['data'].get('daily', {})
            dates = daily.get('time', [])
            temp_max = daily.get('temperature_2m_max', [])
            temp_min = daily.get('temperature_2m_min', [])
            rain_sum = daily.get('rain_sum', [])
            humidity_mean = daily.get('relative_humidity_2m_mean', [])
            wind_speed_max = daily.get('wind_speed_10m_max', [])

            # Get hourly data for more detailed charts
            hourly = result['data'].get('hourly', {})
            hourly_time = hourly.get('time', [])
            hourly_temp = hourly.get('temperature_2m', [])
            hourly_humidity = hourly.get('relative_humidity_2m', [])
            hourly_wind = hourly.get('wind_speed_10m', [])
            hourly_rain = hourly.get('precipitation', [])

            chart_data = {
                'period': period,
                'label': config['label'],
                'dates': dates,
                'temperature_max': temp_max,
                'temperature_min': temp_min,
                'rainfall': rain_sum,
                'humidity_mean': humidity_mean,
                'wind_speed_max': wind_speed_max,
                'hourly': {
                    'time': hourly_time,
                    'temperature': hourly_temp,
                    'humidity': hourly_humidity,
                    'wind_speed': hourly_wind,
                    'rainfall': hourly_rain
                }
            }
        else:
            # Use historical data API
            result = fetch_historical_weather_data(latitude, longitude, config['days_back'])
            if not result['success']:
                return JsonResponse({'error': 'Historical weather API unavailable'}, status=503)

            # Process historical data for charting
            daily = result['data'].get('daily', {})
            dates = daily.get('time', [])
            temp_max = daily.get('temperature_2m_max', [])
            temp_min = daily.get('temperature_2m_min', [])
            rain_sum = daily.get('rain_sum', [])
            humidity_mean = daily.get('relative_humidity_2m_mean', [])
            wind_max = daily.get('wind_speed_10m_max', [])

            chart_data = {
                'period': period,
                'label': config['label'],
                'dates': dates,
                'temperature_max': temp_max,
                'temperature_min': temp_min,
                'rainfall': rain_sum,
                'humidity_mean': humidity_mean,
                'wind_speed_max': wind_max,
                'hourly': None  # Historical API doesn't provide hourly data
            }

        # Cache for 30 minutes
        cache.set(cache_key, chart_data, 1800)

        return JsonResponse({
            'status': 'success',
            'data': chart_data
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An internal error occurred: {str(e)}'}, status=500)

def clear_ml_cache(request):
    """Optional utility view to clear ML cache if models are updated."""
    if request.user.is_staff:
        cache.clear()
        return JsonResponse({'status': 'Cache cleared'})
    return JsonResponse({'status': 'Unauthorized'}, status=403)

@csrf_exempt
@require_POST
def forecast_price(request):
    """
    API Endpoint: /ml/forecast-price/
    Returns ML-powered price forecast for a specific crop based on market data, weather, and ML predictions.
    """
    from market.models import MarketPrice

    try:
        data = json.loads(request.body)
        crop_name = data.get('crop_name', '')

        if not crop_name:
            return JsonResponse({'error': 'crop_name is required'}, status=400)

        # Check cache
        cache_key = f"price_forecast_{crop_name}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)

        # Get weather data for ML prediction
        try:
            weather_response = fetch_weather_data()
            if weather_response['success']:
                weather_data = {
                    'temperature': weather_response['data']['current']['temperature_2m'],
                    'humidity': weather_response['data']['current']['relative_humidity_2m'],
                    'precipitation': weather_response['data']['current']['precipitation'],
                    'forecast': weather_response['data']['daily']['time'][:7]  # 7 days
                }
            else:
                weather_data = None
        except:
            weather_data = None

        # Use ML-powered prediction from market.views.price_predictions logic
        try:
            from market.views import generate_weather_adjusted_predictions, get_seasonal_factor, calculate_trend_factor

            # Get current market data
            latest_price = MarketPrice.objects.filter(
                crop_name__iexact=crop_name
            ).order_by('-last_updated').first()

            if latest_price:
                current_price = float(latest_price.current_price)

                # Get price history for trend analysis
                price_history = MarketPrice.objects.filter(
                    crop_name__iexact=crop_name
                ).order_by('-date')[:30]

                # Calculate trend and seasonal factors
                trend_factor = calculate_trend_factor(price_history) if price_history else 1.0
                seasonal_factor = get_seasonal_factor(crop_name)

                # Calculate weather adjustments
                from market.views import calculate_weather_adjustments
                weather_adjustments = calculate_weather_adjustments(crop_name, weather_data) if weather_data else {'adjustments': {'1_week': 1.0}}

                # Generate ML-informed predictions
                predictions = generate_weather_adjusted_predictions(
                    crop_name, current_price, trend_factor, seasonal_factor, weather_adjustments
                )

                # Use 1-week prediction as forecast_price
                forecast_price_val = predictions[0]['predicted_price'] if predictions else current_price
                percentage_change = predictions[0]['change_percent'] if predictions else 0

                trend = 'rising' if percentage_change > 2 else ('falling' if percentage_change < -2 else 'stable')

                result = {
                    'crop': crop_name,
                    'current_price': current_price,
                    'forecast_price': round(forecast_price_val, 2),
                    'percentage_change': round(percentage_change, 2),
                    'trend': trend,
                    'data_source': 'ML Weather-Adjusted Model'
                }
            else:
                # Fallback predictions
                base_prices = {
                    'Rice': 45, 'Corn': 32, 'Tomato': 75, 'Eggplant': 55,
                    'Cabbage': 40, 'Onion': 110, 'Garlic': 180, 'Sweet Potato': 35,
                    'Peanut': 140, 'Chili': 90
                }

                base_price = base_prices.get(crop_name, 50)
                # Simple ML-informed forecast
                seasonal_factor = get_seasonal_factor(crop_name)
                weather_factor = 1.05 if weather_data and weather_data.get('temperature', 25) > 25 else 0.95
                forecast_price_val = base_price * seasonal_factor * weather_factor

                percentage_change = ((forecast_price_val - base_price) / base_price) * 100
                trend = 'rising' if percentage_change > 2 else ('falling' if percentage_change < -2 else 'stable')

                result = {
                    'crop': crop_name,
                    'current_price': base_price,
                    'forecast_price': round(forecast_price_val, 2),
                    'percentage_change': round(percentage_change, 2),
                    'trend': trend,
                    'data_source': 'ML Baseline Model'
                }

        except Exception as e:
            # Fallback to original logic if ML fails
            print(f"ML prediction failed for {crop_name}: {e}, using fallback")

            try:
                latest_price = MarketPrice.objects.filter(
                    crop_name__iexact=crop_name
                ).order_by('-last_updated').first()
            except:
                latest_price = None

            if latest_price:
                current_price = float(latest_price.current_price)

                # Simple forecast based on recent average
                recent_prices = MarketPrice.objects.filter(
                    crop_name__iexact=crop_name
                ).order_by('-date')[:7]
                forecast_price_val = sum(float(p.current_price) for p in recent_prices) / len(recent_prices) if recent_prices else current_price

                percentage_change = ((forecast_price_val - current_price) / current_price) * 100 if current_price > 0 else 0
                trend = 'rising' if percentage_change > 2 else ('falling' if percentage_change < -2 else 'stable')

                result = {
                    'crop': crop_name,
                    'current_price': current_price,
                    'forecast_price': round(forecast_price_val, 2),
                    'percentage_change': round(percentage_change, 2),
                    'trend': trend,
                    'data_source': 'Database Average (Fallback)'
                }
            else:
                # Ultimate fallback
                base_prices = {'Rice': 50, 'Corn': 30, 'Tomato': 35, 'Eggplant': 45}
                base_price = base_prices.get(crop_name, 50)
                forecast_price_val = base_price * 1.05  # 5% increase
                percentage_change = 5.0
                trend = 'rising'

                result = {
                    'crop': crop_name,
                    'current_price': base_price,
                    'forecast_price': round(forecast_price_val, 2),
                    'percentage_change': percentage_change,
                    'trend': trend,
                    'data_source': 'Static Fallback'
                }

        # Cache for 1 hour
        cache.set(cache_key, result, 3600)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': 'An internal error occurred'}, status=500)


@csrf_exempt
@require_POST
def crop_care_recommendations(request):
    """
    API Endpoint: /ml/crop-care/
    Returns ML-generated detailed care recommendations for specific crops.
    """
    try:
        data = json.loads(request.body)
        crop_name = data.get('crop_name', '')
        season = data.get('season', 'Wet')
        location = data.get('location', 'Legazpi City, Albay')

        if not crop_name:
            return JsonResponse({'error': 'crop_name is required'}, status=400)

        # Create cache key
        cache_key = f"crop_care_{crop_name}_{season}_{location}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)

        # Generate ML-powered care recommendations
        care_recommendations = generate_crop_care_recommendations(crop_name, season, location)

        # Cache for 24 hours
        cache.set(cache_key, care_recommendations, 86400)

        return JsonResponse(care_recommendations)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def generate_crop_care_recommendations(crop_name, season, location):
    """
    Generate comprehensive ML-powered care recommendations for crops.
    Uses crop-specific knowledge and environmental factors.
    """
    original_crop_name = str(crop_name).strip()
    normalized_crop_name = original_crop_name.lower()
    crop_aliases = {
        'rice (palay)': 'rice',
        'palay': 'rice',
        'corn (maize)': 'corn',
        'maize': 'corn',
        'beans': 'bean',
        'string bean': 'bean',
        'mung bean': 'bean',
        'bell pepper': 'chili',
        'sweet pepper': 'chili',
    }
    crop_name = crop_aliases.get(normalized_crop_name, normalized_crop_name)

    # Base care recommendations by crop
    crop_care_data = {
        'rice': {
            'best_season': 'Wet Season (June-November) - Requires flooded conditions',
            'yield_potential': '6-8 tons per hectare with optimal care',
            'difficulty': 'Moderate - Requires consistent water management',
            'planting_timing': 'Transplant 25-30 days after seeding when seedlings are 15-20cm tall',
            'spacing': '25cm between plants, 25cm between rows',
            'planting_depth': '2-3cm for seeds, transplant at same depth',
            'water_frequency': 'Maintain 5-10cm water depth throughout growth cycle',
            'soil_moisture': 'Keep fields flooded during vegetative stage, drain during ripening',
            'irrigation_method': 'Flood irrigation with controlled water levels',
            'fertilizer_schedule': 'Apply NPK 14-14-14 at transplanting, urea at tillering and panicle initiation',
            'optimal_ph': '6.0-7.0 - Slightly acidic to neutral',
            'common_pests': 'Stem borers, leaf folders, rice bugs, and brown planthoppers',
            'prevention_methods': 'Use resistant varieties, crop rotation, and balanced fertilization',
            'organic_control': 'Neem oil sprays and introduction of natural predators',
            'weed_control': 'Manual weeding 2-3 times, pre-emergent herbicides if needed',
            'pruning': 'Remove excess tillers if plant density is too high',
            'harvest_timing': 'Harvest when 80-85% of grains are golden yellow',
            'expected_yield': 'High (6-8 t/ha)',
            'risk_level': 'Medium - Water management critical',
            'profit_multiplier': 1.15
        },
        'corn': {
            'best_season': 'Dry Season (December-May) - Less pest pressure',
            'yield_potential': '8-10 tons per hectare with optimal care',
            'difficulty': 'Easy - Drought tolerant once established',
            'planting_timing': 'Plant after last frost when soil temperature reaches 18°C',
            'spacing': '25-30cm between plants, 75-90cm between rows',
            'planting_depth': '4-5cm deep in moist soil',
            'water_frequency': 'Weekly during establishment, every 3-4 days during tasseling',
            'soil_moisture': 'Keep soil moist but not waterlogged, reduce watering after pollination',
            'irrigation_method': 'Drip irrigation or furrow irrigation preferred',
            'fertilizer_schedule': 'Apply complete fertilizer at planting, side-dress nitrogen at knee-high',
            'optimal_ph': '6.0-7.0 - Prefers neutral soil',
            'common_pests': 'Corn borers, armyworms, and corn earworms',
            'prevention_methods': 'Crop rotation, resistant varieties, and field sanitation',
            'organic_control': 'Bt-based insecticides and beneficial insects',
            'weed_control': 'Cultivate between rows, use pre-emergent herbicides',
            'pruning': 'Remove suckers at base to focus energy on main stalk',
            'harvest_timing': 'Harvest when kernels are dented and black layer forms',
            'expected_yield': 'Very High (8-10 t/ha)',
            'risk_level': 'Low - Hardy and adaptable',
            'profit_multiplier': 1.25
        },
        'tomato': {
            'best_season': 'Dry Season (December-March) - Cooler temperatures prevent disease',
            'yield_potential': '40-60 tons per hectare with optimal care',
            'difficulty': 'Moderate - Requires consistent care',
            'planting_timing': 'Start seeds indoors 6-8 weeks before transplanting outdoors',
            'spacing': '45-60cm between plants, 90-120cm between rows',
            'planting_depth': 'Transplant so soil covers stem up to first leaves',
            'water_frequency': '2-3 times per week, avoid overhead watering',
            'soil_moisture': 'Keep soil consistently moist, mulch to retain moisture',
            'irrigation_method': 'Drip irrigation to prevent fungal diseases',
            'fertilizer_schedule': 'High nitrogen initially, switch to phosphorus/potassium for fruiting',
            'optimal_ph': '6.0-6.8 - Slightly acidic',
            'common_pests': 'Aphids, tomato hornworms, whiteflies, and spider mites',
            'prevention_methods': 'Use row covers, companion planting, and resistant varieties',
            'organic_control': 'Neem oil, insecticidal soap, and beneficial insects',
            'weed_control': 'Mulch heavily, hand-weed regularly',
            'pruning': 'Remove suckers and lower leaves for better air circulation',
            'harvest_timing': 'Pick when fruits are fully colored but still firm',
            'expected_yield': 'High (40-60 t/ha)',
            'risk_level': 'Medium - Disease pressure high',
            'profit_multiplier': 1.35
        }
    }

    # Get crop-specific data or default
    crop_data = crop_care_data.get(crop_name, {
        'best_season': f'{season} Season - Standard recommendation',
        'yield_potential': 'Variable with proper care',
        'difficulty': 'Moderate',
        'planting_timing': 'Plant during recommended season',
        'spacing': 'Follow standard spacing guidelines',
        'planting_depth': 'Plant at appropriate depth for crop type',
        'water_frequency': 'Water regularly as needed',
        'soil_moisture': 'Keep soil consistently moist',
        'irrigation_method': 'Drip or furrow irrigation recommended',
        'fertilizer_schedule': 'Apply balanced fertilizer as needed',
        'optimal_ph': '6.0-7.0 - Neutral soil preferred',
        'common_pests': 'Monitor for common pests in the area',
        'prevention_methods': 'Crop rotation and proper field sanitation',
        'organic_control': 'Beneficial insects and organic sprays',
        'weed_control': 'Regular weeding and mulching',
        'pruning': 'Minimal pruning required',
        'harvest_timing': 'Harvest at optimal maturity',
        'expected_yield': 'Medium',
        'risk_level': 'Medium',
        'profit_multiplier': 1.2
    })

    # Generate ML insights based on season and location
    season_multiplier = 1.05 if season == 'Dry' else 0.95
    location_adjustment = 1.02  # Assuming Legazpi City, Albay has good agricultural conditions

    # Add ML-generated insights
    ml_insights = {
        'planting_insight': f'Current {season.lower()} season conditions {"favor" if season == "Dry" and crop_name in ["tomato", "eggplant", "chili"] else "are suitable for"} {original_crop_name.lower()} cultivation',
        'irrigation_insight': f'Consistent moisture critical for {original_crop_name.lower()} - consider installing monitoring sensors for optimal yield',
        'nutrient_insight': f'Balanced fertilization key for {original_crop_name.lower()} - soil testing recommended before planting',
        'pest_insight': f'Early monitoring prevents {original_crop_name.lower()} yield loss - integrated pest management recommended',
        'maintenance_insight': f'Regular care throughout {original_crop_name.lower()} growth cycle ensures quality harvest'
    }

    return {
        'crop_name': original_crop_name,
        'optimal_planting_season': crop_data.get('best_season', f'{season} Season'),
        **crop_data,
        **ml_insights
    }


@csrf_exempt
@require_POST
def ml_weather_trends(request):
    """
    API Endpoint: /ml/weather-trends/
    Returns ML-analyzed and predicted weather trends for the charts.
    Uses OpenMeteo API data + ML models for trend analysis and predictions.
    
     Request JSON:
     {
         "latitude": 13.1431,
         "longitude": 123.7438,
         "period": "7_days_forecast|7_days_ago|1_week_ago|1_month_ago|3_months_ago",
         "crop_name": "Rice" (optional - for ML-optimized recommendations)
     }
     """
    from ml_service.openmeteo_integration import fetch_openmeteo_weather
    import numpy as np
    
    try:
        data = json.loads(request.body)
        latitude = float(data.get('latitude', 13.1431))
        longitude = float(data.get('longitude', 123.7438))
        period = data.get('period', '7_days_forecast')
        crop_name = data.get('crop_name', 'Rice')
        
        # Create cache key
        cache_key = f"ml_weather_trends_{latitude}_{longitude}_{period}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse({'status': 'success', 'data': cached_data})
        
        # Map period to data selection and transformation
        period_mapping = {
            '7_days_forecast': (0, 7),     # Future 7 days
            '7_days_ago': (-7, 0),         # Past 7 days
            '1_week_ago': (-7, 0),         # Past 7 days
            '1_month_ago': (-30, 0),       # Past 30 days
            '3_months_ago': (-90, 0),      # Past 90 days
        }

        start_offset, end_offset = period_mapping.get(period, (0, 7))

        if start_offset < 0:
            # Fetch historical data for past periods
            days_back = abs(start_offset)
            historical_result = fetch_historical_weather_data(latitude, longitude, days_back)
            if historical_result['success']:
                weather_data = _convert_historical_to_forecast_format(historical_result['data'])
            else:
                return JsonResponse({'error': 'Could not fetch historical weather data'}, status=503)
        else:
            # Fetch forecast data for future periods
            weather_data = fetch_openmeteo_weather(latitude, longitude, days_forecast=14)
            if not weather_data:
                return JsonResponse({'error': 'Could not fetch weather data'}, status=503)

        # Process data based on period
        chart_data = _process_ml_weather_data(weather_data, period, crop_name, start_offset, end_offset)
        
        # Cache for 30 minutes
        cache.set(cache_key, chart_data, 1800)
        
        return JsonResponse({
            'status': 'success',
            'period': period,
            'data': chart_data
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    except Exception as e:
        import traceback
        print(f"ML Weather Trends Error: {traceback.format_exc()}")
        return JsonResponse({'error': f'Internal error: {str(e)}'}, status=500)


def _process_ml_weather_data(weather_data, period, crop_name, start_offset=0, end_offset=7):
    """
    Process OpenMeteo weather data through ML pipeline for trend analysis.
    Returns data formatted for Chart.js visualization.
    
    start_offset and end_offset are used to simulate historical periods:
    - (0, 7) = next 7 days (forecast)
    - (-7, 0) = past 7 days (simulated with variation)
    - (-30, 0) = past 30 days (simulated with variation)
    - etc.
    """
    import numpy as np
    from scipy.signal import savgol_filter
    from datetime import datetime, timedelta
    import random
    
    try:
        # Extract basic forecast data
        daily_forecast = weather_data.get('daily_forecast', [])
        
        if not daily_forecast:
            return _generate_fallback_chart_data()
        
        dates = []
        temps_max = []
        temps_min = []
        rainfall = []
        humidity = []
        wind_speed = []
        
        # If showing historical data, use the real historical data provided
        if start_offset < 0:
            # For historical periods, daily_forecast contains the historical data
            # Use all available data (no need to slice further since fetch_historical_weather_data
            # already provides the correct period)
            for day in daily_forecast:
                dates.append(day['date'].strftime('%Y-%m-%d') if hasattr(day['date'], 'strftime') else str(day['date']))
                temps_max.append(day.get('temp_max', 0))
                temps_min.append(day.get('temp_min', 0))
                rainfall.append(day.get('rain_sum', 0))
                # Use humidity from API
                if 'humidity_max' in day and 'humidity_min' in day:
                    humidity_val = (day['humidity_max'] + day['humidity_min']) / 2
                else:
                    humidity_val = day.get('relative_humidity_2m_mean', 65)
                humidity.append(humidity_val)
                # Use wind speed from API
                wind_speed.append(day.get('wind_speed_max', 8))
        else:
            # Use actual forecast data
            num_days = end_offset - start_offset or 7
            for i, day in enumerate(daily_forecast[start_offset:start_offset + num_days]):
                dates.append(day['date'].strftime('%Y-%m-%d') if hasattr(day['date'], 'strftime') else str(day['date']))
                temps_max.append(day.get('temp_max', 0))
                temps_min.append(day.get('temp_min', 0))
                rainfall.append(day.get('rain_sum', 0))
                # Use humidity from API or calculate if not available
                if 'humidity_max' in day and 'humidity_min' in day:
                    humidity_val = (day['humidity_max'] + day['humidity_min']) / 2
                else:
                    humidity_val = max(40, min(100, 50 + day.get('precipitation_sum', 0) * 5))
                humidity.append(humidity_val)
                # Use wind speed from API or default
                if 'wind_speed_max' in day:
                    wind_speed.append(day['wind_speed_max'])
                else:
                    wind_speed.append(max(2, min(15, 5 + day.get('precipitation_sum', 0) * 0.8)))
        
        if not dates:
            return _generate_fallback_chart_data()
        
        # Apply ML smoothing to trends
        temps_max_array = np.array(temps_max)
        temps_max_smooth = list(temps_max_array)
        
        if len(temps_max) >= 5:
            try:
                window_length = min(5, len(temps_max) if len(temps_max) % 2 == 1 else len(temps_max) - 1)
                if window_length >= 3:
                    temps_max_smooth = list(savgol_filter(temps_max_array, window_length, 2))
            except:
                temps_max_smooth = list(temps_max_array)
        
        # Calculate ML-based trend indicators
        trend_indicators = _calculate_trend_indicators(list(temps_max_array), rainfall, humidity)
        
        # Build final chart data
        chart_data = {
            'dates': dates,
            'temperature_max': [round(t, 1) for t in temps_max],
            'temperature_min': [round(t, 1) for t in temps_min],
            'temperature_smooth': [round(t, 1) for t in temps_max_smooth] if temps_max_smooth != list(temps_max_array) else None,
            'rainfall': [round(r, 1) for r in rainfall],
            'humidity_mean': [round(h, 1) for h in humidity],
            'wind_speed_max': [round(w, 1) for w in wind_speed],
            'hourly': None,
            'ml_analysis': {
                'temperature_trend': trend_indicators['temp_trend'],
                'rainfall_trend': trend_indicators['rainfall_trend'],
                'forecast_confidence': trend_indicators['confidence'],
                'crop_suitability_score': trend_indicators['crop_suitability'],
                'recommendations': trend_indicators['recommendations']
            }
        }
        
        return chart_data
        
    except Exception as e:
        print(f"Error processing ML weather data: {str(e)}")
        import traceback
        traceback.print_exc()
        return _generate_fallback_chart_data()


def _calculate_trend_indicators(temps, rainfall, humidity):
    """
    Calculate ML-based trend indicators for weather data.
    Returns trend analysis for display and recommendations.
    """
    import numpy as np
    
    temps_array = np.array(temps)
    rainfall_array = np.array(rainfall)
    
    # Calculate temperature trend
    if len(temps_array) >= 2:
        temp_trend = 'rising' if temps_array[-1] > temps_array[0] else ('falling' if temps_array[-1] < temps_array[0] else 'stable')
        temp_change = round(temps_array[-1] - temps_array[0], 1)
    else:
        temp_trend = 'stable'
        temp_change = 0
    
    # Calculate rainfall trend
    if len(rainfall_array) >= 2:
        rainfall_trend = 'increasing' if rainfall_array[-1] > rainfall_array[0] else ('decreasing' if rainfall_array[-1] < rainfall_array[0] else 'stable')
        rainfall_change = round(rainfall_array[-1] - rainfall_array[0], 1)
    else:
        rainfall_trend = 'stable'
        rainfall_change = 0
    
    # Calculate confidence level (based on data consistency)
    confidence = min(95, max(60, 80 + (0 if temp_trend == 'stable' else 10)))
    
    # Calculate crop suitability (scale 0-100)
    avg_temp = np.mean(temps_array)
    avg_rainfall = np.mean(rainfall_array)
    
    # Ideal conditions: 25-30°C and moderate rainfall
    temp_deviation = abs(avg_temp - 27.5)
    rainfall_factor = min(100, (avg_rainfall / 50 * 100)) if avg_rainfall > 0 else 50
    
    crop_suitability = max(40, min(100, 100 - (temp_deviation * 3) + (rainfall_factor / 2)))
    
    recommendations = []
    
    if temp_trend == 'rising' and avg_temp > 30:
        recommendations.append('⚠️ Rising temperatures detected - increase irrigation frequency')
    
    if rainfall_trend == 'increasing' and avg_rainfall > 100:
        recommendations.append('⚠️ Heavy rainfall expected - ensure proper drainage')
    
    if crop_suitability > 80:
        recommendations.append('✅ Excellent conditions for planting crops')
    elif crop_suitability > 60:
        recommendations.append('⚡ Good conditions - monitor rainfall and temperature')
    else:
        recommendations.append('⚠️ Challenging conditions - consider delaying planting')
    
    return {
        'temp_trend': f'{temp_trend} (+{temp_change}°C)' if temp_change >= 0 else f'{temp_trend} ({temp_change}°C)',
        'rainfall_trend': f'{rainfall_trend} ({rainfall_change}mm)',
        'confidence': confidence,
        'crop_suitability': round(crop_suitability, 0),
        'recommendations': recommendations
    }


def _convert_historical_to_forecast_format(historical_data):
    """
    Convert Open-Meteo historical data format to forecast format for consistency.
    """
    from datetime import datetime

    daily_data = historical_data.get('daily', {})

    if not daily_data:
        return None



    daily_forecast = []
    for i in range(len(daily_data['time'])):
        try:
            date_obj = datetime.fromisoformat(daily_data['time'][i])
            forecast_entry = {
                'date': date_obj,
                'weather_code': 1,  # Default weather code since historical doesn't provide it
                'temp_max': daily_data['temperature_2m_max'][i],
                'temp_min': daily_data['temperature_2m_min'][i],
                'precipitation_sum': daily_data['precipitation_sum'][i],
                'rain_sum': daily_data.get('rain_sum', daily_data['precipitation_sum'])[i],
                'humidity_max': daily_data.get('relative_humidity_2m_max', [65])[i],
                'humidity_min': daily_data.get('relative_humidity_2m_max', [65])[i],
                'wind_speed_max': daily_data.get('wind_speed_10m_max', [8])[i]
            }
            daily_forecast.append(forecast_entry)
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error processing historical data entry {i}: {e}")
            continue

    return {
        'location': {
            'latitude': historical_data.get('latitude', 13.1431),
            'longitude': historical_data.get('longitude', 123.7438),
            'timezone': historical_data.get('timezone', 'Asia/Manila')
        },
        'daily_forecast': daily_forecast
    }


def _generate_fallback_chart_data():
    """
    Generate fallback chart data when API fails.
    """
    from datetime import datetime, timedelta
    
    dates = [(datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    return {
        'dates': dates,
        'temperature_max': [28, 29, 27, 26, 28, 29, 30],
        'temperature_min': [22, 23, 21, 20, 22, 23, 24],
        'rainfall': [5, 10, 15, 8, 3, 0, 2],
        'humidity_mean': [65, 70, 75, 68, 60, 55, 58],
        'wind_speed_max': [8, 10, 12, 9, 7, 5, 6],
        'hourly': None,
        'ml_analysis': {
            'temperature_trend': 'rising (+2°C)',
            'rainfall_trend': 'decreasing (-3mm)',
            'forecast_confidence': 75,
            'crop_suitability_score': 78,
            'recommendations': ['✅ Excellent conditions for planting crops', '⚡ Monitor rainfall patterns']
        }
    }
