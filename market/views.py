from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse
from django.http import HttpResponsePermanentRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import MarketPrice, BuyerOffer, ScheduleDistribution, SellerOffer, Crop
from .forms import MarketPriceForm, BuyerOfferForm, ScheduleDistributionForm, SellerOfferForm
import json
import random
from anitech.views import account_type_required

@login_required
@account_type_required('admin', 'farmer')
def market_prices_view(request):
    """Pure Django view for /market/ - renders prices.html with DB data + trends."""
    prices = MarketPrice.objects.all().order_by('-last_updated')[:20]
    price_data = []
    
    for price in prices:
        trend = 'stable'
        pct = 0
        if price.previous_price:
            pct = ((price.current_price - price.previous_price) / price.previous_price) * 100
            if pct > 2:
                trend = 'rising'
            elif pct < -2:
                trend = 'falling'
        
        price_data.append({
            'crop': price.crop_name,
            'current_price': float(price.current_price),
            'previous_price': float(price.previous_price or 0),
            'percentage_change': round(pct, 1),
            'trend': trend,
            'unit': price.unit,
            'last_updated': price.last_updated.strftime('%Y-%m-%d')
        })
    
    context = {
        'prices': price_data,
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
        
        # If no specific crops requested, get all available crops from database
        if not crops:
            market_prices = MarketPrice.objects.all().order_by('-last_updated')
            crops = list(market_prices.values_list('crop_name', flat=True).distinct())
        
        results = []
        for crop_name in crops:
            crop_name = crop_name.strip()
            if not crop_name:
                continue
            
            # Get actual price history from database
            price_history = MarketPrice.objects.filter(
                crop_name__iexact=crop_name
            ).order_by('-date')[:30]  # Last 30 records
            
            if price_history:
                # Use actual current price
                latest_price = price_history[0]
                current_price = float(latest_price.current_price)
                
                # Calculate trend based on actual price changes
                if len(price_history) >= 2:
                    previous_price = float(price_history[1].current_price)
                    if previous_price > 0:
                        percentage_change = ((current_price - previous_price) / previous_price) * 100
                    else:
                        percentage_change = 0
                else:
                    percentage_change = 0
                
                # Determine trend
                if percentage_change > 2:
                    trend = 'rising'
                elif percentage_change < -2:
                    trend = 'falling'
                else:
                    trend = 'stable'
                
                # For forecast, calculate simple average of recent prices
                avg_price = sum(float(p.current_price) for p in price_history) / len(price_history)
                
                results.append({
                    'crop': crop_name,
                    'current_price': round(current_price, 2),
                    'previous_price': round(previous_price, 2) if 'previous_price' in locals() else round(current_price, 2),
                    'forecast_price': round(avg_price, 2),
                    'percentage_change': round(percentage_change, 2),
                    'trend': trend,
                    'price_history': [
                        {
                            'date': p.date.strftime('%Y-%m-%d') if p.date else None,
                            'price': float(p.current_price)
                        }
                        for p in reversed(price_history[:7])  # Last 7 days for chart
                    ]
                })
            else:
                # No data in database - use default
                results.append({
                    'crop': crop_name,
                    'current_price': 0,
                    'previous_price': 0,
                    'forecast_price': 0,
                    'percentage_change': 0,
                    'trend': 'stable',
                    'price_history': []
                })
        
        return JsonResponse({'prices': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@account_type_required('admin', 'farmer')
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
@account_type_required('admin', 'farmer')
def price_list(request):
    market_url = reverse('market:market') + '#prices'
    return HttpResponsePermanentRedirect(market_url)

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
@account_type_required('admin', 'farmer')
def offer_list(request):
    # Complete with filter and pagination
    query = request.GET.get('q')
    status = request.GET.get('status')
    crop = request.GET.get('crop')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Admin sees all offers, farmers see only their own
    if request.user.account_type == 'admin':
        offers = BuyerOffer.objects.all().order_by('-date_offered')
    else:
        # Get user's crops for filtering offers
        from crops.models import Crop
        user_crop_ids = Crop.objects.filter(user=request.user).values_list('id', flat=True)
        # Filter offers: only show offers for this farmer's crops
        offers = BuyerOffer.objects.filter(farmer=request.user).order_by('-date_offered')
    
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
    my_offers = BuyerOffer.objects.filter(buyer_name=request.user.username).order_by('-date_offered')
    paginator = Paginator(my_offers, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'buyer_dashboard.html', {'offers': page_obj})

@login_required
def offer_add(request):
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.buyer_name = request.user.username
            offer.save()
            messages.success(request, 'Offer created!')
            return redirect('market:offer_list')
    form = BuyerOfferForm()
    return render(request, 'market_offer_form.html', {'form': form, 'action': 'Add'})

@login_required
def offer_edit(request, offer_id):
    """Premium: Edit buyer offer with form validation."""
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
