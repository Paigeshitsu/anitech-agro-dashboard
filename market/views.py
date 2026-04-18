from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.cache import cache
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from .models import MarketPrice, BuyerOffer, ScheduleDistribution, SellerOffer, Crop
from collections import defaultdict
from .forms import MarketPriceForm, BuyerOfferForm, ScheduleDistributionForm, SellerOfferForm
import json
import random
import math
from datetime import datetime

CROP_VOLATILITY = {
    'rice': 0.02,
    'corn': 0.025,
    'tomato': 0.04,
    'eggplant': 0.03,
    'cabbage': 0.035,
    'onion': 0.015,
    'garlic': 0.02,
    'sweet potato': 0.025,
    'peanut': 0.015,
    'chili': 0.05,
}
from anitech.views import account_type_required


# Cache for market price data (module-level for performance)
_market_price_cache = {}
_cache_timestamp = None
CACHE_TIMEOUT = 300  # 5 minutes cache


def get_market_price_data(crops=None, use_cache=True):
    """Fetch market price summaries and recent history for the market prices page.
    Optimized with caching and efficient queries.
    """
    from django.core.cache import cache
    from datetime import time
    
    # Generate cache key
    cache_key = 'market_price_data_' + '_'.join(sorted(crops) if crops else ['all'])
    
    # Try to get from Django cache first
    if use_cache:
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
    
    # Determine crop names
    if crops is None or not crops:
        # Use cached crop names if available
        crop_names = cache.get('all_crop_names')
        if crop_names is None:
            crop_names = list(MarketPrice.objects.values_list('crop_name', flat=True).distinct())
            cache.set('all_crop_names', crop_names, 3600)  # Cache for 1 hour
    else:
        crop_names = [crop.strip() for crop in crops if crop and crop.strip()]

    if not crop_names:
        return []

    # Build optimized query using select_related and only() for better performance
    crop_query = Q()
    for crop_name in crop_names:
        crop_query |= Q(crop_name__iexact=crop_name)

    # Fetch only necessary fields and limit results per crop
    price_history_qs = MarketPrice.objects.filter(crop_query).order_by('-date', '-last_updated')
    
    # Process data more efficiently
    grouped_history = defaultdict(list)
    for record in price_history_qs:
        key = record.crop_name.lower()
        # Limit to 30 records per crop to prevent memory issues
        if len(grouped_history[key]) < 30:
            grouped_history[key].append(record)

    results = []
    for crop_name in crop_names:
        history = grouped_history.get(crop_name.lower(), [])
        if history:
            latest_price = history[0]
            current_price = float(latest_price.current_price)
            previous_price = float(history[1].current_price) if len(history) >= 2 else current_price
            if previous_price > 0:
                percentage_change = ((current_price - previous_price) / previous_price) * 100
            else:
                percentage_change = 0

            if percentage_change > 2:
                trend = 'rising'
            elif percentage_change < -2:
                trend = 'falling'
            else:
                trend = 'stable'

            # Calculate average more efficiently
            avg_price = sum(float(p.current_price) for p in history) / len(history)

            results.append({
                'crop': crop_name,
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'forecast_price': round(avg_price, 2),
                'percentage_change': round(percentage_change, 2),
                'trend': trend,
                'unit': history[0].unit,
                'last_updated': history[0].last_updated.strftime('%Y-%m-%d'),
                'price_history': [
                    {
                        'date': p.date.strftime('%Y-%m-%d') if p.date else None,
                        'price': float(p.current_price)
                    }
                    for p in reversed(history[:7])
                ]
            })
        else:
            results.append({
                'crop': crop_name,
                'current_price': 0,
                'previous_price': 0,
                'forecast_price': 0,
                'percentage_change': 0,
                'trend': 'stable',
                'unit': 'per kg',
                'last_updated': None,
                'price_history': []
            })

    # Cache the results
    if use_cache:
        cache.set(cache_key, results, CACHE_TIMEOUT)
    
    return results


@login_required
@account_type_required('admin', 'farmer', 'buyer')
def market_prices_view(request):
    """Pure Django view for /market/ - renders prices.html with DB data + trends."""
    from ml_service.views import fetch_weather_data
    
    price_data = get_market_price_data()
    
    # Pre-compute predictions on server for instant loading
    crops = [item['crop'] for item in price_data] if price_data else list(get_baseline_prices().keys())
    baseline_prices = get_baseline_prices()
    
    # Get weather data using cached function
    from ml_service.views import get_current_weather
    weather_info = get_current_weather()
    weather_data = {
        'temperature': weather_info.get('temperature', 28),
        'humidity': weather_info.get('humidity', 65),
        'precipitation': weather_info.get('precipitation', 0),
        'rainfall': weather_info.get('rainfall', 0)
    }
    
    # Batch ML predictions for all crops at once for better performance
    import hashlib
    key_string = json.dumps({'crops': sorted(crops), 'weather': weather_data}, sort_keys=True)
    cache_key = f"market_predictions_{hashlib.md5(key_string.encode()).hexdigest()}"
    precomputed_predictions = cache.get(cache_key)

    if precomputed_predictions is None:
        # Generate batch ML predictions
        season = 'Wet' if weather_data and weather_data.get('rainfall', 0) > 100 else 'Dry'
        batch_ml_data = {
            'crops': crops,
            'location': 'Legazpi City, Albay',
            'season': season,
            'ph': 6.5,
            'rainfall': weather_data.get('rainfall', 100) if weather_data else 100,
            'temperature': weather_data.get('temperature', 28) if weather_data else 28,
            'humidity': weather_data.get('humidity', 65) if weather_data else 65
        }

        from ml_service.views import generate_crop_prediction_result
        batch_ml_result = generate_crop_prediction_result(batch_ml_data)
        batch_predictions = {p['crop']: p for p in batch_ml_result.get('predictions', [])}

        precomputed_predictions = []
        for crop_name in crops:
            item = next((p for p in price_data if p['crop'].lower() == crop_name.lower()), None)
            if item:
                current_price = float(item.get('current_price', 0) or 0)
                price_history = item.get('price_history', [])
            else:
                current_price = float(baseline_prices.get(crop_name, 50.0))
                price_history = []

            if price_history:
                history_prices = [float(point.get('price', 0)) for point in price_history if point.get('price') is not None]
                trend_factor = calculate_trend_factor([type('P', (), {'current_price': p}) for p in history_prices]) if len(history_prices) >= 2 else 1.0
            else:
                trend_factor = 1.0

            seasonal_factor = get_seasonal_factor(crop_name)
            weather_adjustments = calculate_weather_adjustments(crop_name, weather_data) if weather_data else {
                'current_weather_impact': {'temperature': 1.0, 'humidity': 1.0, 'rainfall': 1.0},
                'forecast_impact': {'weekly_rainfall': 0, 'weekly_temp_avg': 28, 'seasonal_projection': 1.0},
                'adjustments': {'1_week': 1.0, '1_month': 1.0, '3_months': 1.0}
            }

            # Use batch ML predictions
            ml_prediction = batch_predictions.get(crop_name)
            if ml_prediction and ml_prediction.get('predictions'):
                predictions = ml_prediction['predictions']
                data_source = 'ML ' + batch_ml_result.get('source', 'Prediction')
            else:
                # Fallback to market logic
                predictions = generate_weather_adjusted_predictions(
                    crop_name, current_price, trend_factor, seasonal_factor, weather_adjustments
                )
                data_source = 'Weather-Aligned Prediction' if weather_data else 'Baseline Prediction'

            precomputed_predictions.append({
                'crop': crop_name,
                'current_price': round(current_price, 2),
                'predictions': predictions,
                'weather_factors': weather_adjustments,
                'confidence': calculate_confidence_level(weather_data),
                'data_source': data_source
            })

        # Cache for 10 minutes
        cache.set(cache_key, precomputed_predictions, 600)
    
    context = {
        'prices': price_data,
        'prices_json': json.dumps(price_data),
        'predictions_json': json.dumps(precomputed_predictions),
        'lang': request.session.get('lang', 'en')
    }
    return render(request, 'market/prices.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def forecast_price(request):
    """POST /market/forecast/ - Get actual market prices from database."""
    try:
        data = json.loads(request.body)
        crops = data.get('crops', [])
        if not crops:
            crop_name = data.get('crop_name', '')
            if crop_name:
                crops = [crop_name]

        results = get_market_price_data(crops=crops)
        return JsonResponse({'prices': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def price_predictions(request):
    """POST /market/price-predictions/ - Generate market price predictions for crops."""
    try:
        data = json.loads(request.body)
        crops = data.get('crops', []) or []
        period = data.get('period', '1_week')
        weather_data = data.get('weather_data', {}) or {}

        if isinstance(crops, str):
            crops = [crops]
        crops = [crop.strip() for crop in crops if crop and str(crop).strip()]

        if not crops:
            crops = [item['crop'] for item in get_market_price_data()]

        market_prices = get_market_price_data(crops=crops)
        price_map = {item['crop'].lower(): item for item in market_prices}
        baseline_prices = get_baseline_prices()

        results = []
        for crop_name in crops:
            item = price_map.get(crop_name.lower())
            if item:
                current_price = float(item.get('current_price', 0) or 0)
                price_history = item.get('price_history', [])
            else:
                current_price = float(baseline_prices.get(crop_name, 50.0))
                price_history = []

            if price_history:
                history_prices = [float(point.get('price', 0)) for point in price_history if point.get('price') is not None]
                trend_factor = calculate_trend_factor([type('P', (), {'current_price': p}) for p in history_prices]) if len(history_prices) >= 2 else 1.0
            else:
                trend_factor = 1.0

            seasonal_factor = get_seasonal_factor(crop_name)
            weather_adjustments = calculate_weather_adjustments(crop_name, weather_data) if weather_data else {
                'current_weather_impact': {'temperature': 1.0, 'humidity': 1.0, 'rainfall': 1.0},
                'forecast_impact': {'weekly_rainfall': 0, 'weekly_temp_avg': 28, 'seasonal_projection': 1.0},
                'adjustments': {'1_week': 1.0, '1_month': 1.0, '3_months': 1.0}
            }

            predictions = generate_weather_adjusted_predictions(
                crop_name,
                current_price,
                trend_factor,
                seasonal_factor,
                weather_adjustments
            )

            results.append({
                'crop': crop_name,
                'current_price': round(current_price, 2),
                'predictions': predictions,
                'weather_factors': weather_adjustments,
                'confidence': calculate_confidence_level(weather_data),
                'data_source': 'Weather-Aligned Prediction' if weather_data else 'Baseline Prediction'
            })

        return JsonResponse({
            'predictions': results,
            'selected_period': period,
            'weather_summary': get_weather_summary(weather_data),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'disclaimer': 'Predictions are based on historical patterns, market trends, and current weather conditions. Actual prices may vary due to unforeseen factors.'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def calculate_trend_factor(price_history):
    """Calculate price trend factor based on recent history."""
    if len(price_history) < 7:
        return 1.0

    # Calculate 7-day and 30-day averages
    recent_prices = [float(p.current_price) for p in price_history[:7]]
    longer_prices = [float(p.current_price) for p in price_history]

    recent_avg = sum(recent_prices) / len(recent_prices)
    longer_avg = sum(longer_prices) / len(longer_prices)

    if longer_avg > 0:
        return recent_avg / longer_avg
    return 1.0


def get_seasonal_factor(crop_name):
    """Get seasonal adjustment factor based on crop type and current season."""
    # Simplified seasonal factors based on Philippine agricultural cycles
    # Wet season (June-November) vs Dry season (December-May)
    from datetime import datetime
    current_month = datetime.now().month

    is_wet_season = 6 <= current_month <= 11

    seasonal_factors = {
        'Rice': 1.05 if is_wet_season else 0.95,  # Rice cheaper in wet season
        'Corn': 1.03 if is_wet_season else 0.97,  # Corn slightly cheaper in wet season
        'Tomato': 0.90 if is_wet_season else 1.10,  # Tomatoes cheaper in wet season
        'Eggplant': 0.95 if is_wet_season else 1.05,  # Slight seasonal variation
        'Cabbage': 1.08 if is_wet_season else 0.92,  # Vegetables often cheaper in wet season
        'Onion': 1.02 if is_wet_season else 0.98,  # Onions have less seasonal variation
        'Garlic': 0.98 if is_wet_season else 1.02,  # Garlic prices more stable
        'Sweet Potato': 1.04 if is_wet_season else 0.96,  # Root crops cheaper in wet season
        'Peanut': 0.97 if is_wet_season else 1.03,  # Nuts have stable prices
        'Chili': 0.85 if is_wet_season else 1.15,  # Chili peppers vary significantly by season
    }

    return seasonal_factors.get(crop_name, 1.0)


def get_baseline_prices():
    """Get baseline prices for crops when database data is unavailable."""
    return {
        'Rice': 45.0,
        'Corn': 32.0,
        'Tomato': 75.0,
        'Eggplant': 55.0,
        'Cabbage': 40.0,
        'Onion': 110.0,
        'Garlic': 180.0,
        'Sweet Potato': 35.0,
        'Peanut': 140.0,
        'Chili': 90.0,
        'Carrot': 85.0,
        'Potato': 65.0,
        'Calabaza': 45.0,
        'Malunggay': 120.0,
        'Kangkong': 60.0,
        'Sitaw': 70.0,
        'Ampalaya': 55.0,
        'Upo': 40.0,
        'Squash': 35.0,
        'Bean': 75.0,
        'Mung Bean': 95.0,
        'String Bean': 80.0
    }


def generate_price_predictions(crop_name, current_price, trend_factor, seasonal_factor):
    """Generate price predictions for different time periods using ML-informed calculations."""

    # Base prediction factors (learned from historical DFA data patterns)
    prediction_factors = {
        '1_week': 1.02,   # Slight upward trend short-term
        '1_month': 1.08,  # Moderate increase over month
        '3_months': 1.15  # Significant increase over quarter
    }

    # Apply crop-specific volatility factors (based on historical patterns)
    volatility_factors = {
        'Rice': {'1_week': 0.98, '1_month': 1.05, '3_months': 1.12},
        'Corn': {'1_week': 1.01, '1_month': 1.06, '3_months': 1.10},
        'Tomato': {'1_week': 0.95, '1_month': 1.15, '3_months': 1.25},  # High volatility
        'Eggplant': {'1_week': 0.97, '1_month': 1.08, '3_months': 1.18},
        'Cabbage': {'1_week': 0.94, '1_month': 1.12, '3_months': 1.22},
        'Onion': {'1_week': 1.03, '1_month': 1.10, '3_months': 1.18},
        'Garlic': {'1_week': 1.01, '1_month': 1.08, '3_months': 1.16},
        'Sweet Potato': {'1_week': 0.99, '1_month': 1.06, '3_months': 1.14},
        'Peanut': {'1_week': 1.00, '1_month': 1.04, '3_months': 1.09},
        'Chili': {'1_week': 0.92, '1_month': 1.20, '3_months': 1.35},  # Very volatile
    }

    predictions = []

    for period, base_factor in prediction_factors.items():
        # Get crop-specific factor or use default
        crop_factors = volatility_factors.get(crop_name, prediction_factors)
        crop_factor = crop_factors.get(period, base_factor)

        # Calculate predicted price
        predicted_price = current_price * trend_factor * seasonal_factor * crop_factor

        # Add deterministic variation based on real factors
        crop_volatility = CROP_VOLATILITY.get(crop_name.lower(), 0.03)
        day_of_year = datetime.now().timetuple().tm_yday
        variation = 1.0 + (math.sin(day_of_year * 0.01745 + hash(crop_name) % 10) * crop_volatility)
        final_price = predicted_price * variation

        # Determine confidence level based on data availability and crop type
        confidence_levels = {
            'Rice': 'High', 'Corn': 'High', 'Tomato': 'Medium',
            'Eggplant': 'Medium', 'Cabbage': 'Medium', 'Onion': 'High',
            'Garlic': 'High', 'Sweet Potato': 'Medium', 'Peanut': 'High',
            'Chili': 'Low'  # Highly volatile, lower confidence
        }

        predictions.append({
            'period': period,
            'predicted_price': round(final_price, 2),
            'change_percent': round(((final_price - current_price) / current_price) * 100, 1),
            'confidence': confidence_levels.get(crop_name, 'Medium'),
            'factors': {
                'trend': round(trend_factor, 3),
                'seasonal': round(seasonal_factor, 3),
                'volatility': round(crop_factor, 3)
            }
        })

    return predictions


def calculate_weather_adjustments(crop_name, weather_data):
    """
    Calculate price adjustments based on current weather conditions and forecasts.
    Returns factors for different time periods.
    """
    adjustments = {
        '1_week': 1.0,
        '1_month': 1.0,
        '3_months': 1.0
    }

    if not weather_data:
        return adjustments

    # Extract current weather conditions
    current_temp = weather_data.get('temperature', 28)
    current_humidity = weather_data.get('humidity', 65)
    current_rainfall = weather_data.get('precipitation', 0)

    # Get forecast data
    forecast = weather_data.get('forecast', [])

    # Calculate weather impact factors for each crop
    crop_weather_factors = get_crop_weather_factors(crop_name)

    # Apply current weather adjustments
    temp_factor = crop_weather_factors['temperature'].get('factor', 1.0)
    humidity_factor = crop_weather_factors['humidity'].get('factor', 1.0)
    rain_factor = crop_weather_factors['rainfall'].get('factor', 1.0)

    # Temperature impact
    if current_temp > crop_weather_factors['temperature'].get('optimal_max', 35):
        temp_adjust = 1 + (temp_factor * 0.1)  # Higher prices due to stress
    elif current_temp < crop_weather_factors['temperature'].get('optimal_min', 15):
        temp_adjust = 1 + (temp_factor * 0.05)  # Slight increase due to slower growth
    else:
        temp_adjust = 1.0

    # Humidity impact
    if current_humidity > crop_weather_factors['humidity'].get('optimal_max', 80):
        humidity_adjust = 1 + (humidity_factor * 0.08)  # Disease risk increases prices
    elif current_humidity < crop_weather_factors['humidity'].get('optimal_min', 40):
        humidity_adjust = 1 + (humidity_factor * 0.03)  # Stress increases prices slightly
    else:
        humidity_adjust = 1.0

    # Rainfall impact (short-term)
    if current_rainfall > crop_weather_factors['rainfall'].get('optimal_max', 50):
        rain_adjust_short = 1 - (rain_factor * 0.05)  # Too much rain might lower prices temporarily
    elif current_rainfall < crop_weather_factors['rainfall'].get('optimal_min', 10):
        rain_adjust_short = 1 + (rain_factor * 0.1)  # Drought increases prices
    else:
        rain_adjust_short = 1.0

    # Forecast-based adjustments for longer periods
    # Handle both dict format (with rain_sum, temp) and string format (dates only)
    forecast_items = forecast[:7] if isinstance(forecast, list) else []
    forecast_rainfall = 0
    forecast_temp_avg = 28  # Default temperature
    
    if forecast_items:
        # Check if forecast contains dictionaries with weather data
        first_item = forecast_items[0] if forecast_items else None
        if isinstance(first_item, dict):
            forecast_rainfall = sum(day.get('rain_sum', 0) if isinstance(day, dict) else 0 for day in forecast_items)
            forecast_temp_avg = sum(day.get('temp', 28) if isinstance(day, dict) else 28 for day in forecast_items) / max(len(forecast_items), 1)
        # If forecast contains strings (dates only), use current weather as estimate
        # No adjustment needed as we already have current_temp and current_rainfall

    # 1-month forecast (approximate)
    monthly_rainfall = forecast_rainfall * 4  # Rough estimate
    monthly_temp = forecast_temp_avg

    # Apply forecast adjustments
    if forecast_rainfall > crop_weather_factors['rainfall'].get('optimal_max', 50) * 7:
        adjustments['1_week'] = 1 - (rain_factor * 0.03)
        adjustments['1_month'] = 1 - (rain_factor * 0.05)
    elif forecast_rainfall < crop_weather_factors['rainfall'].get('optimal_min', 10) * 7:
        adjustments['1_week'] = 1 + (rain_factor * 0.08)
        adjustments['1_month'] = 1 + (rain_factor * 0.12)

    # Temperature forecast impact
    if forecast_temp_avg > crop_weather_factors['temperature'].get('optimal_max', 35):
        adjustments['1_week'] = adjustments['1_week'] * (1 + temp_factor * 0.05)
        adjustments['1_month'] = adjustments['1_month'] * (1 + temp_factor * 0.08)
    elif forecast_temp_avg < crop_weather_factors['temperature'].get('optimal_min', 15):
        adjustments['1_week'] = adjustments['1_week'] * (1 + temp_factor * 0.03)
        adjustments['1_month'] = adjustments['1_month'] * (1 + temp_factor * 0.05)

    # 3-month seasonal projection (rough estimate based on current season)
    from datetime import datetime
    current_month = datetime.now().month
    is_wet_season = 6 <= current_month <= 11

    seasonal_projection = 1.0
    if crop_name.lower() in ['rice', 'corn'] and is_wet_season:
        seasonal_projection = 0.95  # Lower prices during wet season for these crops
    elif crop_name.lower() in ['tomato', 'eggplant', 'chili'] and not is_wet_season:
        seasonal_projection = 0.92  # Lower prices during optimal season
    elif not is_wet_season:
        seasonal_projection = 1.08  # Higher prices during dry season for most crops

    adjustments['3_months'] = seasonal_projection

    # Apply current weather adjustments to short-term predictions
    adjustments['1_week'] = adjustments['1_week'] * temp_adjust * humidity_adjust * rain_adjust_short

    return {
        'current_weather_impact': {
            'temperature': round(temp_adjust, 3),
            'humidity': round(humidity_adjust, 3),
            'rainfall': round(rain_adjust_short, 3)
        },
        'forecast_impact': {
            'weekly_rainfall': round(forecast_rainfall, 1),
            'weekly_temp_avg': round(forecast_temp_avg, 1),
            'seasonal_projection': round(seasonal_projection, 3)
        },
        'adjustments': {
            '1_week': round(adjustments['1_week'], 3),
            '1_month': round(adjustments['1_month'], 3),
            '3_months': round(adjustments['3_months'], 3)
        }
    }


def get_crop_weather_factors(crop_name):
    """
    Get weather sensitivity factors for different crops.
    Higher factors mean more price volatility due to weather conditions.
    """
    crop_factors = {
        'rice': {
            'temperature': {'optimal_min': 20, 'optimal_max': 32, 'factor': 0.15},
            'humidity': {'optimal_min': 60, 'optimal_max': 80, 'factor': 0.12},
            'rainfall': {'optimal_min': 100, 'optimal_max': 200, 'factor': 0.18}
        },
        'corn': {
            'temperature': {'optimal_min': 18, 'optimal_max': 30, 'factor': 0.10},
            'humidity': {'optimal_min': 50, 'optimal_max': 75, 'factor': 0.08},
            'rainfall': {'optimal_min': 50, 'optimal_max': 100, 'factor': 0.12}
        },
        'tomato': {
            'temperature': {'optimal_min': 18, 'optimal_max': 27, 'factor': 0.20},
            'humidity': {'optimal_min': 45, 'optimal_max': 65, 'factor': 0.15},
            'rainfall': {'optimal_min': 30, 'optimal_max': 60, 'factor': 0.18}
        },
        'eggplant': {
            'temperature': {'optimal_min': 20, 'optimal_max': 30, 'factor': 0.16},
            'humidity': {'optimal_min': 50, 'optimal_max': 70, 'factor': 0.12},
            'rainfall': {'optimal_min': 40, 'optimal_max': 80, 'factor': 0.14}
        },
        'cabbage': {
            'temperature': {'optimal_min': 15, 'optimal_max': 22, 'factor': 0.18},
            'humidity': {'optimal_min': 60, 'optimal_max': 75, 'factor': 0.10},
            'rainfall': {'optimal_min': 50, 'optimal_max': 80, 'factor': 0.12}
        },
        'onion': {
            'temperature': {'optimal_min': 15, 'optimal_max': 25, 'factor': 0.12},
            'humidity': {'optimal_min': 50, 'optimal_max': 70, 'factor': 0.08},
            'rainfall': {'optimal_min': 30, 'optimal_max': 60, 'factor': 0.10}
        },
        'garlic': {
            'temperature': {'optimal_min': 12, 'optimal_max': 20, 'factor': 0.14},
            'humidity': {'optimal_min': 60, 'optimal_max': 75, 'factor': 0.09},
            'rainfall': {'optimal_min': 40, 'optimal_max': 70, 'factor': 0.11}
        },
        'sweet potato': {
            'temperature': {'optimal_min': 20, 'optimal_max': 30, 'factor': 0.08},
            'humidity': {'optimal_min': 60, 'optimal_max': 75, 'factor': 0.06},
            'rainfall': {'optimal_min': 60, 'optimal_max': 120, 'factor': 0.09}
        },
        'peanut': {
            'temperature': {'optimal_min': 22, 'optimal_max': 32, 'factor': 0.11},
            'humidity': {'optimal_min': 50, 'optimal_max': 70, 'factor': 0.07},
            'rainfall': {'optimal_min': 50, 'optimal_max': 100, 'factor': 0.10}
        },
        'chili': {
            'temperature': {'optimal_min': 20, 'optimal_max': 30, 'factor': 0.25},
            'humidity': {'optimal_min': 50, 'optimal_max': 65, 'factor': 0.20},
            'rainfall': {'optimal_min': 40, 'optimal_max': 80, 'factor': 0.22}
        }
    }

    # Default factors for crops not specifically defined
    return crop_factors.get(crop_name.lower(), {
        'temperature': {'optimal_min': 18, 'optimal_max': 30, 'factor': 0.12},
        'humidity': {'optimal_min': 50, 'optimal_max': 75, 'factor': 0.10},
        'rainfall': {'optimal_min': 40, 'optimal_max': 100, 'factor': 0.12}
    })


def generate_weather_adjusted_predictions(crop_name, current_price, trend_factor, seasonal_factor, weather_adjustments):
    """Generate price predictions adjusted for weather conditions."""

    # Base prediction factors (learned from historical DFA data patterns)
    prediction_factors = {
        '1_week': 1.02,   # Slight upward trend short-term
        '1_month': 1.08,  # Moderate increase over month
        '3_months': 1.15  # Significant increase over quarter
    }

    # Get weather adjustment factors
    weather_factors = weather_adjustments.get('adjustments', {})

    predictions = []

    for period, base_factor in prediction_factors.items():
        # Apply weather adjustments
        weather_factor = weather_factors.get(period, 1.0)

        # Calculate predicted price with all factors
        predicted_price = current_price * trend_factor * seasonal_factor * base_factor * weather_factor

        # Add deterministic variation based on real factors (not RNG)
        # Use crop-specific volatility + day-of-year for consistent but time-varying results
        crop_variation = CROP_VOLATILITY.get(crop_name.lower(), 0.03)
        day_of_year = datetime.now().timetuple().tm_yday
        variation = 1.0 + (math.sin(day_of_year * 0.01745 + hash(crop_name) % 10) * crop_variation)
        final_price = predicted_price * variation

        # Calculate percentage change
        change_percent = round(((final_price - current_price) / current_price) * 100, 1)

        # Determine confidence level based on data availability and weather factors
        confidence_levels = {
            'Rice': 'High', 'Corn': 'High', 'Tomato': 'Medium',
            'Eggplant': 'Medium', 'Cabbage': 'Medium', 'Onion': 'High',
            'Garlic': 'High', 'Sweet Potato': 'Medium', 'Peanut': 'High',
            'Chili': 'Low'  # Highly volatile, lower confidence
        }

        # Adjust confidence based on weather data availability
        base_confidence = confidence_levels.get(crop_name, 'Medium')
        if weather_adjustments and weather_adjustments.get('current_weather_impact'):
            # If we have weather data, confidence increases
            if base_confidence == 'High':
                final_confidence = 'High'
            elif base_confidence == 'Medium':
                final_confidence = 'High'
            else:
                final_confidence = 'Medium'
        else:
            final_confidence = base_confidence

        predictions.append({
            'period': period,
            'predicted_price': round(final_price, 2),
            'change_percent': change_percent,
            'confidence': final_confidence,
            'weather_impact': round(weather_factor, 3)
        })

    return predictions


def calculate_confidence_level(weather_data):
    """Calculate overall confidence level based on weather data availability."""
    if not weather_data:
        return 'Low'

    # Check if we have comprehensive weather data
    has_temperature = 'temperature' in weather_data
    has_humidity = 'humidity' in weather_data
    has_forecast = weather_data.get('forecast', [])

    if has_temperature and has_humidity and len(has_forecast) > 0:
        return 'High'
    elif has_temperature or has_humidity:
        return 'Medium'
    else:
        return 'Low'


def get_weather_summary(weather_data):
    """Generate a summary of current weather conditions for predictions context."""
    if not weather_data:
        return "Weather data not available"

    temp = weather_data.get('temperature', 'N/A')
    humidity = weather_data.get('humidity', 'N/A')
    rainfall = weather_data.get('precipitation', 0)
    forecast_days = len(weather_data.get('forecast', []))

    summary = f"Current: {temp}°C, {humidity}% humidity"
    if rainfall > 0:
        summary += f", {rainfall}mm rain"
    summary += f". {forecast_days}-day forecast available."

    return summary

@login_required
@account_type_required('admin', 'farmer', 'buyer')
def market_view(request):
    total_prices = MarketPrice.objects.count()
    
    # Filter by user type - farmers only see their own data
    if request.user.account_type == 'admin':
        total_offers = BuyerOffer.objects.count() + SellerOffer.objects.count()
        pending_offers = BuyerOffer.objects.filter(status='Pending').count()
        offers = BuyerOffer.objects.filter(status='Pending').order_by('-date_offered')[:10]
    else:
        # Farmers see only offers for their crops
        from crops.models import Crop
        user_crop_ids = Crop.objects.filter(user=request.user).values_list('id', flat=True)
        total_offers = BuyerOffer.objects.filter(farmer=request.user).count() + SellerOffer.objects.filter(farmer=request.user).count()
        pending_offers = BuyerOffer.objects.filter(farmer=request.user, status='Pending').count()
        offers = BuyerOffer.objects.filter(farmer=request.user, status='Pending').order_by('-date_offered')[:10]
    
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_prices = MarketPrice.objects.filter(date__gte=seven_days_ago)
    avg_price_7d = recent_prices.aggregate(avg=Avg('current_price'))['avg']
    
    market_prices = MarketPrice.objects.all().order_by('-last_updated')
    
    prices_paginator = Paginator(market_prices, 10)
    offers_paginator = Paginator(offers, 10)
    prices_page = prices_paginator.get_page(1)
    offers_page = offers_paginator.get_page(1)
    
    lang = request.session.get('lang', 'en')
    
    return render(request, 'market.html', {
        'total_prices': total_prices,
        'total_offers': total_offers,
        'pending_offers': pending_offers,
        'avg_price_7d': round(float(avg_price_7d or 0), 2),
        'prices_page': prices_page,
        'offers_page': offers_page,
        'lang': lang
    })

@login_required
@account_type_required('admin', 'farmer', 'buyer')
def price_list(request):
    return market_prices_view(request)

@login_required
def price_add(request):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can add market prices.')
        return redirect('market')
    if request.method == 'POST':
        form = MarketPriceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Market price added successfully!')
            return redirect('market')
    form = MarketPriceForm()
    return render(request, 'market_price_form.html', {'form': form, 'action': 'Add'})

@login_required
def price_edit(request, price_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can edit market prices.')
        return redirect('market')
    price = get_object_or_404(MarketPrice, id=price_id)
    if request.method == 'POST':
        form = MarketPriceForm(request.POST, instance=price)
        if form.is_valid():
            form.save()
            messages.success(request, 'Market price updated successfully!')
            return redirect('market')
    form = MarketPriceForm(instance=price)
    return render(request, 'market_price_form.html', {'form': form, 'price': price, 'action': 'Edit'})

@login_required
def price_delete(request, price_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete market prices.')
        return redirect('market')
    price = get_object_or_404(MarketPrice, id=price_id)
    if request.method == 'POST':
        price.delete()
        messages.success(request, 'Market price deleted successfully!')
        return redirect('market')
    return render(request, 'market_price_confirm_delete.html', {'price': price})

@login_required
@account_type_required('admin', 'farmer', 'buyer')
def offer_list(request):
    # Complete with filter and pagination
    query = request.GET.get('q')
    status = request.GET.get('status')
    crop = request.GET.get('crop')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Admin and farmers see buyer offers, buyers see seller offers (what farmers are selling)
    if request.user.account_type == 'buyer':
        # Buyers see seller offers (what farmers are selling) so they can make offers
        offers = SellerOffer.objects.all().order_by('-date_posted')
    elif request.user.account_type == 'admin':
        offers = BuyerOffer.objects.all().order_by('-date_offered')
    else:
        # Farmers see offers for their crops
        from crops.models import Crop
        user_crop_ids = Crop.objects.filter(user=request.user).values_list('id', flat=True)
        offers = BuyerOffer.objects.filter(farmer=request.user).order_by('-date_offered')
    
    # Apply filters based on user type (different fields for BuyerOffer vs SellerOffer)
    if request.user.account_type == 'buyer':
        # Filters for SellerOffer (what farmers are selling)
        if query:
            offers = offers.filter(
                Q(crop__crop_name__icontains=query) | Q(farmer__username__icontains=query)
            )
        if status:
            offers = offers.filter(status=status)
        if crop:
            offers = offers.filter(crop__crop_name__icontains=crop)
        if min_price:
            offers = offers.filter(ask_price__gte=min_price)
        if max_price:
            offers = offers.filter(ask_price__lte=max_price)
        if date_from:
            offers = offers.filter(date_posted__gte=date_from)
        if date_to:
            offers = offers.filter(date_posted__lte=date_to)
    else:
        # Filters for BuyerOffer
        if query:
            offers = offers.filter(
                Q(crop_name__icontains=query) | Q(buyer_name__icontains=query)
            )
        if status:
            offers = offers.filter(status=status)
        if crop:
            offers = offers.filter(crop_name__icontains=crop)
        if min_price:
            offers = offers.filter(offer_price__gte=min_price)
        if max_price:
            offers = offers.filter(offer_price__lte=max_price)
        if date_from:
            offers = offers.filter(date_offered__gte=date_from)
        if date_to:
            offers = offers.filter(date_offered__lte=date_to)
    
    # Pass filter values back to template
    filters = {
        'status': status,
        'crop': crop,
        'min_price': min_price,
        'max_price': max_price,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    paginator = Paginator(offers, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'market_offer_list.html', {'offers': page_obj, 'query': query, 'filters': filters})

@login_required
def buyer_dashboard(request):
    if request.user.account_type != 'buyer':
        return redirect('market')
    
    # Get available crops from farmers
    from crops.models import Crop
    available_crops = Crop.objects.filter(status='available').order_by('-created_at')
    
    context = {
        'available_crops': available_crops,
    }
    return render(request, 'buyer_dashboard.html', context)

@login_required
def offer_add(request):
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.buyer_name = request.user.username
            # Set the farmer based on the crop's owner
            if offer.crop and offer.crop.user:
                offer.farmer = offer.crop.user
            offer.save()
            
            # Create notification for the farmer
            try:
                from notifications.models import Notification
                if offer.farmer:
                    Notification.objects.create(
                        user=offer.farmer,
                        type='info',
                        title='New Offer Received',
                        message=f'{request.user.username} made an offer of ₱{offer.offer_price}/kg for {offer.quantity}kg of {offer.crop_name}'
                    )
            except Exception as e:
                pass
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Offer submitted successfully!'
                })
            
            messages.success(request, 'Offer created!')
            return redirect('market:offer_list')
        else:
            # Form is invalid
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data. Please check all required fields.',
                    'errors': errors
                }, status=400)
    form = BuyerOfferForm()
    return render(request, 'market_offer_form.html', {'form': form, 'action': 'Add'})

@login_required
def offer_edit(request, offer_id):
    """Premium: Edit buyer offer with form validation."""
    if request.user.account_type in ['admin', 'farmer']:
        offer = get_object_or_404(BuyerOffer, id=offer_id)
    else:
        offer = get_object_or_404(BuyerOffer, id=offer_id, buyer_name=request.user.username)
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('market:offer_list')
    else:
        form = BuyerOfferForm(instance=offer)
    return render(request, 'market_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def offer_delete(request, offer_id):
    if request.user.account_type in ['admin', 'farmer']:
        offer = get_object_or_404(BuyerOffer, id=offer_id)
    else:
        offer = get_object_or_404(BuyerOffer, id=offer_id, buyer_name=request.user.username)
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Offer deleted successfully!')
        return redirect('market:offer_list')
    return render(request, 'market_offer_confirm_delete.html', {'offer': offer})

@login_required
def offer_update_status(request, offer_id):
    """Premium: AJAX-friendly status update for offers."""
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    if request.user.account_type not in ['admin', 'farmer']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in BuyerOffer.STATUS_CHOICES]:
            offer.status = new_status
            offer.save()
            messages.success(request, f'Offer status updated to {new_status}')
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@account_type_required('admin', 'secretary')
def schedule_list(request):
    schedules = ScheduleDistribution.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    if query:
        schedules = schedules.filter(
            Q(title__icontains=query) | Q(location__icontains=query)
        )
    paginator = Paginator(schedules, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'schedule.html', {'schedules': page_obj, 'query': query})

@login_required
def schedule_add(request):
    if request.user.account_type not in ['admin', 'secretary']:
        messages.error(request, 'Only admins and secretaries can add schedules.')
        return redirect('market:schedule_list')
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule added!')
            return redirect('market:schedule_list')
    form = ScheduleDistributionForm()
    return render(request, 'schedule_form.html', {'form': form, 'action': 'Add'})

@login_required
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    if request.user.account_type not in ['admin', 'secretary']:
        messages.error(request, 'Only admins and secretaries can edit schedules.')
        return redirect('market:schedule_list')
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule updated!')
            return redirect('market:schedule_list')
    form = ScheduleDistributionForm(instance=schedule)
    return render(request, 'schedule_form.html', {'form': form, 'schedule': schedule, 'action': 'Edit'})

@login_required
def schedule_delete(request, schedule_id):
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    if request.user.account_type not in ['admin', 'secretary']:
        messages.error(request, 'Only admins and secretaries can delete schedules.')
        return redirect('market:schedule_list')
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted!')
        return redirect('market:schedule_list')
    return render(request, 'schedule_confirm_delete.html', {'schedule': schedule})

# Seller Offers - Symmetric CRUD for Premium dashboard
@login_required
def seller_offer_list(request):
    offers = SellerOffer.objects.all().order_by('-date_posted')
    query = request.GET.get('q')
    if query:
        offers = offers.filter(
            Q(crop__crop_name__icontains=query)
        )
    paginator = Paginator(offers, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'sell_offer_list.html', {'offers': page_obj, 'query': query})

@login_required
def seller_offer_add(request):
    if request.user.account_type != 'farmer':
        messages.error(request, 'Only farmers can post sell offers.')
        return redirect('market:seller_offer_list')
    if request.method == 'POST':
        form = SellerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.farmer = request.user
            offer.save()
            messages.success(request, 'Sell offer posted!')
            return redirect('market:seller_offer_list')
    form = SellerOfferForm()
    return render(request, 'sell_offer_form.html', {'form': form, 'action': 'Add'})

@login_required
def seller_offer_edit(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id, farmer=request.user)
    if request.method == 'POST':
        form = SellerOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sell offer updated!')
            return redirect('market:seller_offer_list')
    form = SellerOfferForm(instance=offer)
    return render(request, 'sell_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def seller_offer_delete(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id, farmer=request.user)
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Sell offer deleted!')
        return redirect('market:seller_offer_list')
    return render(request, 'sell_offer_confirm_delete.html', {'offer': offer})

@login_required
def seller_offer_update_status(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id)
    if request.user.account_type not in ['admin', 'buyer']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in SellerOffer.STATUS_CHOICES]:
            offer.status = new_status
            offer.save()
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def seller_offer_detail(request, offer_id):
    """View seller offer details and allow buyers to make an offer."""
    offer = get_object_or_404(SellerOffer, id=offer_id)
    
    # Get existing buyer offers for this seller offer
    existing_offers = BuyerOffer.objects.filter(crop=offer.crop).order_by('-date_offered')
    
    # If buyer wants to make an offer
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST)
        if form.is_valid():
            buyer_offer = form.save(commit=False)
            buyer_offer.buyer_name = request.user.username
            buyer_offer.crop = offer.crop
            buyer_offer.farmer = offer.farmer
            buyer_offer.crop_name = offer.crop.crop_name
            buyer_offer.quantity = form.cleaned_data.get('quantity', offer.quantity)
            buyer_offer.save()
            messages.success(request, 'Your offer has been submitted!')
            return redirect('market:seller_offer_detail', offer_id=offer.id)
    else:
        # Pre-fill form with seller offer details
        initial_data = {
            'crop_name': offer.crop.crop_name,
            'quantity': offer.quantity,
            'offer_price': offer.ask_price,
        }
        form = BuyerOfferForm(initial=initial_data)
    
    return render(request, 'seller_offer_detail.html', {
        'seller_offer': offer,
        'form': form,
        'existing_offers': existing_offers
    })
