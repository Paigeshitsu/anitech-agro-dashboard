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
from .models import Crop
from .forms import CropForm
from anitech.views import account_type_required


def _clear_available_crops_cache():
    """Clear all available crops cache keys"""
    cache.delete('dashboard_available_crops')
    cache.delete('buyer_available_crops')
    # Clear all sort and search variations
    for sort in ['newest', 'oldest', 'price-high', 'price-low', 'name Asc', 'name-desc']:
        cache.delete(f'available_crops_sorted_{sort}')
        cache.delete(f'available_crops_sorted_{sort}_search_')

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
    'Beans': {'en': 'Beans', 'tl': 'Sitaw'},
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

def get_translated_crop_name(crop_name, lang='en'):
    """Get translated crop name based on language"""
    return CROP_TRANSLATIONS.get(crop_name, {}).get(lang, crop_name)


def _build_crop_prediction_payload(season):
    from ml_service.views import get_current_weather
    from .models import Crop
    from django.core.cache import cache

    cache_key = f'crop_prediction_payload_{season}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    weather = get_current_weather()
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

    crop_names = list(Crop.objects.values_list('crop_name', flat=True).distinct())

    # Use a region identifier matching ML model training data
    # Legazpi City, Albay is in Bicol Region → use 'Bicol'
    location = 'Bicol'

    result = ({
        'ph': 6.5,  # Soil pH - would need soil sensors for true live data
        'rainfall': rainfall,
        'temperature': temperature,
        'humidity': humidity,
        'location': location,
        'season': season,
        'crops': crop_names,
        'k': len(crop_names),
    }, weather)

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

@login_required
@account_type_required('admin', 'farmer', 'buyer')
def crop_recommendations(request):
    """ML-powered crop recommendations page"""
    lang = request.session.get('lang', 'en')

    # Get current season (simplified)
    current_month = timezone.now().month
    season = 'Wet' if 6 <= current_month <= 11 else 'Dry'

    # Cache key based on season and weather
    cache_key = f'crop_recommendations_{season}_{lang}'
    cached_data = cache.get(cache_key)
    if cached_data:
        return render(request, 'crops.html', cached_data)

    result = _build_crop_prediction_payload(season)
    payload, weather = result

    try:
        from ml_service.views import generate_crop_prediction_result

        prediction_result = generate_crop_prediction_result(payload)
        predictions = _enrich_predictions(prediction_result.get('predictions', []), season)
    except Exception as e:
        print(f"Crop recommendations error: {e}")
        prediction_result = {'source': 'error', 'predictions': []}
        predictions = []

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
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.user = request.user
            crop.save()
            # Clear available crops cache when new crop is added
            _clear_available_crops_cache()
            
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': crop.id,
                    'crop_name': crop.crop_name,
                    'message': f'Crop "{crop.crop_name}" added successfully!'
                })
            
            messages.success(request, f'Crop "{crop.crop_name}" added successfully!')
            return redirect('crops')
        else:
            # Form is invalid - return detailed error information
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Crop form errors: {form.errors}')
            logger.error(f'Crop form data: {request.POST}')
            logger.error(f'Crop form files: {request.FILES}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {}
                for field, error_list in form.errors.items():
                    errors[field] = [str(e) for e in error_list]
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid form data. Please check all required fields.',
                    'errors': errors
                }, status=400)
            else:
                # For non-AJAX requests, show form errors in template
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
        crop.delete()
        # Clear available crops cache when crop is deleted
        _clear_available_crops_cache()
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


@login_required
@account_type_required('admin', 'farmer', 'buyer')
def available_crops(request):
    """List all available crops for buyers - farmers see only their own crops"""
    # Get filter and sort parameters
    sort_by = request.GET.get('sort', 'newest')
    search_query = request.GET.get('search', '')
    lang = request.session.get('lang', 'en')
    
    # Farmers should only see their own crops in available crops
    if request.user.account_type == 'farmer':
        crops = Crop.objects.filter(status='available', user=request.user)
    elif request.user.account_type == 'admin':
        # Admins see all available crops
        crops = Crop.objects.filter(status='available')
    else:
        # Buyers see all available crops (marketplace)
        crops = Crop.objects.filter(status='available')
    
    # Only show available crops - use cache for faster loading (only for buyers)
    cache_key = f'available_crops_sorted_{sort_by}_search_{search_query}'
    if request.user.account_type == 'buyer':
        cached_crops = cache.get(cache_key)
        if cached_crops is not None:
            crops = cached_crops
    else:
        cache.delete(cache_key)  # Clear cache for farmers/admins to ensure fresh data
        
        # Apply search filter
        if search_query:
            crops = crops.filter(
                Q(crop_name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        # Apply sorting
        if sort_by == 'newest':
            crops = crops.order_by('-created_at')
        elif sort_by == 'oldest':
            crops = crops.order_by('created_at')
        elif sort_by == 'price-high':
            crops = crops.order_by('-price')
        elif sort_by == 'price-low':
            crops = crops.order_by('price')
        elif sort_by == 'name Asc':
            crops = crops.order_by('crop_name')
        elif sort_by == 'name-desc':
            crops = crops.order_by('-crop_name')
        
        # Cache for 5 minutes (300 seconds)
        cache.set(cache_key, crops, 300)
    
    # Add translated crop names
    for crop in crops:
        crop.translated_name = get_translated_crop_name(crop.crop_name, lang)
    
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
        messages.success(request, f'Purchased {crop.crop_name} ({crop.quantity}kg) for ₱{crop.price}!')
        # Create notification to farmer
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=crop.user,
                title=f'Crop Sold: {crop.crop_name}',
                message=f'Your {crop.crop_name} has been purchased by {request.user.username}',
                type='success'
            )
        except:
            pass
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

