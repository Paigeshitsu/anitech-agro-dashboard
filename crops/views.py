from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Crop
from .forms import CropForm

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

def get_translated_crop_name(crop_name, lang='en'):
    """Get translated crop name based on language"""
    return CROP_TRANSLATIONS.get(crop_name, {}).get(lang, crop_name)

@login_required
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
def crop_add(request):
    """Add a new crop"""
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.user = request.user
            crop.save()
            messages.success(request, f'Crop "{crop.crop_name}" added successfully!')
            return redirect('crops')
    else:
        form = CropForm()
    
    return render(request, 'crop_form.html', {
        'form': form,
        'action': 'Add'
    })

@login_required
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
        messages.success(request, f'Crop "{crop_name}" deleted successfully!')
        return redirect('crops')
    
    return render(request, 'crop_confirm_delete.html', {'crop': crop})

@login_required
def crop_view(request, crop_id):
    """View crop details"""
    crop = get_object_or_404(Crop, id=crop_id)
    return render(request, 'crop_detail.html', {'crop': crop})


@login_required
def available_crops(request):
    """List all available crops for buyers"""
    # Get filter and sort parameters
    sort_by = request.GET.get('sort', 'newest')
    lang = request.session.get('lang', 'en')
    
    # Only show available crops
    crops = Crop.objects.filter(status='available')
    
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
        messages.success(request, f'Purchased {crop.crop_name} ({crop.quantity}kg) for ₱{crop.price}!')
        # Create notification to farmer
        try:
            from notifications.models import Notification
            Notification.objects.create(
                user=crop.user,
                title=f'Crop Sold: {crop.crop_name}',
                message=f'Your {crop.crop_name} has been purchased by {request.user.username}',
                notification_type='sale'
            )
        except:
            pass
        return redirect('crops:available_crops')
    
    return render(request, 'crop_detail.html', {'crop': crop, 'buy_mode': True})

