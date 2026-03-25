from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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

@login_required
def set_language_view(request):
    """Handle language switching - based on old PHP system update_language action"""
    if request.method == 'POST':
        language = request.POST.get('language', 'en')
        set_language(request, language)
    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
@account_type_required('admin', 'farmer')
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
    from market.models import BuyerOffer, SellerOffer, MarketPrice, ScheduleDistribution
    from notifications.models import Notification
    from django.core.cache import cache
    import json
    
    # Get user-specific data
    user = request.user
    
    # Get stats
    if user.account_type == 'admin':
        total_crops = Crop.objects.count()
        available_crops_count = Crop.objects.filter(status='available').count()
        seller_offers_count = SellerOffer.objects.filter(status='Pending').count()
        total_offers = BuyerOffer.objects.count()
        pending_offers = BuyerOffer.objects.filter(status='Pending').count()
        # Get all recent data for admin
        recent_crops = Crop.objects.all()[:5]
        recent_offers = BuyerOffer.objects.order_by('-date_offered')[:5]
        buyer_offers = BuyerOffer.objects.order_by('-date_offered')[:5]
    else:
        # Farmers and buyers see only their own data
        total_crops = Crop.objects.filter(user=user).count()
        available_crops_count = Crop.objects.filter(status='available', user=user).count()
        seller_offers_count = SellerOffer.objects.filter(farmer=user, status='Pending').count()
        # For farmers, show offers for their crops; for buyers, show their offers
        if user.account_type == 'farmer':
            total_offers = BuyerOffer.objects.filter(farmer=user).count()
            pending_offers = BuyerOffer.objects.filter(farmer=user, status='Pending').count()
            # Get offers for this farmer's crops
            farmer_crop_ids = Crop.objects.filter(user=user).values_list('id', flat=True)
            recent_offers = BuyerOffer.objects.filter(crop_id__in=farmer_crop_ids).order_by('-date_offered')[:5]
            buyer_offers = BuyerOffer.objects.filter(farmer=user).order_by('-date_offered')[:5]
        else:
            # Buyer sees their own offers
            total_offers = BuyerOffer.objects.filter(buyer_name=user.username).count()
            pending_offers = BuyerOffer.objects.filter(buyer_name=user.username, status='Pending').count()
            recent_offers = BuyerOffer.objects.filter(buyer_name=user.username).order_by('-date_offered')[:5]
            buyer_offers = recent_offers
        # Get farmer's own crops
        recent_crops = Crop.objects.filter(user=user)[:5]
    from market.models import MarketPrice, Inventory
    recent_prices = MarketPrice.objects.order_by('-date')[:10]
    market_prices = recent_prices[:5]  # For table in template
    
    # Get notifications
    notifications = Notification.objects.filter(user=user)[:5] if hasattr(user, 'id') else []
    unread_count = Notification.objects.filter(user=user, is_read=False).count() if hasattr(user, 'id') else 0
    
    # Get market prices for graph (horizontal bar)
    market_prices = MarketPrice.objects.order_by('-date')[:10]
    market_trends = []
    for mp in market_prices:
        market_trends.append({
            'crop': mp.crop_name,
            'price': float(mp.current_price)
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
    
    # Get available crops for market distribution (user-specific cache)
    cache_key = f'dashboard_available_crops_{user.id}' if user.id else 'dashboard_available_crops'
    try:
        available_crops_list = cache.get(cache_key)
        if not available_crops_list:
            # For farmers, only show their own crops; for admins, show all
            if user.account_type != 'admin':
                available_crops_list = list(Crop.objects.filter(status='available', user=user)[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))
            else:
                available_crops_list = list(Crop.objects.filter(status='available')[:10].values('id', 'crop_name', 'quantity', 'price', 'unit', 'status', 'created_at'))
            cache.set(cache_key, available_crops_list, 300)  # Cache for 5 min
    except:
        if user.account_type != 'admin':
            available_crops_list = Crop.objects.filter(status='available', user=user)[:10]
        else:
            available_crops_list = Crop.objects.filter(status='available')[:10]
    
    # Get seller offers (market offers) - for buyers to see and make offers on
    if user.account_type == 'admin':
        seller_offers = SellerOffer.objects.all().select_related('farmer', 'crop').order_by('-date_posted')[:10]
    elif user.account_type == 'farmer':
        seller_offers = SellerOffer.objects.filter(farmer=user).select_related('farmer', 'crop').order_by('-date_posted')[:10]
    else:
        # Buyers see all seller offers to make offers on
        seller_offers = SellerOffer.objects.all().select_related('farmer', 'crop').order_by('-date_posted')[:10]
    
    # Get season based on current month (from crops views)
    from datetime import datetime
    current_month = datetime.now().month
    season = "Wet" if 6 <= current_month <= 11 else "Dry"
    
    # Get language preference
    lang = request.session.get('lang', 'en')
    
    # Get inventory items for this user
    inventory_items = Inventory.objects.filter(user=user).order_by('-date_added')[:10] if user.account_type != 'buyer' else []
    
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
        'forecast': forecast,
        'predictions': predictions,
        'crops': available_crops_list,
        'buyer_offers': buyer_offers,
        'seller_offers': seller_offers,
        'season': season,
        'lang': lang,
        'inventory_items': inventory_items,
    }
    
    # For buyers, redirect to buyer dashboard
    if user.account_type == 'buyer':
        from market.models import BuyerOffer, SellerOffer, MarketPrice
        from django.core.paginator import Paginator
        # Get buyer-specific stats
        buyer_total_offers = BuyerOffer.objects.filter(buyer_name=user.username).count()
        buyer_pending = BuyerOffer.objects.filter(buyer_name=user.username, status='Pending').count()
        buyer_accepted = BuyerOffer.objects.filter(buyer_name=user.username, status='Accepted').count()
        active_seller_offers = SellerOffer.objects.filter(status='Available').count()
        from crops.models import Crop
        total_crops = Crop.objects.count()
        market_prices_count = MarketPrice.objects.count()
        
        # Get buyer's own offers
        buyer_offers = BuyerOffer.objects.filter(buyer_name=user.username).order_by('-date_offered')
        paginator = Paginator(buyer_offers, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))
        
        return render(request, 'buyer_dashboard.html', {
            'offers': page_obj,
            'pending_count': buyer_pending,
            'accepted_count': buyer_accepted,
            'active_offers': active_seller_offers,
            'total_crops': total_crops,
            'market_prices_count': market_prices_count,
        })
    
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

