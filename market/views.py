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

@login_required
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
    """POST /market/forecast/ - Legacy PHP mock forecasts for JS."""
    try:
        data = json.loads(request.body)
        crops = data.get('crops', [])
        if not crops:
            crop_name = data.get('crop_name', '')
            if crop_name:
                crops = [crop_name]
        
        results = []
        for crop_name in crops:
            crop_name = crop_name.strip()
            if not crop_name:
                continue
            
            latest_price = MarketPrice.objects.filter(crop_name__iexact=crop_name).order_by('-last_updated').first()
            current_price = latest_price.current_price if latest_price else 30.0
            
            forecast_change = random.uniform(-10, 15)
            forecast_price = current_price * (1 + forecast_change / 100)
            trend = 'rising' if forecast_change > 2 else ('falling' if forecast_change < -2 else 'stable')
            
            results.append({
                'crop': crop_name,
                'current_price': float(current_price),
                'forecast_price': round(float(forecast_price), 2),
                'percentage_change': round(forecast_change, 2),
                'trend': trend
            })
        
        return JsonResponse({'prices': results})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def market_view(request):
    total_prices = MarketPrice.objects.count()
    total_offers = BuyerOffer.objects.count() + SellerOffer.objects.count()
    pending_offers = BuyerOffer.objects.filter(status='Pending').count()
    
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_prices = MarketPrice.objects.filter(date__gte=seven_days_ago)
    avg_price_7d = recent_prices.aggregate(avg=Avg('current_price'))['avg']
    
    market_prices = MarketPrice.objects.all().order_by('-last_updated')
    offers = BuyerOffer.objects.filter(status='Pending').order_by('-date_offered')[:10]
    
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
def offer_list(request):
    # Complete with filter and pagination
    query = request.GET.get('q')
    offers = BuyerOffer.objects.all().order_by('-date_offered')
    if query:
        offers = offers.filter(
            Q(crop_name__icontains=query) | Q(buyer_name__icontains=query)
        )
    paginator = Paginator(offers, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'market_offer_list.html', {'offers': page_obj, 'query': query})

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
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can add schedules.')
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
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can edit schedules.')
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
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete schedules.')
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
