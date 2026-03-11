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


def fetch_weather_data(latitude=13.1422, longitude=123.7438, timezone="Asia/Manila"):
    """
    Fetch weather data from Open-Meteo API.
    
    Args:
        latitude: Location latitude (default: Legazpi City, Philippines)
        longitude: Location longitude (default: Legazpi City, Philippines)
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
                "rain_sum"
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


def get_current_weather(latitude=13.1422, longitude=123.7438):
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


def get_weekly_forecast(latitude=13.1422, longitude=123.7438):
    """
    Get 7-day forecast formatted for the template.
    Starts from current day dynamically.
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
        times = daily.get('time', [])
        weather_codes = daily.get('weather_code', [])
        max_temps = daily.get('temperature_2m_max', [])
        min_temps = daily.get('temperature_2m_min', [])
        apparent_max = daily.get('apparent_temperature_max', [])
        apparent_min = daily.get('apparent_temperature_min', [])
        rain_sum = daily.get('rain_sum', [])
        sunrise = daily.get('sunrise', [])
        sunset = daily.get('sunset', [])
        
        # Get current day name for dynamic starting point
        manila_tz = pytz.timezone('Asia/Manila')
        current_date = datetime.now(manila_tz)
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        current_day_idx = current_date.weekday()
        
        forecast = []
        
        for i in range(min(7, len(times))):
            try:
                date_obj = datetime.strptime(times[i], '%Y-%m-%d')
                # Calculate day name relative to current day
                day_offset = (date_obj.date() - current_date.date()).days
                day_name = days[(current_day_idx + day_offset) % 7]
            except:
                day_name = days[(current_day_idx + i) % 7]
            
            forecast.append({
                'day': day_name,
                'date': times[i],
                'temp': round((max_temps[i] + min_temps[i]) / 2),
                'temp_max': round(max_temps[i]),
                'temp_min': round(min_temps[i]),
                'feels_like_max': round(apparent_max[i]) if i < len(apparent_max) else round(max_temps[i]),
                'feels_like_min': round(apparent_min[i]) if i < len(apparent_min) else round(min_temps[i]),
                'rain_sum': round(rain_sum[i], 1) if i < len(rain_sum) else 0,
                'sunrise': sunrise[i] if i < len(sunrise) else '',
                'sunset': sunset[i] if i < len(sunset) else '',
                'icon': get_weather_icon(weather_codes[i]),
                'condition': get_weather_condition(weather_codes[i]),
                'precipitation': daily.get('rain_sum', [0])[i] if daily.get('rain_sum') else 0
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
            'precipitation': 10 * (i % 3)
        })
        # Advance one day for next iteration
        current_date = current_date.replace(day=min(current_date.day + 1, 28))
    
    return forecast


def get_farming_recommendations(weather_data, forecast):
    """
    Generate farming recommendations based on weather data.
    """
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
    
    # Default recommendation if none generated
    if not recommendations:
        recommendations.append({
            'type': 'success',
            'icon': 'check-circle',
            'title': 'Good Conditions',
            'message': 'Weather conditions are favorable for farming activities.'
        })
    
    return recommendations[:4]  # Return max 4 recommendations

def get_model():
    """
    Loads the model once and keeps it in memory. 
    This prevents slow disk reads on every API request.
    """
    global _MODEL_CACHE
    if _MODEL_CACHE is None:
        from .model import load_model
        model_path = Path(__file__).parent / "models" / "crop_model.joblib"
        try:
            _MODEL_CACHE = load_model(model_path)
            print(f"Successfully loaded ML model from {model_path}")
        except Exception as e:
            print(f"Error loading model: {e}")
            return None
    return _MODEL_CACHE

@csrf_exempt
@require_POST
def predict_crops(request):
    """
    API Endpoint: /ml/predict/
    Returns top-k crop recommendations based on environmental data.
    Includes a caching layer to improve dashboard load times.
    """
    try:
        # 1. Parse Input
        data = json.loads(request.body)
        
        # 2. Optimization: Prediction Caching
        # We create a unique key based on the input values. 
        # If the same Location/Season/Soil data is sent twice, we return the cached result.
        cache_input = f"{data.get('location')}-{data.get('season')}-{data.get('ph')}-{data.get('rainfall')}"
        cache_key = hashlib.md5(cache_input.encode()).hexdigest()
        
        cached_prediction = cache.get(f"ml_res_{cache_key}")
        if cached_prediction:
            return JsonResponse({
                'predictions': cached_prediction, 
                'source': 'cache',
                'status': 'success'
            })

        # 3. Get Model (Loaded in RAM)
        model = get_model()
        if model is None:
            return JsonResponse({'error': 'ML Model not initialized'}, status=500)

        # 4. Perform Inference
        from .model import predict_top_k
        # k=8 matches the 8 cards shown in your dashboard screenshot
        k_value = data.get('k', 8) 
        predictions = predict_top_k(model, data, k=k_value)

        # 5. Store in cache for 1 hour (3600 seconds)
        cache.set(f"ml_res_{cache_key}", predictions, 3600)

        return JsonResponse({
            'predictions': predictions, 
            'source': 'model_inference',
            'status': 'success'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except KeyError as e:
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'error': 'An internal error occurred during prediction'}, status=500)

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
    Returns price forecast for a specific crop.
    """
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
        
        # Generate mock price data (in production, this would use ML model)
        import random
        base_prices = {
            'Rice': 50, 'Corn': 30, 'Eggplant': 45, 'Bitter Gourd': 40,
            'Tomato': 35, 'Sweet Potato': 25, 'Okra': 28, 'Peanut': 60,
            'Melon': 45, 'Watermelon': 30, 'Cucumber': 22, 'Carrot': 35,
            'Chili': 50, 'Potato': 28, 'Cabbage': 20, 'Onion': 55,
            'Garlic': 70, 'Squash': 18, 'Beans': 32
        }
        
        base_price = base_prices.get(crop_name, 30)
        current_price = base_price + random.randint(-5, 10)
        forecast_change = random.uniform(-10, 15)
        forecast_price = current_price * (1 + forecast_change/100)
        
        result = {
            'crop': crop_name,
            'current_price': current_price,
            'forecast_price': round(forecast_price, 2),
            'percentage_change': round(forecast_change, 2),
            'trend': 'rising' if forecast_change > 2 else ('falling' if forecast_change < -2 else 'stable')
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
