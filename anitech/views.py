


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .utils import set_language, get_current_lang, get_translations, get_crop_name

def home_view(request):
    return render(request, 'home.html')

@login_required
def set_language_view(request):
    """Handle language switching - based on old PHP system update_language action"""
    if request.method == 'POST':
        language = request.POST.get('language', 'en')
        set_language(request, language)
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
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
    
    # Default coordinates (Legazpi City, Albay, Philippines)
    latitude = request.GET.get('lat', 13.1422)
    longitude = request.GET.get('lon', 123.7438)
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        latitude = 13.1422
        longitude = 123.7438
    
    # Get weather data using Open-Meteo API
    current_weather = get_current_weather(latitude, longitude)
    forecast = get_weekly_forecast(latitude, longitude)
    recommendations = get_farming_recommendations(current_weather, forecast)
    
    context = {
        'current_weather': current_weather,
        'forecast': forecast,
        'recommendations': recommendations,
        'latitude': latitude,
        'longitude': longitude,
    }
    
    return render(request, 'weather.html', context)


@login_required
def dashboard_view(request):
    """Dashboard view - main page after login"""
    from crops.models import Crop
    from market.models import BuyerOffer, MarketPrice, ScheduleDistribution
    from notifications.models import Notification
    from django.core.cache import cache
    import json
    
    # Get user-specific data
    user = request.user
    
    # Get stats
    total_crops = Crop.objects.filter(user=user).count() if hasattr(user, 'id') else 0
    available_crops = Crop.objects.filter(status='available').count()
    total_offers = BuyerOffer.objects.count()
    pending_offers = BuyerOffer.objects.filter(status='pending').count()
    
    # Get recent data
    recent_crops = Crop.objects.all()[:5]
    recent_offers = BuyerOffer.objects.order_by('-date_offered')[:5]
    recent_prices = MarketPrice.objects.order_by('-date')[:5]
    
    # Get notifications
    notifications = Notification.objects.filter(user=user)[:5] if hasattr(user, 'id') else []
    unread_count = Notification.objects.filter(user=user, is_read=False).count() if hasattr(user, 'id') else 0
    
    # Get market prices for graph (horizontal bar)
    market_prices = MarketPrice.objects.order_by('-date')[:10]
    market_trends = []
    for mp in market_prices:
        market_trends.append({
            'crop': mp.crop_name,
            'price': float(mp.price)
        })
    market_trends_json = json.dumps(market_trends)
    
    # Get 7-day weather forecast (cached)
    from ml_service.views import get_current_weather, get_weekly_forecast
    try:
        forecast = cache.get('dashboard_forecast')
        if not forecast:
            forecast = get_weekly_forecast(13.1422, 123.7438)
            cache.set('dashboard_forecast', forecast, 1800)  # Cache for 30 min
    except:
        forecast = []
    
    # Get AI crop predictions (cached for faster loading)
    try:
        predictions = cache.get('dashboard_predictions')
        if not predictions:
            from ml_service.model import get_model, predict_top_k
            model = get_model()
            if model:
                predictions = predict_top_k(model, {
                    'location': 'Legazpi',
                    'season': 'wet',
                    'ph': 6.5,
                    'rainfall': 1500
                }, k=8)
            else:
                # Fallback predictions
                predictions = [
                    {'crop': 'Rice', 'score': 92, 'season': 'Wet', 'trend': 'rising', 'change_pct': 5, 'price': 50, 'category': 'seasonal'},
                    {'crop': 'Corn', 'score': 88, 'season': 'Dry', 'trend': 'rising', 'change_pct': 3, 'price': 45, 'category': 'seasonal'},
                    {'crop': 'Tomato', 'score': 85, 'season': 'Dry', 'trend': 'stable', 'change_pct': 1, 'price': 60, 'category': 'high-demand'},
                    {'crop': 'Eggplant', 'score': 82, 'season': 'Wet', 'trend': 'rising', 'change_pct': 4, 'price': 80, 'category': 'seasonal'},
                    {'crop': 'Cabbage', 'score': 78, 'season': 'Dry', 'trend': 'falling', 'change_pct': 2, 'price': 40, 'category': 'seasonal'},
                    {'crop': 'Pepper', 'score': 75, 'season': 'Wet', 'trend': 'rising', 'change_pct': 6, 'price': 70, 'category': 'high-demand'},
                    {'crop': 'Onion', 'score': 72, 'season': 'Dry', 'trend': 'stable', 'change_pct': 0, 'price': 55, 'category': 'high-demand'},
                    {'crop': 'Garlic', 'score': 70, 'season': 'Dry', 'trend': 'rising', 'change_pct': 3, 'price': 65, 'category': 'seasonal'},
                ]
            cache.set('dashboard_predictions', predictions, 3600)  # Cache for 1 hour
    except:
        predictions = []
    
    # Get available crops for market distribution
    available_crops_list = Crop.objects.filter(status='available')[:5]
    
    # Get buyer offers
    buyer_offers = BuyerOffer.objects.order_by('-date_offered')[:5]
    
    # Get season based on current month (from crops views)
    from datetime import datetime
    current_month = datetime.now().month
    season = "Wet" if 6 <= current_month <= 11 else "Dry"
    
    # Get language preference
    lang = request.session.get('lang', 'en')
    
    context = {
        'total_crops': total_crops,
        'available_crops': available_crops,
        'total_offers': total_offers,
        'pending_offers': pending_offers,
        'recent_crops': recent_crops,
        'recent_offers': recent_offers,
        'recent_prices': recent_prices,
        'notifications': notifications,
        'unread_count': unread_count,
        'market_trends_json': market_trends_json,
        'forecast': forecast,
        'predictions': predictions,
        'crops': available_crops_list,
        'buyer_offers': buyer_offers,
        'season': season,
        'lang': lang,
    }
    
    return render(request, 'dashboard.html', context)


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
    user = request.user
    
    context = {
        'user': user,
    }
    
    return render(request, 'profile.html', context)

