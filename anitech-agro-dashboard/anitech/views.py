from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .utils import set_language, get_current_lang, get_translations, get_crop_name
from functools import wraps

def account_type_required(*allowed_types):
    """Decorator to restrict access based on account type"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.account_type not in allowed_types:
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def home_view(request):
    return render(request, 'home.html')


def _get_inventory_queryset(user):
    from market.models import Inventory

    if not getattr(user, 'is_authenticated', False):
        return Inventory.objects.none()
    if user.account_type in ['admin', 'secretary']:
        return Inventory.objects.all().order_by('-date_added')
    return Inventory.objects.filter(user=user).order_by('-date_added')


def _get_dashboard_cache_key(user):
    from django.db.models import Max
    from crops.models import Crop
    from market.models import BuyerOffer, Inventory, ScheduleDistribution, SellerOffer

    user_id = getattr(user, 'id', None) or 'guest'
    account_type = getattr(user, 'account_type', 'guest')

    def get_cached_max_id(cache_key, queryset):
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        latest_id = queryset.aggregate(max_id=Max('id')).get('max_id') or 0
        cache.set(cache_key, latest_id, 60)
        return latest_id

    crop_latest = get_cached_max_id('dashboard_sig_crop', Crop.objects.all())
    offer_latest = get_cached_max_id('dashboard_sig_buyer_offer', BuyerOffer.objects.all())
    seller_offer_latest = get_cached_max_id('dashboard_sig_seller_offer', SellerOffer.objects.all())
    schedule_latest = get_cached_max_id('dashboard_sig_schedule', ScheduleDistribution.objects.all())

    if getattr(user, 'is_authenticated', False):
        inventory_latest = get_cached_max_id(
            f'dashboard_sig_inventory_{user_id}_{account_type}',
            _get_inventory_queryset(user),
        )
    else:
        inventory_latest = 0

    return (
        f"dashboard_full_v4_{user_id}_{account_type}_"
        f"c{crop_latest}_o{offer_latest}_so{seller_offer_latest}_"
        f"s{schedule_latest}_i{inventory_latest}"
    )

def system_health_check(request):
    """System health check endpoint for monitoring"""
    from ml_service.views import get_current_weather, generate_crop_prediction_result
    from market.views import get_market_price_data
    from crops.views import _build_crop_prediction_payload
    from django.core.cache import cache

    health_status = {
        'database': False,
        'cache': False,
        'weather_api': False,
        'ml_predictions': False,
        'market_data': False,
        'timestamp': timezone.now().isoformat()
    }

    try:
        # Check database
        from crops.models import Crop
        Crop.objects.count()
        health_status['database'] = True
    except Exception as e:
        health_status['database_error'] = str(e)

    try:
        # Check cache
        cache.set('health_test', 'ok', 10)
        test_value = cache.get('health_test')
        health_status['cache'] = test_value == 'ok'
    except Exception as e:
        health_status['cache_error'] = str(e)

    try:
        # Check weather API
        weather = get_current_weather()
        health_status['weather_api'] = isinstance(weather, dict) and 'temperature' in weather
    except Exception as e:
        health_status['weather_api_error'] = str(e)

    try:
        # Check ML predictions
        payload, _, _ = _build_crop_prediction_payload('Wet')
        result = generate_crop_prediction_result(payload)
        health_status['ml_predictions'] = result.get('status') == 'success'
    except Exception as e:
        health_status['ml_predictions_error'] = str(e)

    try:
        # Check market data
        market_data = get_market_price_data()
        health_status['market_data'] = isinstance(market_data, list)
    except Exception as e:
        health_status['market_data_error'] = str(e)

    status_code = 200 if all([health_status[k] for k in ['database', 'cache', 'weather_api', 'ml_predictions', 'market_data']]) else 503

    return JsonResponse(health_status, status=status_code)

@login_required
def set_language_view(request):
    """Handle language switching - based on old PHP system update_language action"""
    if request.method == 'POST':
        language = request.POST.get('language', 'en')
        set_language(request, language)
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


# @login_required
# @account_type_required('admin', 'farmer', 'buyer')
def weather_view(request):
    """
    Weather forecast page view.
    Uses Open-Meteo API for weather data with fallback support.
    """
    from ml_service.views import (
        get_current_weather,
        get_weekly_forecast,
        get_farming_recommendations
    )
    from django.core.cache import cache
    import hashlib
    from activity_log.utils import log_activity
    from notifications.services import notify_admins_once, notify_all_users

    # Weather forecasting is fixed to Legazpi City, Albay, Philippines.
    latitude = 13.1431
    longitude = 123.7438

    # Cache the entire weather page context
    cache_key = f"weather_page_{latitude}_{longitude}"
    cached_context = cache.get(cache_key)
    if cached_context:
        return render(request, 'weather.html', cached_context)

    # Get weather data using Open-Meteo API
    current_weather = get_current_weather(latitude, longitude)
    forecast = get_weekly_forecast(latitude, longitude)
    recommendations = get_farming_recommendations(current_weather, forecast)

    weather_snapshot = {
        'condition': current_weather.get('condition'),
        'temperature': current_weather.get('temperature'),
        'humidity': current_weather.get('humidity'),
    }
    weather_alert_key = 'weather_notification_snapshot'
    previous_snapshot = cache.get(weather_alert_key)
    if previous_snapshot != weather_snapshot:
        cache.set(weather_alert_key, weather_snapshot, 3600)
        summary_message = (
            f"Weather forecast updated: {current_weather.get('condition', 'Unknown')} at "
            f"{current_weather.get('temperature', '--')}°C in Legazpi City."
        )
        notify_admins_once(
            'admin_notification_weather_forecast',
            weather_snapshot,
            'Weather forecast updated',
            summary_message,
            notif_type='weather',
            timeout=3600,
        )
        notify_all_users('Weather forecast updated', summary_message, notif_type='weather')
        log_activity(
            user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
            event_type='read',
            severity='info',
            status='success',
            action='Weather forecast updated',
            description=summary_message,
            resource_type='system',
            resource_name='Weather',
        )

    if getattr(request, 'user', None) and request.user.is_authenticated:
        log_activity(
            request=request,
            user=request.user,
            event_type='read',
            severity='info',
            status='success',
            action='Viewed weather forecast',
            description=f'{request.user.username} viewed the weather forecast page.',
            resource_type='system',
            resource_name='Weather',
        )

    context = {
        'current_weather': current_weather,
        'forecast': forecast,
        'recommendations': recommendations,
        'latitude': latitude,
        'longitude': longitude,
    }

    # Cache for 15 minutes (weather data cache duration)
    cache.set(cache_key, context, 900)

    return render(request, 'weather.html', context)


# @login_required
def dashboard_view(request):
    """Dashboard view - main page after login"""
    from crops.models import Crop
    from market.models import BuyerOffer, SellerOffer, MarketPrice, ScheduleDistribution
    from notifications.models import Notification
    from django.core.cache import cache
    import json
    import hashlib

    user = request.user
    if not user.is_authenticated:
        # Mock user for anonymous access
        class MockUser:
            def __init__(self):
                self.account_type = 'buyer'
                self.id = None
                self.username = 'guest'
        user = MockUser()

    dashboard_cache_key = _get_dashboard_cache_key(user)
    cached_dashboard = cache.get(dashboard_cache_key)
    if cached_dashboard:
        template_name = 'buyer_dashboard.html' if user.account_type == 'buyer' and 'my_offers' in cached_dashboard else 'dashboard.html'
        return render(request, template_name, cached_dashboard)

    # Reuse the crop recommendations pipeline so dashboard cards stay aligned
    # with the ML model, Open-Meteo weather, and market price crop pool.
    from ml_service.views import get_weekly_forecast, generate_crop_prediction_result
    from crops.views import (
        _build_crop_prediction_payload,
        _build_recommendation_cards,
        _notify_admins_about_top_recommendation,
    )

    ml_payload, current_weather, market_snapshot = _build_crop_prediction_payload()
    season = ml_payload['season']

    try:
        prediction_result = generate_crop_prediction_result(ml_payload)
        ml_predictions = prediction_result.get('predictions', [])
    except Exception:
        prediction_result = {'predictions': []}
        ml_predictions = []

    predictions = _build_recommendation_cards(ml_predictions, season, current_weather, market_snapshot)
    _notify_admins_about_top_recommendation(predictions, season)

    # User-specific statistics
    if user.account_type == 'admin':
        # Cache expensive queries for 5 minutes
        cache_key_prefix = 'admin_dashboard_'
        total_crops = cache.get(cache_key_prefix + 'total_crops')
        if total_crops is None:
            total_crops = Crop.objects.count()
            cache.set(cache_key_prefix + 'total_crops', total_crops, 300)

        available_crops_count = cache.get(cache_key_prefix + 'available_crops')
        if available_crops_count is None:
            available_crops_count = Crop.objects.filter(status='available').count()
            cache.set(cache_key_prefix + 'available_crops', available_crops_count, 300)

        seller_offers_count = cache.get(cache_key_prefix + 'seller_offers_pending')
        if seller_offers_count is None:
            seller_offers_count = SellerOffer.objects.filter(status='Pending').count()
            cache.set(cache_key_prefix + 'seller_offers_pending', seller_offers_count, 300)

        total_offers = cache.get(cache_key_prefix + 'total_offers')
        if total_offers is None:
            total_offers = BuyerOffer.objects.count()
            cache.set(cache_key_prefix + 'total_offers', total_offers, 300)

        pending_offers = cache.get(cache_key_prefix + 'pending_offers')
        if pending_offers is None:
            pending_offers = BuyerOffer.objects.filter(status='Pending').count()
            cache.set(cache_key_prefix + 'pending_offers', pending_offers, 300)

        recent_crops = cache.get(cache_key_prefix + 'recent_crops')
        if recent_crops is None:
            recent_crops = list(Crop.objects.all()[:5])
            cache.set(cache_key_prefix + 'recent_crops', recent_crops, 300)

        recent_offers = cache.get(cache_key_prefix + 'recent_offers')
        if recent_offers is None:
            recent_offers = list(BuyerOffer.objects.order_by('-date_offered')[:5])
            cache.set(cache_key_prefix + 'recent_offers', recent_offers, 300)

        buyer_offers = cache.get(cache_key_prefix + 'buyer_offers')
        if buyer_offers is None:
            buyer_offers = list(BuyerOffer.objects.order_by('-date_offered')[:5])
            cache.set(cache_key_prefix + 'buyer_offers', buyer_offers, 300)
    elif user.account_type == 'secretary':
        cache_key_prefix = 'secretary_dashboard_'
        total_crops = cache.get(cache_key_prefix + 'total_crops')
        if total_crops is None:
            total_crops = Crop.objects.count()
            cache.set(cache_key_prefix + 'total_crops', total_crops, 300)

        available_crops_count = cache.get(cache_key_prefix + 'available_crops')
        if available_crops_count is None:
            available_crops_count = Crop.objects.filter(status='available').count()
            cache.set(cache_key_prefix + 'available_crops', available_crops_count, 300)

        seller_offers_count = cache.get(cache_key_prefix + 'seller_offers_pending')
        if seller_offers_count is None:
            seller_offers_count = SellerOffer.objects.filter(status='Pending').count()
            cache.set(cache_key_prefix + 'seller_offers_pending', seller_offers_count, 300)

        total_offers = cache.get(cache_key_prefix + 'total_offers')
        if total_offers is None:
            total_offers = BuyerOffer.objects.count()
            cache.set(cache_key_prefix + 'total_offers', total_offers, 300)

        pending_offers = cache.get(cache_key_prefix + 'pending_offers')
        if pending_offers is None:
            pending_offers = BuyerOffer.objects.filter(status='Pending').count()
            cache.set(cache_key_prefix + 'pending_offers', pending_offers, 300)

        recent_crops = cache.get(cache_key_prefix + 'recent_crops')
        if recent_crops is None:
            recent_crops = list(Crop.objects.all().order_by('-created_at')[:5])
            cache.set(cache_key_prefix + 'recent_crops', recent_crops, 300)

        recent_offers = cache.get(cache_key_prefix + 'recent_offers')
        if recent_offers is None:
            recent_offers = list(BuyerOffer.objects.order_by('-date_offered')[:5])
            cache.set(cache_key_prefix + 'recent_offers', recent_offers, 300)

        buyer_offers = cache.get(cache_key_prefix + 'buyer_offers')
        if buyer_offers is None:
            buyer_offers = list(BuyerOffer.objects.select_related('crop', 'farmer').order_by('-date_offered')[:5])
            cache.set(cache_key_prefix + 'buyer_offers', buyer_offers, 300)
    else:
        # Cache user-specific queries for 5 minutes
        user_cache_key_prefix = f'user_dashboard_{user.id}_'

        total_crops = cache.get(user_cache_key_prefix + 'total_crops')
        if total_crops is None:
            total_crops = Crop.objects.filter(user=user).count()
            cache.set(user_cache_key_prefix + 'total_crops', total_crops, 300)

        available_crops_count = cache.get(user_cache_key_prefix + 'available_crops')
        if available_crops_count is None:
            available_crops_count = Crop.objects.filter(status='available', user=user).count()
            cache.set(user_cache_key_prefix + 'available_crops', available_crops_count, 300)

        seller_offers_count = cache.get(user_cache_key_prefix + 'seller_offers_pending')
        if seller_offers_count is None:
            seller_offers_count = SellerOffer.objects.filter(farmer=user, status='Pending').count()
            cache.set(user_cache_key_prefix + 'seller_offers_pending', seller_offers_count, 300)

        if user.account_type == 'farmer':
            total_offers = cache.get(user_cache_key_prefix + 'total_offers')
            if total_offers is None:
                total_offers = BuyerOffer.objects.filter(farmer=user).count()
                cache.set(user_cache_key_prefix + 'total_offers', total_offers, 300)

            pending_offers = cache.get(user_cache_key_prefix + 'pending_offers')
            if pending_offers is None:
                pending_offers = BuyerOffer.objects.filter(farmer=user, status='Pending').count()
                cache.set(user_cache_key_prefix + 'pending_offers', pending_offers, 300)

            farmer_crop_ids = cache.get(user_cache_key_prefix + 'farmer_crop_ids')
            if farmer_crop_ids is None:
                farmer_crop_ids = list(Crop.objects.filter(user=user).values_list('id', flat=True))
                cache.set(user_cache_key_prefix + 'farmer_crop_ids', farmer_crop_ids, 300)

            recent_offers = cache.get(user_cache_key_prefix + 'recent_offers')
            if recent_offers is None:
                recent_offers = list(BuyerOffer.objects.filter(crop_id__in=farmer_crop_ids).order_by('-date_offered')[:5])
                cache.set(user_cache_key_prefix + 'recent_offers', recent_offers, 300)

            buyer_offers = cache.get(user_cache_key_prefix + 'buyer_offers')
            if buyer_offers is None:
                buyer_offers = list(BuyerOffer.objects.filter(farmer=user).order_by('-date_offered')[:5])
                cache.set(user_cache_key_prefix + 'buyer_offers', buyer_offers, 300)
        else:
            total_offers = cache.get(user_cache_key_prefix + 'total_offers')
            if total_offers is None:
                total_offers = BuyerOffer.objects.filter(buyer_name=user.username).count()
                cache.set(user_cache_key_prefix + 'total_offers', total_offers, 300)

            pending_offers = cache.get(user_cache_key_prefix + 'pending_offers')
            if pending_offers is None:
                pending_offers = BuyerOffer.objects.filter(buyer_name=user.username, status='Pending').count()
                cache.set(user_cache_key_prefix + 'pending_offers', pending_offers, 300)

            recent_offers = cache.get(user_cache_key_prefix + 'recent_offers')
            if recent_offers is None:
                recent_offers = list(BuyerOffer.objects.filter(buyer_name=user.username).order_by('-date_offered')[:5])
                cache.set(user_cache_key_prefix + 'recent_offers', recent_offers, 300)

            buyer_offers = recent_offers

        recent_crops = cache.get(user_cache_key_prefix + 'recent_crops')
        if recent_crops is None:
            recent_crops = list(Crop.objects.filter(user=user)[:5])
            cache.set(user_cache_key_prefix + 'recent_crops', recent_crops, 300)

    # Market data with caching
    from market.models import MarketPrice, Inventory

    # Cache recent prices
    recent_prices_cache_key = 'dashboard_recent_prices'
    recent_prices = cache.get(recent_prices_cache_key)
    if recent_prices is None:
        recent_prices = list(MarketPrice.objects.order_by('-date')[:10])
        cache.set(recent_prices_cache_key, recent_prices, 300)

    # Cache user notifications
    if hasattr(user, 'id'):
        notifications_cache_key = f'user_notifications_{user.id}'
        notifications = cache.get(notifications_cache_key)
        if notifications is None:
            notifications = list(Notification.objects.filter(user=user)[:5])
            cache.set(notifications_cache_key, notifications, 300)

        unread_count_cache_key = f'user_unread_count_{user.id}'
        unread_count = cache.get(unread_count_cache_key)
        if unread_count is None:
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
            cache.set(unread_count_cache_key, unread_count, 60)  # Shorter cache for unread count
    else:
        notifications = []
        unread_count = 0

    # Cache market trends data
    market_trends_cache_key = 'dashboard_market_trends'
    market_trends_json = cache.get(market_trends_cache_key)
    if market_trends_json is None:
        market_prices_chart = list(MarketPrice.objects.order_by('-date')[:10])
        market_trends = [{'crop': mp.crop_name, 'price': float(mp.current_price)} for mp in market_prices_chart]
        market_trends_json = json.dumps(market_trends)
        cache.set(market_trends_cache_key, market_trends_json, 300)

    # Cache ML-backed market chart data for the dashboard.
    from market.views import generate_fallback_market_predictions, generate_ml_market_predictions, get_market_price_data, get_baseline_prices
    price_data = get_market_price_data()
    dashboard_market_chart_crops = [item['crop'] for item in price_data[:5]] if price_data else list(get_baseline_prices().keys())[:5]
    market_chart_cache_key = (
        f"dashboard_market_chart_{season}_"
        f"{round(float(current_weather.get('temperature', 28) or 28), 1)}_"
        f"{round(float(current_weather.get('humidity', 75) or 75), 1)}_"
        f"{round(float(current_weather.get('rainfall', 0) or 0), 1)}_"
        f"{'_'.join(dashboard_market_chart_crops)}"
    )
    dashboard_market_predictions = cache.get(market_chart_cache_key)
    if dashboard_market_predictions is None:
        market_weather_data = {
            'temperature': current_weather.get('temperature', 28),
            'humidity': current_weather.get('humidity', 75),
            'precipitation': current_weather.get('precipitation', 0),
            'rainfall': current_weather.get('rainfall', 0),
        }
        try:
            dashboard_market_predictions = generate_ml_market_predictions(dashboard_market_chart_crops, market_weather_data)
        except Exception:
            dashboard_market_predictions = generate_fallback_market_predictions(dashboard_market_chart_crops)
        cache.set(market_chart_cache_key, dashboard_market_predictions, 600)

    # Weather forecast (cached)
    try:
        forecast = cache.get('dashboard_forecast')
        if not forecast:
            forecast = get_weekly_forecast(13.1431, 123.7438)
            cache.set('dashboard_forecast', forecast, 1800)
    except Exception:
        forecast = []

    # Available crops for market (cached)
    cache_key = f'dashboard_available_crops_{user.id}' if user.id else 'dashboard_available_crops'
    try:
        available_crops_list = cache.get(cache_key)
        if not available_crops_list:
            if user.account_type != 'admin':
                available_crops_list = list(Crop.objects.filter(status='available', user=user)[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))
            else:
                available_crops_list = list(Crop.objects.filter(status='available')[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))
            cache.set(cache_key, available_crops_list, 300)
    except Exception:
        if user.account_type != 'admin':
            available_crops_list = list(Crop.objects.filter(status='available', user=user)[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))
        else:
            available_crops_list = list(Crop.objects.filter(status='available')[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))

    # Seller offers
    if user.account_type == 'admin':
        seller_offers = SellerOffer.objects.all().select_related('farmer', 'crop').order_by('-date_posted')[:10]
    elif user.account_type == 'farmer':
        seller_offers = SellerOffer.objects.filter(farmer=user).select_related('farmer', 'crop').order_by('-date_posted')[:10]
    else:
        seller_offers = SellerOffer.objects.all().select_related('farmer', 'crop').order_by('-date_posted')[:10]

    # ML statistics
    ml_seasonal_count = sum(1 for p in predictions if p.get('category') == 'seasonal') if predictions else 0
    ml_high_demand_count = sum(1 for p in predictions if p.get('category') == 'high-demand') if predictions else 0
    ml_rising_trends_count = sum(1 for p in predictions if p.get('trend') == 'rising') if predictions else 0

    schedules_preview = list(ScheduleDistribution.objects.order_by('scheduled_date')[:3])

    # Language & inventory
    lang = request.session.get('lang', 'en')
    inventory_items = list(_get_inventory_queryset(user)[:10]) if user.account_type != 'buyer' else []

    context = {
        'total_crops': total_crops,
        'available_crops': available_crops_list,
        'available_crops_count': available_crops_count,
        'seller_offers_count': seller_offers_count,
        'total_offers': total_offers,
        'pending_offers': pending_offers,
        'recent_crops': recent_crops,
        'recent_offers': recent_offers,
        'recent_prices': recent_prices,
        'notifications': notifications,
        'unread_count': unread_count,
        'market_trends_json': market_trends_json,
        'dashboard_market_predictions': dashboard_market_predictions,
        'dashboard_market_chart_crops': dashboard_market_chart_crops,
        'forecast': forecast,
        'predictions': predictions,
        'dashboard_prediction_pool': ml_payload.get('crops', []),
        'dashboard_market_prices': ml_payload.get('market_prices', {}),
        'crops': available_crops_list,
        'buyer_offers': buyer_offers,
        'seller_offers': seller_offers,
        'schedules_preview': schedules_preview,
        'season': season,
        'lang': lang,
        'inventory_items': inventory_items,
        'ml_seasonal_count': ml_seasonal_count,
        'ml_high_demand_count': ml_high_demand_count,
        'ml_rising_trends_count': ml_rising_trends_count,
        'seasonal_crops': [p for p in predictions if p.get('category') == 'seasonal'] if predictions else [],
        'weather_snapshot': {
            'temperature': current_weather.get('temperature', 27),
            'humidity': current_weather.get('humidity', 75),
            'rainfall': current_weather.get('rainfall', 0),
        },
    }

    # Buyer-specific redirect with caching
    if user.account_type == 'buyer':
        from market.models import BuyerOffer, SellerOffer, MarketPrice
        from django.core.paginator import Paginator
        from crops.models import Crop

        buyer_cache_key = f'buyer_dashboard_v2_{user.id}'
        cached_buyer_data = cache.get(buyer_cache_key)
        if cached_buyer_data:
            # Still need to handle pagination dynamically
            buyer_offers_qs = BuyerOffer.objects.filter(buyer_name=user.username).order_by('-date_offered')
            paginator = Paginator(buyer_offers_qs, 10)
            page_obj = paginator.get_page(request.GET.get('page', 1))
            cached_buyer_data['my_offers'] = page_obj
            return render(request, 'buyer_dashboard.html', cached_buyer_data)

        buyer_total_offers = BuyerOffer.objects.filter(buyer_name=user.username).count()
        buyer_pending = BuyerOffer.objects.filter(buyer_name=user.username, status='Pending').count()
        buyer_accepted = BuyerOffer.objects.filter(buyer_name=user.username, status='Accepted').count()
        active_crops = Crop.objects.filter(status='available').count()
        total_crops = Crop.objects.count()
        market_prices_count = MarketPrice.objects.count()
        buyer_offers_qs = BuyerOffer.objects.filter(buyer_name=user.username).order_by('-date_offered')
        paginator = Paginator(buyer_offers_qs, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        available_crops = list(Crop.objects.filter(status='available').order_by('-created_at')[:10])

        buyer_context = {
            'my_offers': page_obj,
            'available_crops': available_crops,
            'pending_count': buyer_pending,
            'accepted_count': buyer_accepted,
            'active_offers': active_crops,
            'total_crops': total_crops,
            'market_prices_count': market_prices_count,
            'lang': request.session.get('lang', 'en'),
        }

        # Cache buyer dashboard data for 5 minutes (except pagination)
        cache.set(buyer_cache_key, buyer_context, 300)

        return render(request, 'buyer_dashboard.html', buyer_context)

    # Cache the dashboard context for 5 minutes
    cache.set(dashboard_cache_key, context, 300)

    return render(request, 'dashboard.html', context)


def dashboard_recommendations_api(request):
    from crops.views import (
        _build_crop_prediction_payload,
        _build_recommendation_cards,
        _notify_admins_about_top_recommendation,
    )
    from ml_service.views import generate_crop_prediction_result

    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        ml_payload, current_weather, market_snapshot = _build_crop_prediction_payload()
        season = ml_payload['season']
        prediction_result = generate_crop_prediction_result(ml_payload)
        ml_predictions = prediction_result.get('predictions', [])
        recommendations = _build_recommendation_cards(ml_predictions, season, current_weather, market_snapshot)
        _notify_admins_about_top_recommendation(recommendations, season)

        return JsonResponse({
            'status': 'success',
            'predictions': recommendations,
            'season': season,
        })
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


@login_required
def schedule_view(request):
    """Schedule view for distribution schedules"""
    from market.models import ScheduleDistribution
    
    schedules = ScheduleDistribution.objects.all().order_by('scheduled_date')
    
    context = {
        'schedules': schedules,
    }
    
    return render(request, 'schedule.html', context)


@login_required
def profile_view(request):
    """Profile view for user profile"""
    from crops.models import Crop
    from market.models import BuyerOffer, SellerOffer
    
    user = request.user
    
    # Get user stats
    crops_count = Crop.objects.filter(user=user).count() if hasattr(user, 'id') else 0
    offers_count = BuyerOffer.objects.filter(farmer=user).count() if hasattr(user, 'id') else 0
    
    context = {
        'user': user,
        'crops_count': crops_count,
        'offers_count': offers_count,
    }
    
    return render(request, 'profile.html', context)

# Inventory Views
@login_required
def inventory_list(request):
    inventory_items = _get_inventory_queryset(request.user)
    context = {
        'inventory_items': inventory_items,
    }
    return render(request, 'inventory.html', context)


@login_required
def inventory_add(request):
    from market.models import Inventory
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        item_type = request.POST.get('item_type', 'other')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit', 'pcs')
        Inventory.objects.create(
            user=request.user,
            item_name=item_name,
            item_type=item_type,
            quantity=int(quantity),
            unit=unit
        )
    return redirect('dashboard')

@login_required
def inventory_edit(request, inventory_id):
    from market.models import Inventory
    from django.shortcuts import get_object_or_404
    inventory = get_object_or_404(Inventory, id=inventory_id, user=request.user)
    if request.method == 'POST':
        inventory.item_name = request.POST.get('item_name')
        inventory.item_type = request.POST.get('item_type', 'other')
        inventory.quantity = int(request.POST.get('quantity'))
        inventory.unit = request.POST.get('unit', 'pcs')
        inventory.save()
    return redirect('dashboard')

@login_required
def inventory_delete(request, inventory_id):
    from market.models import Inventory
    from django.shortcuts import get_object_or_404
    inventory = get_object_or_404(Inventory, id=inventory_id, user=request.user)
    inventory.delete()
    return redirect('dashboard')
