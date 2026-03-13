from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from .models import MarketPrice, BuyerOffer, ScheduleDistribution, SellerOffer, Crop
from .forms import MarketPriceForm, BuyerOfferForm, ScheduleDistributionForm, SellerOfferForm
from django.urls import reverse
from django.http import HttpResponsePermanentRedirect

@login_required
def market_view(request):
    """Main market view showing prices and offers"""
    total_prices = MarketPrice.objects.count()
    total_offers = BuyerOffer.objects.count() + SellerOffer.objects.count()
    pending_offers = BuyerOffer.objects.filter(status='Pending').count()
    
    seven_days_ago = timezone.now().date() - timedelta(days=7)
    recent_prices = MarketPrice.objects.filter(date__gte=seven_days_ago)
    avg_price_7d = recent_prices.aggregate(avg=Avg('price'))['avg']
    
    market_prices = MarketPrice.objects.all().order_by('-date')
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

# ============ Market Price CRUD (Original) ============

@login_required
def price_list(request):
    """Redirect to main market page with prices tab active"""
    from django.http import HttpResponsePermanentRedirect
    import urllib.parse
    market_url = reverse('market:market')
    redirect_url = market_url + '#prices'
    return HttpResponsePermanentRedirect(redirect_url)

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
    else:
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
    else:
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

# ============ Buyer Offer CRUD + Legacy Filters ============

@login_required
def offer_list(request):
    offers = BuyerOffer.objects.all().order_by('-date_offered')
    
    # User filtering
    if request.user.account_type == 'buyer':
        offers = offers.filter(buyer_name=request.user.username)
    elif request.user.account_type == 'farmer':
        offers = offers.filter(farmer=request.user)
    
    # Legacy filters
    status = request.GET.get('status')
    crop_query = request.GET.get('crop')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if status:
        offers = offers.filter(status=status)
    if crop_query:
        offers = offers.filter(Q(crop_name__icontains=crop_query) | Q(crop__crop_name__icontains=crop_query))
    if min_price:
        offers = offers.filter(offer_price__gte=float(min_price))
    if max_price:
        offers = offers.filter(offer_price__lte=float(max_price))
    if date_from:
        offers = offers.filter(date_offered__gte=date_from)
    if date_to:
        offers = offers.filter(date_offered__lte=date_to)

    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'market_offer_list.html', {
        'offers': page_obj,
        'page_obj': page_obj,
        'filters': request.GET,
    })

@login_required
def buyer_dashboard(request):
    if request.user.account_type != 'buyer':
        return redirect('market')
    my_offers = BuyerOffer.objects.filter(buyer_name=request.user.username).order_by('-date_offered')
    paginator = Paginator(my_offers, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'buyer_dashboard.html', {'offers': page_obj, 'page_obj': page_obj})

@login_required
def offer_add(request):
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            if request.user.account_type == 'buyer':
                offer.buyer_name = request.user.username
            offer.save()
            messages.success(request, 'Offer created successfully!')
            return redirect('market')
    else:
        form = BuyerOfferForm(initial={'buyer_name': request.user.username if request.user.account_type == 'buyer' else ''})
    return render(request, 'market_offer_form.html', {'form': form, 'action': 'Add'})

@login_required
def offer_edit(request, offer_id):
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    if request.user.account_type == 'buyer' and offer.buyer_name != request.user.username:
        messages.error(request, 'You can only edit your own offers.')
        return redirect('market')
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('market')
    else:
        form = BuyerOfferForm(instance=offer)
    return render(request, 'market_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def offer_delete(request, offer_id):
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    if request.user.account_type == 'buyer' and offer.buyer_name != request.user.username:
        messages.error(request, 'You can only delete your own offers.')
        return redirect('market')
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Offer deleted successfully!')
        return redirect('market')
    return render(request, 'market_offer_confirm_delete.html', {'offer': offer})

@login_required
def offer_update_status(request, offer_id):
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    if request.user.account_type not in ['farmer', 'admin']:
        messages.error(request, 'You do not have permission.')
        return redirect('market')
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Accepted', 'Rejected']:
            offer.status = new_status
            offer.save()
            messages.success(request, f'Offer status updated to {new_status}!')
    return redirect('market:offer_list')

# ============ Seller Offer CRUD (Legacy) ============

@login_required
def seller_offer_list(request):
    if request.user.account_type == 'farmer':
        offers = SellerOffer.objects.filter(farmer=request.user).order_by('-date_posted')
    else:
        offers = SellerOffer.objects.all().order_by('-date_posted')
    paginator = Paginator(offers, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'sell_offer_list.html', {'page_obj': page_obj})

@login_required
def seller_offer_add(request):
    if request.user.account_type != 'farmer':
        messages.error(request, 'Only farmers can post sell offers.')
        return redirect('market')
    if request.method == 'POST':
        form = SellerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.farmer = request.user
            offer.save()
            messages.success(request, 'Sell offer posted successfully!')
            return redirect('market:seller_offer_list')
    else:
        form = SellerOfferForm()
    return render(request, 'sell_offer_form.html', {'form': form, 'action': 'Post'})

@login_required
def seller_offer_edit(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id)
    if request.user.account_type != 'farmer' or offer.farmer != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('market:seller_offer_list')
    if request.method == 'POST':
        form = SellerOfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sell offer updated!')
            return redirect('market:seller_offer_list')
    else:
        form = SellerOfferForm(instance=offer)
    return render(request, 'sell_offer_form.html', {'form': form, 'offer': offer, 'action': 'Edit'})

@login_required
def seller_offer_delete(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id)
    if request.user.account_type != 'farmer' or offer.farmer != request.user:
        messages.error(request, 'Permission denied.')
        return redirect('market:seller_offer_list')
    if request.method == 'POST':
        offer.delete()
        messages.success(request, 'Sell offer deleted!')
        return redirect('market:seller_offer_list')
    return render(request, 'sell_offer_confirm_delete.html', {'offer': offer})

@login_required
def seller_offer_update_status(request, offer_id):
    offer = get_object_or_404(SellerOffer, id=offer_id)
    if request.user.account_type not in ['buyer', 'admin']:
        messages.error(request, 'Permission denied.')
        return redirect('market:seller_offer_list')
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Accepted', 'Rejected']:
            offer.status = new_status
            offer.save()
            messages.success(request, f'Sell offer status updated to {new_status}!')
    return redirect('market:seller_offer_list')

# ============ Schedule Distribution CRUD (Original) ============

@login_required
def schedule_list(request):
    from users.views import schedule_view
    return schedule_view(request)

@login_required
def schedule_add(request):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can add schedules.')
        return redirect('schedule')
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule added successfully!')
            return redirect('schedule')
    else:
        form = ScheduleDistributionForm()
    return render(request, 'schedule_form.html', {'form': form, 'action': 'Add'})

@login_required
def schedule_edit(request, schedule_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can edit schedules.')
        return redirect('schedule')
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    if request.method == 'POST':
        form = ScheduleDistributionForm(request.POST, instance=schedule)
        if form.is_valid():
            form.save()
            messages.success(request, 'Schedule updated successfully!')
            return redirect('schedule')
    else:
        form = ScheduleDistributionForm(instance=schedule)
    return render(request, 'schedule_form.html', {'form': form, 'schedule': schedule, 'action': 'Edit'})

@login_required
def schedule_delete(request, schedule_id):
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete schedules.')
        return redirect('schedule')
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully!')
        return redirect('schedule')
    return render(request, 'schedule_confirm_delete.html', {'schedule': schedule})

