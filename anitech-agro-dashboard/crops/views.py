from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from .models import Crop
from .forms import CropForm
from anitech.views import account_type_required
from anitech.utils import get_crop_name
from activity_log.utils import log_activity
from notifications.services import create_notification, notify_admins, notify_admins_once

EXCLUDED_MARKET_CROPS = {'audit crop', 'audit crop2'}


def _is_excluded_market_crop(crop_name):
    return str(crop_name or '').strip().lower() in EXCLUDED_MARKET_CROPS


def _clear_available_crops_cache():
    """Clear all available crops cache keys"""
    cache.delete('dashboard_available_crops')
    cache.delete('buyer_available_crops')
    # Clear all sort and search variations
    for sort in ['newest', 'oldest', 'price-high', 'price-low', 'name-asc', 'name-desc']:
        cache.delete(f'available_crops_sorted_{sort}')
        cache.delete(f'available_crops_sorted_{sort}_search_')


def _notify_admins_about_top_recommendation(predictions, season):
    if not predictions:
        return

    top_prediction = predictions[0]
    snapshot = {
        'crop': top_prediction.get('crop'),
        'season': season,
        'suitability_percent': top_prediction.get('suitability_percent'),
        'price': top_prediction.get('price'),
    }
    price_suffix = (
        f" with an estimated price of PHP {top_prediction.get('price')}/kg"
        if top_prediction.get('price') not in [None, '']
        else ''
    )
    notify_admins_once(
        'admin_notification_top_crop_recommendation',
        snapshot,
        'Top crop recommendation updated',
        (
            f"{top_prediction.get('crop')} is now the top recommendation for the "
            f"{season} season at {top_prediction.get('suitability_percent')}% suitability"
            f"{price_suffix}."
        ),
        notif_type='info',
        timeout=3600,
    )

# Crop name translations (matching old PHP system)
CROP_TRANSLATIONS = {
    'Rice': {'en': 'Rice', 'tl': 'Palay'},
    'Corn': {'en': 'Corn', 'tl': 'Mais'},
    'Eggplant': {'en': 'Eggplant', 'tl': 'Talong'},
    'Bitter Gourd': {'en': 'Bitter Gourd', 'tl': 'Ampalaya'},
    'Tomato': {'en': 'Tomato', 'tl': 'Kamatis'},
    'Sweet Potato': {'en': 'Sweet Potato', 'tl': 'Kamote'},
    'Okra': {'en': 'Lady Fingers', 'tl': 'Okra'},
    'Peanut': {'en': 'Peanut', 'tl': 'Mani'},
    'Melon': {'en': 'Melon', 'tl': 'Melon'},
    'Watermelon': {'en': 'Watermelon', 'tl': 'Pakwan'},
    'Cucumber': {'en': 'Cucumber', 'tl': 'Pipino'},
    'Carrot': {'en': 'Carrot', 'tl': 'Karot'},
    'Chili': {'en': 'Chili', 'tl': 'Siling Labuyo'},
    'Potato': {'en': 'Potato', 'tl': 'Patatas'},
    'Cabbage': {'en': 'Cabbage', 'tl': 'Repolyo'},
    'Onion': {'en': 'Onion', 'tl': 'Sibuyas'},
    'Garlic': {'en': 'Garlic', 'tl': 'Bawang'},
    'Squash': {'en': 'Squash', 'tl': 'Kalabasa'},
    'Beans': {'en': 'String Beans', 'tl': 'Sitaw'},
}

CROP_UI_METADATA = {
    'Rice': {'harvest_days': 115, 'optimal_months': 2},
    'Corn': {'harvest_days': 110, 'optimal_months': 1},
    'Onion': {'harvest_days': 100, 'optimal_months': 7},
    'Garlic': {'harvest_days': 120, 'optimal_months': 6},
    'Tomato': {'harvest_days': 75, 'optimal_months': 6},
    'Eggplant': {'harvest_days': 80, 'optimal_months': 5},
    'Cabbage': {'harvest_days': 90, 'optimal_months': 4},
    'Chili': {'harvest_days': 85, 'optimal_months': 3},
    'Sweet Potato': {'harvest_days': 105, 'optimal_months': 4},
    'Peanut': {'harvest_days': 95, 'optimal_months': 3},
    'Cassava': {'harvest_days': 240, 'optimal_months': 8},
    'Bean': {'harvest_days': 65, 'optimal_months': 2},
    'Beans': {'harvest_days': 65, 'optimal_months': 2},
}

CROP_NAME_ALIASES = {
    'Bean': 'Beans',
    'String Bean': 'Beans',
    'String Beans': 'Beans',
    'Sitaw': 'Beans',
    'Sitao': 'Beans',
    'Pole Sitao': 'Beans',
    'Eggplants': 'Eggplant',
    'Bitter Gourd': 'Bitter Gourd',
    'Ampalaya': 'Bitter Gourd',
    'Lady Fingers': 'Okra',
    'Chinese Cabbage': 'Cabbage',
    'Pechay': 'Cabbage',
}

SEASONAL_CROP_PROFILES = {
    'Rice': {
        'preferred_seasons': {'Wet'},
        'temperature_range': (24, 31),
        'rainfall_range': (90, 260),
        'humidity_range': (72, 95),
    },
    'Corn': {
        'preferred_seasons': {'Wet'},
        'temperature_range': (23, 30),
        'rainfall_range': (70, 200),
        'humidity_range': (65, 88),
    },
    'Onion': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (18, 29),
        'rainfall_range': (0, 70),
        'humidity_range': (45, 78),
    },
    'Garlic': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (17, 28),
        'rainfall_range': (0, 60),
        'humidity_range': (45, 76),
    },
    'Tomato': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (20, 30),
        'rainfall_range': (0, 90),
        'humidity_range': (50, 82),
    },
    'Eggplant': {
        'preferred_seasons': {'Dry', 'Wet'},
        'temperature_range': (22, 31),
        'rainfall_range': (20, 180),
        'humidity_range': (55, 88),
    },
    'Cabbage': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (16, 27),
        'rainfall_range': (0, 120),
        'humidity_range': (55, 84),
    },
    'Chili': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (21, 31),
        'rainfall_range': (0, 100),
        'humidity_range': (50, 82),
    },
    'Sweet Potato': {
        'preferred_seasons': {'Dry', 'Wet'},
        'temperature_range': (23, 32),
        'rainfall_range': (20, 170),
        'humidity_range': (55, 88),
    },
    'Peanut': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (24, 33),
        'rainfall_range': (0, 90),
        'humidity_range': (45, 78),
    },
    'Cassava': {
        'preferred_seasons': {'Dry', 'Wet'},
        'temperature_range': (23, 33),
        'rainfall_range': (20, 180),
        'humidity_range': (50, 88),
    },
    'Bean': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (20, 30),
        'rainfall_range': (0, 120),
        'humidity_range': (50, 82),
    },
    'Beans': {
        'preferred_seasons': {'Dry'},
        'temperature_range': (21, 31),
        'rainfall_range': (0, 130),
        'humidity_range': (50, 84),
    },
}

HIGH_DEMAND_CROPS = {
    'Rice', 'Onion', 'Garlic', 'Tomato', 'Eggplant', 'Cabbage', 'Beans'
}

RECOMMENDATION_CACHE_VERSION = 'v2'

def get_translated_crop_name(crop_name, lang='en'):
    """Get translated crop name based on language"""
    return get_crop_name(crop_name, lang)


def _normalize_crop_key(crop_name):
    if not crop_name:
        return crop_name
    return CROP_NAME_ALIASES.get(crop_name, crop_name)


def _display_crop_name(crop_name):
    normalized_name = get_crop_name(crop_name, 'en')
    if normalized_name == 'Beans':
        return 'String Beans'
    return normalized_name


def _get_market_price_snapshot():
    from market.models import MarketPrice

    snapshot = {}
    for market_price in MarketPrice.objects.order_by('-last_updated', '-id'):
        if _is_excluded_market_crop(market_price.crop_name):
            continue
        normalized_name = _normalize_crop_key(market_price.crop_name)
        if not normalized_name or normalized_name in snapshot:
            continue

        snapshot[normalized_name] = {
            'crop': normalized_name,
            'price': float(market_price.current_price or 0),
            'trend_percent': float(market_price.trend_percent or 0),
        }

    return snapshot


def _build_market_signature(market_snapshot):
    if not market_snapshot:
        return 'no-market-prices'

    total_price = round(sum(item.get('price', 0) for item in market_snapshot.values()), 2)
    total_trend = round(sum(item.get('trend_percent', 0) for item in market_snapshot.values()), 2)
    return f"{len(market_snapshot)}_{total_price}_{total_trend}"


def _get_recommendation_crop_pool():
    """
    Use market price crops as the canonical recommendation pool so the crop
    recommendations page stays consistent with the market prices page.
    """
    market_snapshot = _get_market_price_snapshot()
    if market_snapshot:
        return sorted(market_snapshot)

    crop_pool = {
        normalized_name
        for normalized_name in (
            _normalize_crop_key(crop_name)
            for crop_name in (set(CROP_UI_METADATA) | set(SEASONAL_CROP_PROFILES) | HIGH_DEMAND_CROPS)
        )
        if normalized_name
    }

    db_crop_names = Crop.objects.values_list('crop_name', flat=True).distinct()
    for crop_name in db_crop_names:
        normalized_name = _normalize_crop_key(crop_name)
        if normalized_name:
            crop_pool.add(normalized_name)

    return sorted(crop_pool)


def _score_range(value, lower, upper, tolerance):
    if lower <= value <= upper:
        return 1.0
    if value < lower:
        return max(0.0, 1 - ((lower - value) / tolerance))
    return max(0.0, 1 - ((value - upper) / tolerance))


def _derive_season_from_weather(weather):
    current_month = timezone.now().month
    month_season = 'Wet' if 6 <= current_month <= 11 else 'Dry'

    rainfall = float(weather.get('rainfall', 0) or 0)
    precipitation = float(weather.get('precipitation', 0) or 0)
    humidity = float(weather.get('humidity', 0) or 0)

    wet_signals = 0
    if rainfall >= 8:
        wet_signals += 2
    elif rainfall >= 3:
        wet_signals += 1
    if precipitation >= 1:
        wet_signals += 1
    if humidity >= 86:
        wet_signals += 1
    if month_season == 'Wet':
        wet_signals += 1

    return 'Wet' if wet_signals >= 2 else 'Dry'


def _calculate_weather_fit(crop_name, weather, season):
    profile = SEASONAL_CROP_PROFILES.get(_normalize_crop_key(crop_name))
    if not profile:
        return 0.5

    temperature = float(weather.get('temperature', 28) or 28)
    rainfall = float(weather.get('rainfall', 0) or 0)
    humidity = float(weather.get('humidity', 80) or 80)

    temp_score = _score_range(temperature, *profile['temperature_range'], tolerance=8)
    rain_score = _score_range(rainfall, *profile['rainfall_range'], tolerance=80)
    humidity_score = _score_range(humidity, *profile['humidity_range'], tolerance=18)

    weather_score = (temp_score * 0.45) + (rain_score * 0.35) + (humidity_score * 0.20)
    season_bonus = 1.0 if season in profile['preferred_seasons'] else 0.55
    return max(0.0, min(1.0, weather_score * season_bonus))


def _build_market_demand_index(crop_names, prediction_dict, market_snapshot):
    crop_names = [crop_name for crop_name in crop_names if crop_name]
    if not crop_names:
        return {}, set()

    max_market_price = max(
        (market_snapshot.get(crop_name, {}).get('price', 0) for crop_name in crop_names),
        default=0,
    )

    demand_score_by_crop = {}
    for crop_name in crop_names:
        market_data = market_snapshot.get(crop_name, {})
        ml_score = float(prediction_dict.get(crop_name, {}).get('score', 0) or 0)
        price_component = (
            float(market_data.get('price', 0) or 0) / max_market_price
            if max_market_price > 0
            else 0
        )
        trend_component = min(max(float(market_data.get('trend_percent', 0) or 0), 0.0), 25.0) / 25.0
        base_component = 0.2 if crop_name in HIGH_DEMAND_CROPS else 0.0

        demand_score_by_crop[crop_name] = max(
            0.0,
            min(1.0, (price_component * 0.5) + (trend_component * 0.2) + (ml_score * 0.2) + base_component),
        )

    ranked_crops = sorted(
        demand_score_by_crop.items(),
        key=lambda item: (-item[1], item[0]),
    )
    leader_count = min(len(ranked_crops), max(1, (len(ranked_crops) + 1) // 3))
    demand_leaders = {crop_name for crop_name, _ in ranked_crops[:leader_count]}
    return demand_score_by_crop, demand_leaders


def _build_recommendation_cards(ml_predictions, season, weather, market_snapshot=None):
    prediction_dict = {}
    for prediction in ml_predictions:
        normalized_name = _normalize_crop_key(prediction.get('crop'))
        if not normalized_name:
            continue
        current = prediction_dict.get(normalized_name)
        if current is None or float(prediction.get('score', 0) or 0) > float(current.get('score', 0) or 0):
            prediction_dict[normalized_name] = prediction

    candidate_crops = sorted(market_snapshot) if market_snapshot else sorted(prediction_dict)
    demand_score_by_crop, demand_leaders = _build_market_demand_index(
        candidate_crops,
        prediction_dict,
        market_snapshot or {},
    )

    cards = []
    for canonical_name in candidate_crops:
        ml_prediction = prediction_dict.get(canonical_name, {})
        metadata = CROP_UI_METADATA.get(canonical_name, {})
        ml_score = float(ml_prediction.get('score', 0) or 0)
        weather_fit = _calculate_weather_fit(canonical_name, weather, season)
        preferred_seasons = SEASONAL_CROP_PROFILES.get(canonical_name, {}).get('preferred_seasons', set())
        demand_score = demand_score_by_crop.get(canonical_name, 0.0)
        market_data = (market_snapshot or {}).get(canonical_name, {})

        # Blend ML confidence with live Open-Meteo conditions so the seasonal
        # cards reflect the current season while demand cards stay grounded in
        # current market prices.
        final_score = max(0.0, min(1.0, (ml_score * 0.6) + (weather_fit * 0.25) + (demand_score * 0.15)))
        suitability_percent = round(final_score * 100)

        ml_category = ml_prediction.get('category')
        is_current_season_fit = (
            season in preferred_seasons and weather_fit >= 0.55
            if preferred_seasons
            else ml_category == 'seasonal' and final_score >= 0.6
        )
        is_high_demand = canonical_name in demand_leaders or demand_score >= 0.55
        category = 'seasonal' if is_current_season_fit else 'high-demand'

        cards.append({
            'crop_key': canonical_name,
            'crop': _display_crop_name(canonical_name),
            'score': round(final_score, 4),
            'suitability_percent': suitability_percent,
            'harvest_days': metadata.get('harvest_days', 90),
            'optimal_months': metadata.get(
                'optimal_months',
                2 if suitability_percent >= 70 else 3 if suitability_percent >= 55 else 5
            ),
            'season_label': (
                f'Recommended for the current {season.lower()} season'
                if is_current_season_fit
                else f'Monitor during the current {season.lower()} season'
            ),
            'plant_now': is_current_season_fit or final_score >= 0.65,
            'category': category,
            'price': market_data.get('price') or ml_prediction.get('price'),
            'predicted_price': ml_prediction.get('price'),
            'trend_percent': round(float(market_data.get('trend_percent', 0) or 0), 2),
            'demand_percent': round(demand_score * 100),
            'weather_fit': round(weather_fit, 4),
            'current_season_fit': is_current_season_fit,
            'high_demand_fit': is_high_demand,
        })

    seasonal_cards = [
        card for card in cards if card['current_season_fit']
    ]
    high_demand_cards = [
        card for card in cards if card['high_demand_fit'] and not card['current_season_fit']
    ]

    if not seasonal_cards and cards:
        fallback_seasonal_cards = sorted(
            cards,
            key=lambda item: (-item['weather_fit'], -item['suitability_percent'], item['crop']),
        )[:max(2, min(3, len(cards)))]

        for card in fallback_seasonal_cards:
            card['current_season_fit'] = True
            card['category'] = 'seasonal'
            card['season_label'] = f'Recommended for the current {season.lower()} season'
            card['plant_now'] = True

        seasonal_cards = fallback_seasonal_cards

    if not high_demand_cards and cards:
        non_seasonal_cards = [card for card in cards if not card['current_season_fit']]
        high_demand_cards = sorted(
            non_seasonal_cards,
            key=lambda item: (-item['demand_percent'], -item['suitability_percent'], item['crop']),
        )[:max(1, min(3, len(non_seasonal_cards)))]

    selected_cards = {
        card['crop_key']: card
        for card in seasonal_cards + high_demand_cards
    }

    minimum_card_count = min(len(cards), 6)
    if len(selected_cards) < minimum_card_count:
        ranked_cards = sorted(
            cards,
            key=lambda item: (-item['suitability_percent'], -item['demand_percent'], item['crop']),
        )
        for card in ranked_cards:
            if card['crop_key'] in selected_cards:
                continue
            selected_cards[card['crop_key']] = card
            if len(selected_cards) >= minimum_card_count:
                break

    curated_cards = list(selected_cards.values())
    curated_cards.sort(
        key=lambda item: (
            item['category'] != 'seasonal',
            -item['suitability_percent'],
            -item['demand_percent'],
            item['harvest_days'],
            item['crop'],
        )
    )
    return curated_cards


def _build_crop_prediction_payload(season=None):
    from ml_service.views import get_current_weather
    from django.core.cache import cache

    weather = get_current_weather()
    inferred_season = season or _derive_season_from_weather(weather)
    market_snapshot = _get_market_price_snapshot()
    market_signature = _build_market_signature(market_snapshot)
    crop_names = _get_recommendation_crop_pool()
    cache_key = (
        f"crop_prediction_payload_{inferred_season}_"
        f"{round(float(weather.get('temperature', 28) or 28), 1)}_"
        f"{round(float(weather.get('humidity', 80) or 80), 1)}_"
        f"{round(float(weather.get('rainfall', 0) or 0), 1)}_"
        f"{len(crop_names)}_{market_signature}"
    )
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    humidity = weather.get('humidity', 80)
    temperature = weather.get('temperature', 28)
    # Use actual rainfall from daily API data (live)
    rainfall = weather.get('rainfall', 0)
    if rainfall == 0:
        # Fallback: derive from precipitation if rainfall not available
        precipitation = weather.get('precipitation', 0)
        rainfall = max(40, int(precipitation * 25))

    # Ensure reasonable bounds
    rainfall = max(0, min(500, rainfall))

    # Keep crop/weather ML predictions anchored to Legazpi City, Albay.
    # The pricing model maps this to the Bicol training region internally.
    location = 'Legazpi City'

    result = ({
        'ph': 6.5,  # Soil pH - would need soil sensors for true live data
        'rainfall': rainfall,
        'temperature': temperature,
        'humidity': humidity,
        'location': location,
        'season': inferred_season,
        'crops': crop_names,
        'market_prices': {
            crop_name: {
                'current_price': market_data.get('price', 0),
                'trend_percent': market_data.get('trend_percent', 0),
            }
            for crop_name, market_data in market_snapshot.items()
        },
        'k': len(crop_names) or 8,
    }, weather, market_snapshot)

    cache.set(cache_key, result, 600)  # Cache for 10 minutes

    return result


def _enrich_predictions(predictions, season):
    enriched = []
    for prediction in predictions:
        crop_name = prediction.get('crop', '')
        metadata = CROP_UI_METADATA.get(crop_name, {})
        optimal_months = metadata.get('optimal_months', 3)

        card = dict(prediction)
        card['harvest_days'] = metadata.get('harvest_days', 90)
        card['optimal_months'] = optimal_months
        card['season_label'] = f'{season} Season'
        card['suitability_percent'] = round(float(prediction.get('score', 0)) * 100)
        card['plant_now'] = card['suitability_percent'] >= 55 or optimal_months <= 2
        enriched.append(card)
    return enriched

# @login_required
# @account_type_required('admin', 'farmer', 'buyer')
def crop_recommendations(request):
    """ML-powered crop recommendations page"""
    lang = request.session.get('lang', 'en')
    payload, weather, market_snapshot = _build_crop_prediction_payload()
    season = payload['season']
    market_signature = _build_market_signature(market_snapshot)

    cache_key = (
        f"crop_recommendations_{RECOMMENDATION_CACHE_VERSION}_{season}_{lang}_"
        f"{round(float(weather.get('temperature', 28) or 28), 1)}_"
        f"{round(float(weather.get('humidity', 80) or 80), 1)}_"
        f"{round(float(weather.get('rainfall', 0) or 0), 1)}_"
        f"{market_signature}"
    )
    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'crops.html', cached_data)

    try:
        from ml_service.views import generate_crop_prediction_result

        prediction_result = generate_crop_prediction_result(payload)
        ml_predictions = prediction_result.get('predictions', [])
    except Exception as e:
        print(f"Crop recommendations error: {e}")
        prediction_result = {'source': 'error', 'predictions': []}
        ml_predictions = []

    predictions = _build_recommendation_cards(ml_predictions, season, weather, market_snapshot)
    _notify_admins_about_top_recommendation(predictions, season)

    context = {
        'lang': lang,
        'season': season,
        'current_season': season,
        'predictions': predictions,
        'prediction_source': prediction_result.get('source', 'unknown'),
        'prediction_fallback': prediction_result.get('fallback', False),
        'weather_snapshot': {
            'temperature': weather.get('temperature', 28),
            'humidity': weather.get('humidity', 80),
            'rainfall': weather.get('rainfall', 0),  # Live daily rainfall from Open-Meteo API
        },
    }

    # Cache for 10 minutes
    cache.set(cache_key, context, 600)

    return render(request, 'crops.html', context)

@account_type_required('admin', 'farmer')
def crops_list(request):
    """List all crops with filtering and sorting"""
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', 'newest')
    lang = request.session.get('lang', 'en')
    
    # Base queryset - show user's crops for non-admin, all for admin
    if request.user.account_type == 'admin':
        crops = Crop.objects.all().select_related('user')
    else:
        crops = Crop.objects.filter(user=request.user)
    
    # Apply status filter
    if status_filter:
        crops = crops.filter(status=status_filter)
    
    # Apply sorting
    if sort_by == 'newest':
        crops = crops.order_by('-created_at')
    elif sort_by == 'oldest':
        crops = crops.order_by('created_at')
    elif sort_by == 'price-high':
        crops = crops.order_by('-price')
    elif sort_by == 'price-low':
        crops = crops.order_by('price')
    
    # Pagination
    paginator = Paginator(crops, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get current season for crop prediction
    from datetime import datetime
    month = datetime.now().month
    is_wet = (month >= 6 and month <= 11)
    season = "Wet" if is_wet else "Dry"
    
    return render(request, 'crops.html', {
        'crops': page_obj,
        'status_filter': status_filter,
        'sort_by': sort_by,
        'season': season,
        'lang': lang,
    })

@login_required
@account_type_required('admin', 'farmer')
def crop_add(request):
    """Add a new crop"""
    if request.method == 'POST':
        # Simplified crop addition for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from decimal import Decimal
            crop_name = request.POST.get('crop_name')
            grade = request.POST.get('grade')
            price_str = request.POST.get('price')
            quantity_str = request.POST.get('quantity')

            if not all([crop_name, price_str, quantity_str]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields: crop_name, price, quantity'
                }, status=400)

            try:
                price = Decimal(price_str)
                quantity = Decimal(quantity_str)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid price or quantity format'
                }, status=400)

            try:
                crop = Crop.objects.create(
                    user=request.user,
                    crop_name=crop_name,
                    grade=grade or None,
                    price=price,
                    quantity=quantity,
                    status='available'
                )
                # Clear available crops cache when new crop is added
                _clear_available_crops_cache()
                log_activity(
                    request=request,
                    user=request.user,
                    event_type='create',
                    severity='info',
                    status='success',
                    action=f'Added crop: {crop.crop_name}',
                    description=f'{request.user.username} added {crop.quantity} {crop.unit} of {crop.crop_name}.',
                    resource_type='crop',
                    resource_id=str(crop.id),
                    resource_name=crop.crop_name,
                )
                notify_admins(
                    'New crop added',
                    (
                        f"{request.user.username} added {crop.quantity} {crop.unit} of "
                        f"{crop.crop_name} at PHP {crop.price}."
                    ),
                    notif_type='info',
                )
                
                return JsonResponse({
                    'success': True,
                    'id': crop.id,
                    'crop_name': crop.crop_name,
                    'message': f'Crop "{crop.crop_name}" added successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
        else:
            # For non-AJAX requests, use the full form
            form = CropForm(request.POST, request.FILES)
            if form.is_valid():
                crop = form.save(commit=False)
                crop.user = request.user
                crop.save()
                # Clear available crops cache when new crop is added
                _clear_available_crops_cache()
                log_activity(
                    request=request,
                    user=request.user,
                    event_type='create',
                    severity='info',
                    status='success',
                    action=f'Added crop: {crop.crop_name}',
                    description=f'{request.user.username} added {crop.quantity} {crop.unit} of {crop.crop_name}.',
                    resource_type='crop',
                    resource_id=str(crop.id),
                    resource_name=crop.crop_name,
                )
                notify_admins(
                    'New crop added',
                    (
                        f"{request.user.username} added {crop.quantity} {crop.unit} of "
                        f"{crop.crop_name} at PHP {crop.price}."
                    ),
                    notif_type='info',
                )
                
                messages.success(request, f'Crop "{crop.crop_name}" added successfully!')
                return redirect('crops')
            else:
                # Form is invalid
                pass
    else:
        form = CropForm()
    
    return render(request, 'crop_form.html', {
        'form': form,
        'action': 'Add'
    })

@login_required
@account_type_required('admin', 'farmer')
def crop_edit(request, crop_id):
    """Edit an existing crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check permission (admin or owner)
    if request.user.account_type != 'admin' and crop.user != request.user:
        messages.error(request, 'You do not have permission to edit this crop.')
        return redirect('crops')
    
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            # Clear available crops cache when crop is edited
            _clear_available_crops_cache()
            log_activity(
                request=request,
                user=request.user,
                event_type='update',
                severity='info',
                status='success',
                action=f'Updated crop: {crop.crop_name}',
                description=f'{request.user.username} updated crop details for {crop.crop_name}.',
                resource_type='crop',
                resource_id=str(crop.id),
                resource_name=crop.crop_name,
            )
            messages.success(request, f'Crop "{crop.crop_name}" updated successfully!')
            return redirect('crops')
    else:
        form = CropForm(instance=crop)
    
    return render(request, 'crop_form.html', {
        'form': form,
        'crop': crop,
        'action': 'Edit'
    })

@login_required
@account_type_required('admin', 'farmer')
def crop_delete(request, crop_id):
    """Delete a crop"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check permission (admin or owner)
    if request.user.account_type != 'admin' and crop.user != request.user:
        messages.error(request, 'You do not have permission to delete this crop.')
        return redirect('crops')
    
    if request.method == 'POST':
        crop_name = crop.crop_name
        crop_id_value = crop.id
        crop.delete()
        # Clear available crops cache when crop is deleted
        _clear_available_crops_cache()
        log_activity(
            request=request,
            user=request.user,
            event_type='delete',
            severity='info',
            status='success',
            action=f'Deleted crop: {crop_name}',
            description=f'{request.user.username} deleted crop listing for {crop_name}.',
            resource_type='crop',
            resource_id=str(crop_id_value),
            resource_name=crop_name,
        )
        messages.success(request, f'Crop "{crop_name}" deleted successfully!')
        return redirect('crops')
    
    return render(request, 'crop_confirm_delete.html', {'crop': crop})

@login_required
def crop_view(request, crop_id):
    """View crop details"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Import BuyerOfferForm for buyers to make offers
    from market.forms import BuyerOfferForm
    offer_form = BuyerOfferForm()
    
    return render(request, 'crop_detail.html', {
        'crop': crop,
        'offer_form': offer_form,
    })


# @login_required
# @account_type_required('admin', 'farmer', 'buyer')
def available_crops(request):
    """List all available crops for buyers - farmers see only their own crops"""
    user = request.user
    if not user.is_authenticated:
        class MockUser:
            def __init__(self):
                self.account_type = 'buyer'
                self.id = None
                self.username = 'guest'
        user = MockUser()

    # Get filter and sort parameters
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    lang = request.session.get('lang', 'en')

    # Farmers should only see their own crops in available crops
    if user.account_type == 'farmer':
        crops = Crop.objects.filter(status='available', user=user)
    elif user.account_type == 'admin':
        # Admins see all available crops
        crops = Crop.objects.filter(status='available')
    else:
        # Buyers see all available crops (marketplace)
        crops = Crop.objects.filter(status='available')

    # Only show available crops - use cache for faster loading (only for buyers)
    if search_query:
        crops = crops.filter(
            Q(crop_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if sort_by == 'newest':
        crops = crops.order_by('-created_at')
    elif sort_by == 'oldest':
        crops = crops.order_by('created_at')
    elif sort_by == 'price-high':
        crops = crops.order_by('-price')
    elif sort_by == 'price-low':
        crops = crops.order_by('price')
    elif sort_by in ['name Asc', 'name-asc']:
        sort_by = 'name-asc'
        crops = crops.order_by('crop_name')
    elif sort_by == 'name-desc':
        crops = crops.order_by('-crop_name')

    if user.account_type == 'buyer':
        cache_key = f'available_crops_sorted_{sort_by}_search_{search_query.lower().strip()}'
        cached_crop_ids = cache.get(cache_key)
        if cached_crop_ids is None:
            cached_crop_ids = list(crops.values_list('id', flat=True))
            cache.set(cache_key, cached_crop_ids, 300)
        crops = Crop.objects.filter(id__in=cached_crop_ids).select_related('user')
        if sort_by == 'newest':
            crops = crops.order_by('-created_at')
        elif sort_by == 'oldest':
            crops = crops.order_by('created_at')
        elif sort_by == 'price-high':
            crops = crops.order_by('-price')
        elif sort_by == 'price-low':
            crops = crops.order_by('price')
        elif sort_by == 'name-asc':
            crops = crops.order_by('crop_name')
        elif sort_by == 'name-desc':
            crops = crops.order_by('-crop_name')
    else:
        crops = crops.select_related('user')
    
    # Add translated crop names and ML predictions
    for crop in crops:
        crop.translated_name = get_crop_name(crop.crop_name, lang)
        
        # Add ML market price prediction
        try:
            from ml_service.market_price_predictor import predict_market_price
            location = 'Legazpi City'
            season = crop.season or ('wet' if 6 <= datetime.now().month <= 11 else 'dry')
            
            prediction = predict_market_price(
                crop.crop_name, 
                location, 
                season=season
            )
            crop.ml_predicted_price = prediction['predicted_price_php']
            crop.price_trend = prediction['price_shock_pct']
        except Exception:
            # Fallback if ML prediction fails
            crop.ml_predicted_price = None
            crop.price_trend = 0
    
    # Pagination
    paginator = Paginator(crops, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'available_crops.html', {
        'crops': page_obj,
        'sort_by': sort_by,
        'lang': lang,
    })

@login_required
def crop_purchase(request, crop_id):
    """Direct purchase crop (full quantity) for buyers"""
    if request.user.account_type != 'buyer':
        messages.error(request, 'Only buyers can purchase crops.')
        return redirect('crops:available_crops')
    
    crop = get_object_or_404(Crop, id=crop_id, status='available')
    
    if request.method == 'POST':
        # Full quantity purchase
        crop.status = 'sold'
        crop.save()
        # Clear available crops cache when crop is purchased
        _clear_available_crops_cache()
        log_activity(
            request=request,
            user=request.user,
            event_type='update',
            severity='info',
            status='success',
            action=f'Purchased crop: {crop.crop_name}',
            description=f'{request.user.username} purchased {crop.crop_name} from {crop.user.username}.',
            resource_type='crop',
            resource_id=str(crop.id),
            resource_name=crop.crop_name,
        )
        messages.success(request, f'Purchased {crop.crop_name} ({crop.quantity}kg) for ₱{crop.price}!')
        # Create notification to farmer
        try:
            create_notification(
                crop.user,
                'success',
                f'Crop Sold: {crop.crop_name}',
                f'Your {crop.crop_name} has been purchased by {request.user.username}.'
            )
        except:
            pass
        notify_admins(
            'Crop purchased',
            (
                f"{request.user.username} bought {crop.quantity}kg of {crop.crop_name} "
                f"from {crop.user.username} for PHP {crop.price}."
            ),
            notif_type='success',
        )
        return redirect('crops:available_crops')
    
    return render(request, 'crop_detail.html', {'crop': crop, 'buy_mode': True})


@login_required
def get_crop_data(request, crop_id):
    """API endpoint to get crop data for edit popup"""
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check permission
    if request.user.account_type != 'admin' and crop.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    from django.utils import timezone
    
    data = {
        'id': crop.id,
        'crop_name': crop.crop_name,
        'grade': crop.grade,
        'status': crop.status,
        'price': str(crop.price),
        'quantity': crop.quantity,
        'wholesale_price': str(crop.wholesale_price) if crop.wholesale_price else '',
        'retail_price': str(crop.retail_price) if crop.retail_price else '',
        'harvest_date': crop.harvest_date.isoformat() if crop.harvest_date else '',
        'available_until': crop.available_until.isoformat() if crop.available_until else '',
        'description': crop.description or '',
        'image': crop.image.url if crop.image else None,
    }
    
    return JsonResponse(data)


@login_required
def update_crop_ajax(request, crop_id):
    """API endpoint to update crop via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check permission
    if request.user.account_type != 'admin' and crop.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Handle both JSON and multipart form data
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle multipart form data with file upload
        crop.crop_name = request.POST.get('crop_name', crop.crop_name)
        crop.grade = request.POST.get('grade', crop.grade)
        crop.status = request.POST.get('status', crop.status)
        crop.price = request.POST.get('price', crop.price)
        crop.quantity = request.POST.get('quantity', crop.quantity)
        crop.wholesale_price = request.POST.get('wholesale_price') or None
        crop.retail_price = request.POST.get('retail_price') or None
        crop.description = request.POST.get('description', '')
        
        # Handle image upload
        if request.FILES.get('image'):
            crop.image = request.FILES.get('image')
    else:
        # Handle JSON data
        import json
        try:
            data = json.loads(request.body)
        except:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Update fields
        crop.crop_name = data.get('crop_name', crop.crop_name)
        crop.grade = data.get('grade', crop.grade)
        crop.status = data.get('status', crop.status)
        crop.price = data.get('price', crop.price)
        crop.quantity = data.get('quantity', crop.quantity)
        crop.wholesale_price = data.get('wholesale_price') or None
        crop.retail_price = data.get('retail_price') or None
        crop.description = data.get('description', '')
    
    crop.save()
    
    # Clear cache
    _clear_available_crops_cache()
    
    return JsonResponse({'success': True, 'message': 'Crop updated successfully'})


@login_required
def delete_crop_ajax(request, crop_id):
    """API endpoint to delete crop via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    crop = get_object_or_404(Crop, id=crop_id)
    
    # Check permission
    if request.user.account_type != 'admin' and crop.user != request.user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    crop_name = crop.crop_name
    crop.delete()
    
    # Clear cache
    _clear_available_crops_cache()
    
    return JsonResponse({'success': True, 'message': f'Crop "{crop_name}" deleted successfully'})


@csrf_exempt
@require_POST
def get_crop_names(request):
    """
    API Endpoint: /crops/get-names/
    Returns all unique crop names from the database for ML predictions
    Optimized for performance with proper caching
    """
    # Cache crop names for 6 hours since they don't change frequently
    cache_key = 'all_crop_names'
    cached_names = cache.get(cache_key)

    if cached_names is not None:
        return JsonResponse({
            'status': 'success',
            'crop_names': cached_names,
            'count': len(cached_names),
            'cached': True
        })

    try:
        # Get all unique crop names from database - optimized query
        crop_names_list = list(Crop.objects.values_list('crop_name', flat=True).distinct())

        # Cache for 6 hours (21600 seconds) - longer cache for better performance
        cache.set(cache_key, crop_names_list, 21600)

        return JsonResponse({
            'status': 'success',
            'crop_names': crop_names_list,
            'count': len(crop_names_list)
        })

    except Exception as e:
        return JsonResponse({'error': f'Failed to get crop names: {str(e)}'}, status=500)

