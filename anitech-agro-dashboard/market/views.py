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
from .services import (
    ensure_market_price_data_available,
    get_market_data_version,
    get_market_sync_status,
    is_market_data_stale,
    sync_bantay_presyo_market_prices,
    trigger_bantay_presyo_sync_async,
)
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

CROP_FORECAST_ALIASES = {
    'commercial milled rice': 'Rice',
    'rice (commercial milled)': 'Rice',
    'red onion': 'Onion',
    'chinese cabbage': 'Cabbage',
    'pechay': 'Cabbage',
    'string beans': 'Bean',
    'string bean': 'Bean',
    'sitao': 'Bean',
    'kalabasa': 'Squash',
    'talong': 'Eggplant',
    'ampalaya': 'Ampalaya',
    'watermelon': 'Watermelon',
    'melon': 'Melon',
    'calamansi': 'Calamansi',
}
from anitech.views import account_type_required


# Cache for market price data (module-level for performance)
_market_price_cache = {}
_cache_timestamp = None
CACHE_TIMEOUT = 300  # 5 minutes cache
EXCLUDED_MARKET_CROPS = {'audit crop', 'audit crop2'}


def _is_valid_market_price(value):
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(numeric) and numeric > 0


def _is_excluded_market_crop(crop_name):
    return str(crop_name or '').strip().lower() in EXCLUDED_MARKET_CROPS


def _filter_valid_market_predictions(predictions):
    valid_predictions = []
    for item in predictions:
        if not _is_valid_market_price(item.get('current_price')):
            continue

        periods = item.get('predictions') or []
        period_map = {
            period.get('period'): period.get('predicted_price')
            for period in periods
            if isinstance(period, dict)
        }
        if not all(
            _is_valid_market_price(period_map.get(period_name))
            for period_name in ['1_week', '1_month', '3_months']
        ):
            continue

        valid_predictions.append(item)
    return valid_predictions


def _log_buyer_offer_activity(request, offer, event_type, action, description, status='success'):
    try:
        from activity_log.utils import log_activity
        log_activity(
            request=request,
            user=request.user,
            event_type=event_type,
            severity='info',
            status=status,
            action=action,
            description=description,
            resource_type='market',
            resource_id=str(offer.id),
            resource_name=offer.crop_name,
        )
    except Exception:
        pass


def _build_seller_offer_form(user, *args, **kwargs):
    """Limit seller-offer crop choices to crops owned by the current farmer."""
    form = SellerOfferForm(*args, **kwargs)
    form.fields['crop'].queryset = Crop.objects.filter(user=user).order_by('crop_name')
    return form


def _get_market_weather_data():
    from ml_service.views import get_current_weather

    weather_info = get_current_weather()
    return {
        'temperature': weather_info.get('temperature', 28),
        'humidity': weather_info.get('humidity', 65),
        'precipitation': weather_info.get('precipitation', 0),
        'rainfall': weather_info.get('rainfall', 0)
    }


def get_market_price_data(crops=None, use_cache=True):
    """Fetch market price summaries and recent history for the market prices page.
    Optimized with caching and efficient queries.
    """
    from django.core.cache import cache
    from datetime import time
    
    # Generate cache key
    cache_key = (
        f"market_price_data_v{get_market_data_version()}_"
        + '_'.join(sorted(crops) if crops else ['all'])
    )
    
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

    crop_names = [crop_name for crop_name in crop_names if not _is_excluded_market_crop(crop_name)]

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
        if _is_excluded_market_crop(record.crop_name):
            continue
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


# @login_required
# @account_type_required('admin', 'farmer', 'buyer')
def market_prices_view(request):
    """Pure Django view for /market/ - renders prices.html with DB data + trends."""
    ensure_market_price_data_available()
    trigger_bantay_presyo_sync_async(only_if_stale=True)
    price_data = get_market_price_data()
    crops = [item['crop'] for item in price_data if _is_valid_market_price(item.get('current_price'))]
    
    # Get weather data using cached function
    weather_data = _get_market_weather_data()
    
    import hashlib
    price_snapshot = {item['crop']: item['current_price'] for item in price_data}
    key_string = json.dumps({'crops': sorted(crops), 'weather': weather_data, 'prices': price_snapshot}, sort_keys=True)
    cache_key = f"market_predictions_{hashlib.md5(key_string.encode()).hexdigest()}"
    precomputed_predictions = cache.get(cache_key)

    if precomputed_predictions is None:
        try:
            precomputed_predictions = generate_ml_market_predictions(crops, weather_data)
        except Exception:
            precomputed_predictions = generate_fallback_market_predictions(crops)
        precomputed_predictions = _filter_valid_market_predictions(precomputed_predictions)
        cache.set(cache_key, precomputed_predictions, 600)
    else:
        precomputed_predictions = _filter_valid_market_predictions(precomputed_predictions)
    
    context = {
        'prices': precomputed_predictions,
        'prices_json': json.dumps(precomputed_predictions),
        'predictions_json': json.dumps(precomputed_predictions),
        'lang': request.session.get('lang', 'en'),
        'market_sync_status': get_market_sync_status(),
        'market_data_is_stale': is_market_data_stale(),
    }
    return render(request, 'market/prices.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_market_prices(request):
    force_refresh = str(request.POST.get('force', '')).lower() in {'1', 'true', 'yes'}
    run_async = str(request.POST.get('async', 'true')).lower() not in {'0', 'false', 'no'}

    if run_async:
        started = trigger_bantay_presyo_sync_async(force=force_refresh, only_if_stale=not force_refresh)
        status_code = 202 if started else 200
        return JsonResponse(
            {
                'started': started,
                'async': True,
                'status': get_market_sync_status(),
            },
            status=status_code,
        )

    result = sync_bantay_presyo_market_prices(force=force_refresh)
    status_code = 200 if result.get('status') == 'success' else 409 if result.get('reason') == 'sync_in_progress' else 500
    return JsonResponse(
        {
            **result,
            'async': False,
            'status': get_market_sync_status(),
        },
        status=status_code,
    )

@csrf_exempt
@require_http_methods(["POST"])
def forecast_price(request):
    """POST /market/forecast/ - Get actual market prices from database."""
    try:
        ensure_market_price_data_available()
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
    """POST /market/price-predictions/ - Generate market price predictions for crops using current Open-Meteo weather data."""
    try:
        ensure_market_price_data_available()
        data = json.loads(request.body)
        crops = data.get('crops', []) or []
        period = data.get('period', '1_week')

        if isinstance(crops, str):
            crops = [crops]
        crops = [crop.strip() for crop in crops if crop and str(crop).strip()]

        if not crops:
            crops = [item['crop'] for item in get_market_price_data()]

        # Fetch current weather from Open-Meteo API
        from ml_service.views import get_current_weather
        weather_data = get_current_weather()

        # Determine season based on current weather
        season = 'Wet' if weather_data.get('rainfall', 0) > 100 else 'Dry'

        # Use ML model to predict prices for each crop
        from ml_service.market_price_predictor import predict_market_price

        predicted_prices = {}
        for crop_name in crops:
            try:
                # Pass weather features to ML model
                prediction = predict_market_price(
                    crop=crop_name,
                    location='Legazpi City',  # Default location, could be made configurable
                    season=season,
                    months_ahead=1 if period == '1_month' else 3 if period == '3_months' else 0,
                    weather_data=weather_data
                )
                predicted_prices[crop_name] = prediction.get('predicted_price_php', get_baseline_prices().get(crop_name, 50.0))
            except Exception as e:
                # Fallback to baseline price if ML prediction fails
                baseline_prices = get_baseline_prices()
                predicted_prices[crop_name] = baseline_prices.get(crop_name, 50.0)

        return JsonResponse({
            'predicted_prices': predicted_prices,
            'weather_data': weather_data,
            'season': season,
            'period': period,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'disclaimer': 'Predictions are based on current Open-Meteo weather data and ML model analysis. Actual prices may vary due to unforeseen factors.'
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
        'Rice': 50.0,  # Updated to be closer to ML predictions
        'Corn': 35.0,
        'Tomato': 80.0,
        'Eggplant': 60.0,
        'Cabbage': 45.0,
        'Onion': 120.0,
        'Garlic': 190.0,
        'Sweet Potato': 40.0,
        'Peanut': 150.0,
        'Chili': 95.0,
        'Carrot': 90.0,
        'Potato': 70.0,
        'Calabaza': 50.0,
        'Malunggay': 125.0,
        'Kangkong': 65.0,
        'Sitaw': 75.0,
        'Ampalaya': 60.0,
        'Upo': 45.0,
        'Squash': 40.0,
        'Bean': 80.0,
        'Mung Bean': 100.0,
        'String Bean': 85.0
    }


def generate_ml_market_predictions(crops, weather_data):
    """Generate ML-based market prices and forecasts for each crop."""
    from ml_service.market_price_predictor import predict_market_price

    if not crops:
        return []

    season = 'Wet' if weather_data and weather_data.get('rainfall', 0) > 100 else 'Dry'
    baseline_prices = get_baseline_prices()
    actual_price_map = {
        item['crop']: float(item['current_price'] or 0)
        for item in get_market_price_data(crops=crops, use_cache=True)
    }
    results = []

    for crop_name in crops:
        model_crop_name = CROP_FORECAST_ALIASES.get(crop_name.lower(), crop_name)
        crop_history = next((item for item in get_market_price_data(crops=[crop_name], use_cache=True)), None)
        history_points = crop_history.get('price_history', []) if crop_history else []
        history_len = len(history_points)
        trend_factor = calculate_trend_factor([
            type('PricePoint', (), {'current_price': point['price']})() for point in reversed(history_points)
        ]) if history_len >= 2 else 1.0
        seasonal_factor = get_seasonal_factor(model_crop_name)
        weather_adjustments = calculate_weather_adjustments(model_crop_name, weather_data) if weather_data else {
            'current_weather_impact': {'temperature': 1.0, 'humidity': 1.0, 'rainfall': 1.0},
            'forecast_impact': {'weekly_rainfall': 0, 'weekly_temp_avg': 28, 'seasonal_projection': 1.0},
            'adjustments': {'1_week': 1.0, '1_month': 1.0, '3_months': 1.0}
        }
        actual_current_price = float(actual_price_map.get(crop_name) or 0)
        if actual_current_price <= 0:
            continue

        weather_projection = {
            item['period']: float(item['predicted_price'])
            for item in generate_weather_adjusted_predictions(
                model_crop_name,
                actual_current_price,
                trend_factor,
                seasonal_factor,
                weather_adjustments,
            )
        }

        try:
            current_prediction = predict_market_price(
                crop=model_crop_name,
                location='Bicol',
                season=season,
                months_ahead=0,
                weather_data=weather_data
            )
            month1_prediction = predict_market_price(
                crop=model_crop_name,
                location='Bicol',
                season=season,
                months_ahead=1,
                weather_data=weather_data
            )
            month3_prediction = predict_market_price(
                crop=model_crop_name,
                location='Bicol',
                season=season,
                months_ahead=3,
                weather_data=weather_data
            )
            model_current_price = float(current_prediction.get('predicted_price_php', actual_current_price))
            model_month1_price = float(month1_prediction.get('predicted_price_php', model_current_price))
            model_month3_price = float(month3_prediction.get('predicted_price_php', model_current_price))

            current_price = actual_current_price
            if model_current_price > 0:
                ml_month1_price = actual_current_price * (model_month1_price / model_current_price)
                ml_3m_price = actual_current_price * (model_month3_price / model_current_price)
            else:
                ml_month1_price = model_month1_price
                ml_3m_price = model_month3_price

            history_weight = 0.65 if history_len >= 4 else 0.45 if history_len >= 2 else 0.25
            model_weight = 1.0 - history_weight
            next_month_price = (weather_projection.get('1_month', actual_current_price) * history_weight) + (ml_month1_price * model_weight)
            next_3m_price = (weather_projection.get('3_months', actual_current_price) * history_weight) + (ml_3m_price * model_weight)
        except Exception as e:
            # Fallback to actual database prices if ML prediction fails
            current_price = float(actual_price_map.get(crop_name) or baseline_prices.get(crop_name, 50.0))
            next_month_price = weather_projection.get('1_month', current_price * 1.05)
            next_3m_price = weather_projection.get('3_months', current_price * 1.10)

        week1_candidate = weather_projection.get('1_week', current_price)
        week1_price = round((week1_candidate * 0.7) + ((current_price + (next_month_price - current_price) * 0.25) * 0.3), 2)
        next_month_price = round(next_month_price, 2)
        next_3m_price = round(next_3m_price, 2)

        # Ensure horizons diverge from current enough to be visible when history is sparse.
        volatility = CROP_VOLATILITY.get(model_crop_name.lower(), 0.03)
        min_week_delta = current_price * max(volatility * 0.6, 0.01)
        min_month_delta = current_price * max(volatility * 1.2, 0.025)
        min_3m_delta = current_price * max(volatility * 2.0, 0.05)

        if abs(week1_price - current_price) < min_week_delta:
            week1_price = round(current_price + (min_week_delta if weather_adjustments['adjustments'].get('1_week', 1.0) >= 1 else -min_week_delta), 2)
        if abs(next_month_price - current_price) < min_month_delta:
            next_month_price = round(current_price + (min_month_delta if weather_adjustments['adjustments'].get('1_month', 1.0) >= 1 else -min_month_delta), 2)
        if abs(next_3m_price - current_price) < min_3m_delta:
            next_3m_price = round(current_price + (min_3m_delta if weather_adjustments['adjustments'].get('3_months', 1.0) >= 1 else -min_3m_delta), 2)

        predictions = [
            {
                'period': 'current',
                'predicted_price': round(current_price, 2),
                'change_percent': 0.0,
                'confidence': calculate_confidence_level(weather_data)
            },
            {
                'period': '1_week',
                'predicted_price': round(week1_price, 2),
                'change_percent': round(((week1_price - current_price) / current_price) * 100, 1) if current_price > 0 else 0.0,
                'confidence': calculate_confidence_level(weather_data)
            },
            {
                'period': '1_month',
                'predicted_price': round(next_month_price, 2),
                'change_percent': round(((next_month_price - current_price) / current_price) * 100, 1) if current_price > 0 else 0.0,
                'confidence': calculate_confidence_level(weather_data)
            },
            {
                'period': '3_months',
                'predicted_price': round(next_3m_price, 2),
                'change_percent': round(((next_3m_price - current_price) / current_price) * 100, 1) if current_price > 0 else 0.0,
                'confidence': calculate_confidence_level(weather_data)
            }
        ]

        results.append({
            'crop': crop_name,
            'current_price': round(current_price, 2),
            'predictions': predictions,
            'weather_factors': weather_adjustments,
            'confidence': calculate_confidence_level(weather_data),
            'data_source': 'ML Prediction',
            'ml_breakdown': {
                'source': 'Bantay Presyo Database',
                'market_crop': crop_name,
                'model_crop': model_crop_name,
                'history_points': history_len,
                'actual_current_price': round(actual_current_price, 2),
                'trend_factor': round(trend_factor, 3),
                'seasonal_factor': round(seasonal_factor, 3),
                'weather_adjustments': weather_adjustments.get('adjustments', {}),
                'current_weather_impact': weather_adjustments.get('current_weather_impact', {}),
                'forecast_impact': weather_adjustments.get('forecast_impact', {}),
            },
        })

    return results


def generate_fallback_market_predictions(crops):
    """Use current DB prices with simple projections when ML dependencies are unavailable."""
    fallback_results = []

    for item in get_market_price_data(crops=crops, use_cache=True):
        current_price = float(item.get('current_price') or 0)
        if current_price <= 0:
            continue

        week1_price = round(current_price * 1.02, 2)
        month1_price = round(current_price * 1.05, 2)
        month3_price = round(current_price * 1.10, 2)

        fallback_results.append({
            'crop': item['crop'],
            'current_price': round(current_price, 2),
            'predictions': [
                {'period': 'current', 'predicted_price': round(current_price, 2), 'change_percent': 0.0, 'confidence': 0.55},
                {'period': '1_week', 'predicted_price': week1_price, 'change_percent': round(((week1_price - current_price) / current_price) * 100, 1), 'confidence': 0.5},
                {'period': '1_month', 'predicted_price': month1_price, 'change_percent': round(((month1_price - current_price) / current_price) * 100, 1), 'confidence': 0.45},
                {'period': '3_months', 'predicted_price': month3_price, 'change_percent': round(((month3_price - current_price) / current_price) * 100, 1), 'confidence': 0.4},
            ],
            'weather_factors': {},
            'confidence': 0.5,
            'data_source': 'Database Fallback',
            'ml_breakdown': {
                'source': 'Bantay Presyo Database',
                'market_crop': item['crop'],
                'model_crop': item['crop'],
                'history_points': len(item.get('price_history', [])),
                'actual_current_price': round(current_price, 2),
                'trend_factor': 1.0,
                'seasonal_factor': 1.0,
                'weather_adjustments': {},
                'current_weather_impact': {},
                'forecast_impact': {},
            },
        })

    return fallback_results


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
            'change_percent': round(((final_price - current_price) / current_price) * 100, 1) if current_price > 0 else 0.0,
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
        if current_price > 0:
            change_percent = round(((final_price - current_price) / current_price) * 100, 1)
        else:
            change_percent = 0.0

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

# @login_required
# @account_type_required('admin', 'farmer', 'buyer')
def market_view(request):
    user = request.user
    if not user.is_authenticated:
        class MockUser:
            def __init__(self):
                self.account_type = 'buyer'
                self.id = None
                self.username = 'guest'
                self.is_authenticated = False
        user = MockUser()

    total_prices = MarketPrice.objects.count()

    # Filter by user type - farmers only see their own data, while buyers and
    # guests see the shared market summary.
    if user.account_type == 'admin':
        total_offers = BuyerOffer.objects.count() + SellerOffer.objects.count()
        pending_offers = BuyerOffer.objects.filter(status='Pending').count()
        offers = BuyerOffer.objects.filter(status='Pending').order_by('-date_offered')[:10]
    elif user.is_authenticated and user.account_type == 'farmer':
        # Farmers see only offers for their crops
        from crops.models import Crop
        user_crop_ids = Crop.objects.filter(user=user).values_list('id', flat=True)
        total_offers = BuyerOffer.objects.filter(farmer=user).count() + SellerOffer.objects.filter(farmer=user).count()
        pending_offers = BuyerOffer.objects.filter(farmer=user, status='Pending').count()
        offers = BuyerOffer.objects.filter(farmer=user, status='Pending').order_by('-date_offered')[:10]
    else:
        total_offers = BuyerOffer.objects.count() + SellerOffer.objects.count()
        pending_offers = BuyerOffer.objects.filter(status='Pending').count()
        offers = BuyerOffer.objects.filter(status='Pending').order_by('-date_offered')[:10]
    
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_prices = MarketPrice.objects.filter(date__gte=seven_days_ago)
    avg_price_7d = recent_prices.aggregate(avg=Avg('current_price'))['avg']
    
    market_prices = MarketPrice.objects.all().order_by('-last_updated')
    
    prices_paginator = Paginator(market_prices, 10)
    offers_paginator = Paginator(offers, 10)
    prices_page = prices_paginator.get_page(1)
    offers_page = offers_paginator.get_page(1)
    
    lang = request.session.get('lang', 'en')
    
    # Add ML predictions for immediate loading
    from ml_service.views import fetch_weather_data
    price_data = get_market_price_data()
    crops = [item['crop'] for item in price_data] if price_data else list(get_baseline_prices().keys())
    
    # Get weather data
    from ml_service.views import get_current_weather
    weather_info = get_current_weather()
    weather_data = {
        'temperature': weather_info.get('temperature', 28),
        'humidity': weather_info.get('humidity', 65),
        'precipitation': weather_info.get('precipitation', 0),
        'rainfall': weather_info.get('rainfall', 0)
    }

    import hashlib
    key_string = json.dumps({'crops': sorted(crops), 'weather': weather_data}, sort_keys=True)
    cache_key = f"market_predictions_{hashlib.md5(key_string.encode()).hexdigest()}"
    precomputed_predictions = cache.get(cache_key)

    if precomputed_predictions is None:
        precomputed_predictions = generate_ml_market_predictions(crops, weather_data)
        cache.set(cache_key, precomputed_predictions, 600)

    return render(request, 'market/market.html', {
        'total_prices': total_prices,
        'total_offers': total_offers,
        'pending_offers': pending_offers,
        'avg_price_7d': round(float(avg_price_7d or 0), 2),
        'prices_page': prices_page,
        'offers_page': offers_page,
        'lang': lang,
        'predictions_json': json.dumps(precomputed_predictions)
    })

@login_required
@account_type_required('admin', 'farmer', 'buyer')
def price_list(request):
    return market_prices_view(request)

@login_required
def price_add(request):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can add market prices.')
        return redirect('market:market')
    if request.method == 'POST':
        form = MarketPriceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Market price added successfully!')
            return redirect('market:market')
    form = MarketPriceForm()
    return render(request, 'market/market_price_form.html', {'form': form, 'action': 'Add'})

@login_required
def price_edit(request, price_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can edit market prices.')
        return redirect('market:market')
    price = get_object_or_404(MarketPrice, id=price_id)
    if request.method == 'POST':
        form = MarketPriceForm(request.POST, instance=price)
        if form.is_valid():
            form.save()
            messages.success(request, 'Market price updated successfully!')
            return redirect('market:market')
    form = MarketPriceForm(instance=price)
    return render(request, 'market/market_price_form.html', {'form': form, 'price': price, 'action': 'Edit'})

@login_required
def price_delete(request, price_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete market prices.')
        return redirect('market:market')
    price = get_object_or_404(MarketPrice, id=price_id)
    if request.method == 'POST':
        price.delete()
        messages.success(request, 'Market price deleted successfully!')
        return redirect('market:market')
    return render(request, 'market/market_price_confirm_delete.html', {'price': price})

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
        offers = SellerOffer.objects.select_related('farmer', 'crop').all().order_by('-date_posted')
    elif request.user.account_type == 'admin':
        offers = BuyerOffer.objects.select_related('crop', 'farmer').all().order_by('-date_offered')
    else:
        # Farmers only see buyer offers made on their own crops.
        offers = BuyerOffer.objects.select_related('crop', 'farmer').filter(
            crop__user=request.user
        ).order_by('-date_offered')
    
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
    return render(request, 'market/market_offer_list.html', {
        'offers': page_obj,
        'page_obj': page_obj,
        'query': query,
        'filters': filters,
        'lang': request.session.get('lang', 'en'),
    })

@login_required
def buyer_dashboard(request):
    if request.user.account_type != 'buyer':
        return redirect('market:market')
    
    # Get available crops from farmers
    from crops.models import Crop
    available_crops = Crop.objects.filter(status='available').order_by('-created_at')
    
    # Get seller offers (crops listed by farmers for sale)
    from .models import SellerOffer
    seller_offers = SellerOffer.objects.filter(status__in=['Pending', 'Available']).order_by('-date_posted')
    
    # Get buyer's submitted offers
    from .models import BuyerOffer
    my_offers = BuyerOffer.objects.filter(buyer_name=request.user.username).order_by('-date_offered')
    
    context = {
        'available_crops': available_crops,
        'seller_offers': seller_offers,
        'my_offers': my_offers,
        'lang': request.session.get('lang', 'en'),
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
            _log_buyer_offer_activity(
                request,
                offer,
                'create',
                f'{request.user.username} created a buyer offer for {offer.crop_name}',
                f'Buyer offer submitted for {offer.quantity} kg of {offer.crop_name} at PHP {offer.offer_price}.',
            )
            
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
    initial_data = {}
    crop_id = request.GET.get('crop')
    if crop_id:
        try:
            from crops.models import Crop
            crop = Crop.objects.get(id=crop_id)
            initial_data = {
                'crop': crop,
                'crop_name': crop.crop_name,
                'farmer': crop.user,
            }
        except Crop.DoesNotExist:
            pass
    form = BuyerOfferForm(initial=initial_data)
    return render(request, 'market/market_offer_form.html', {'form': form, 'action': 'Add'})

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
            offer = form.save()
            _log_buyer_offer_activity(
                request,
                offer,
                'update',
                f'{request.user.username} updated a buyer offer for {offer.crop_name}',
                f'Buyer offer updated to {offer.quantity} kg of {offer.crop_name} at PHP {offer.offer_price}.',
            )
            messages.success(request, 'Offer updated successfully!')
            return redirect('market:offer_list')
    else:
        form = BuyerOfferForm(instance=offer)
    return render(request, 'market/market_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def offer_delete(request, offer_id):
    if request.user.account_type in ['admin', 'farmer']:
        offer = get_object_or_404(BuyerOffer, id=offer_id)
    else:
        offer = get_object_or_404(BuyerOffer, id=offer_id, buyer_name=request.user.username)
    if request.method == 'POST':
        offer_id_value = offer.id
        crop_name = offer.crop_name
        quantity = offer.quantity
        offer_price = offer.offer_price
        offer.delete()
        try:
            from activity_log.utils import log_activity
            log_activity(
                request=request,
                user=request.user,
                event_type='delete',
                severity='info',
                status='success',
                action=f'{request.user.username} deleted a buyer offer for {crop_name}',
                description=f'Buyer offer for {quantity} kg of {crop_name} at PHP {offer_price} was deleted.',
                resource_type='market',
                resource_id=str(offer_id_value),
                resource_name=crop_name,
            )
        except Exception:
            pass
        messages.success(request, 'Offer deleted successfully!')
        return redirect('market:offer_list')
    return render(request, 'market/market_offer_confirm_delete.html', {'offer': offer})

@login_required
def offer_update_status(request, offer_id):
    """Premium: AJAX-friendly status update for offers."""
    if request.user.account_type not in ['admin', 'farmer']:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    if request.user.account_type == 'farmer':
        offer = get_object_or_404(BuyerOffer.objects.select_related('crop'), id=offer_id, crop__user=request.user)
    else:
        offer = get_object_or_404(BuyerOffer.objects.select_related('crop'), id=offer_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in [choice[0] for choice in BuyerOffer.STATUS_CHOICES]:
            offer.status = new_status
            offer.save()
            if offer.crop and new_status == 'Accepted':
                offer.crop.status = 'reserved'
                offer.crop.save(update_fields=['status'])
            elif offer.crop and new_status == 'Rejected' and offer.crop.status == 'reserved':
                has_other_accepted = BuyerOffer.objects.filter(crop=offer.crop, status='Accepted').exclude(id=offer.id).exists()
                if not has_other_accepted:
                    offer.crop.status = 'available'
                    offer.crop.save(update_fields=['status'])
            try:
                from activity_log.utils import log_activity
                log_activity(
                    request=request,
                    user=request.user,
                    event_type='update',
                    severity='info',
                    status='success',
                    action=f'{request.user.username} set buyer offer to {new_status}',
                    description=f'Buyer offer for {offer.crop_name} was updated to {new_status}.',
                    resource_type='market',
                    resource_id=str(offer.id),
                    resource_name=offer.crop_name,
                    visible_to_roles=['admin', 'farmer'],
                )
            except Exception:
                pass
            messages.success(request, f'Offer status updated to {new_status}')
            return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'error': 'Invalid request'}, status=400)

# @login_required
# @account_type_required('admin', 'secretary')
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
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Only admins and secretaries can add schedules.'}, status=403)
        messages.error(request, 'Only admins and secretaries can add schedules.')
        return redirect('market:schedule_list')
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Schedule added!'})
            messages.success(request, 'Schedule added!')
            return redirect('market:schedule_list')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': form.errors}, status=400)
    form = ScheduleDistributionForm()
    return render(request, 'market/schedule_form.html', {'form': form, 'action': 'Add'})

@login_required
def schedule_edit(request, schedule_id):
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    if request.user.account_type not in ['admin', 'secretary']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Only admins and secretaries can edit schedules.'}, status=403)
        messages.error(request, 'Only admins and secretaries can edit schedules.')
        return redirect('market:schedule_list')
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Schedule updated!'})
            messages.success(request, 'Schedule updated!')
            return redirect('market:schedule_list')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': form.errors}, status=400)
    form = ScheduleDistributionForm(instance=schedule)
    return render(request, 'market/schedule_form.html', {'form': form, 'schedule': schedule, 'action': 'Edit'})

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
    return render(request, 'market/schedule_confirm_delete.html', {'schedule': schedule})

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
    return render(request, 'market/sell_offer_list.html', {'offers': page_obj, 'query': query})

@login_required
def seller_offer_add(request):
    if request.user.account_type != 'farmer':
        messages.error(request, 'Only farmers can post sell offers.')
        return redirect('market:seller_offer_list')
    if request.method == 'POST':
        form = _build_seller_offer_form(request.user, request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.farmer = request.user
            offer.save()
            messages.success(request, 'Sell offer posted!')
            return redirect('market:seller_offer_list')
    else:
        form = _build_seller_offer_form(request.user)
    return render(request, 'market/sell_offer_form.html', {'form': form, 'action': 'Add'})

@login_required
def seller_offer_edit(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id, farmer=request.user)
    if request.method == 'POST':
        form = _build_seller_offer_form(request.user, request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sell offer updated!')
            return redirect('market:seller_offer_list')
    else:
        form = _build_seller_offer_form(request.user, instance=offer)
    return render(request, 'market/sell_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def seller_offer_delete(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id, farmer=request.user)
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Sell offer deleted!')
        return redirect('market:seller_offer_list')
    return render(request, 'market/sell_offer_confirm_delete.html', {'offer': offer})

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
        if request.user.account_type != 'buyer':
            messages.error(request, 'Only buyers can submit offers for seller listings.')
            return redirect('market:seller_offer_detail', offer_id=offer.id)

        post_data = request.POST.copy()
        post_data['crop_name'] = offer.crop.crop_name
        post_data['crop'] = offer.crop_id
        post_data['farmer'] = offer.farmer_id
        form = BuyerOfferForm(post_data)
        if form.is_valid():
            buyer_offer = form.save(commit=False)
            buyer_offer.buyer_name = request.user.username
            buyer_offer.crop = offer.crop
            buyer_offer.farmer = offer.farmer
            buyer_offer.crop_name = offer.crop.crop_name
            buyer_offer.quantity = form.cleaned_data.get('quantity', offer.quantity)
            buyer_offer.save()
            _log_buyer_offer_activity(
                request,
                buyer_offer,
                'create',
                f'{request.user.username} created a buyer offer for {buyer_offer.crop_name}',
                f'Buyer offer submitted for {buyer_offer.quantity} kg of {buyer_offer.crop_name} at PHP {buyer_offer.offer_price}.',
            )
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
    
    return render(request, 'market/seller_offer_detail.html', {
        'seller_offer': offer,
        'form': form,
        'existing_offers': existing_offers
    })
