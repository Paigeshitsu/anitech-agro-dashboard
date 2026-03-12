from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import MarketPrice, BuyerOffer, ScheduleDistribution
from .forms import MarketPriceForm, BuyerOfferForm, ScheduleDistributionForm

@login_required
def market_view(request):
    """Main market view showing prices and offers"""
    market_prices = MarketPrice.objects.all().order_by('-date')[:20]
    offers = BuyerOffer.objects.all().order_by('-date_offered')[:20]
    
    # Get language preference
    lang = request.session.get('lang', 'en')
    
    return render(request, 'market.html', {
        'market_prices': market_prices,
        'offers': offers,
        'lang': lang
    })

# ============ Market Price CRUD ============

@login_required
def price_list(request):
    """List all market prices - redirects to main market view"""
    return redirect('market')

@login_required
def price_add(request):
    """Add a new market price"""
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
    
    return render(request, 'market_price_form.html', {
        'form': form,
        'action': 'Add'
    })

@login_required
def price_edit(request, price_id):
    """Edit a market price"""
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
    
    return render(request, 'market_price_form.html', {
        'form': form,
        'price': price,
        'action': 'Edit'
    })

@login_required
def price_delete(request, price_id):
    """Delete a market price"""
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete market prices.')
        return redirect('market')
    
    price = get_object_or_404(MarketPrice, id=price_id)
    
    if request.method == 'POST':
        price.delete()
        messages.success(request, 'Market price deleted successfully!')
        return redirect('market')
    
    return render(request, 'market_price_confirm_delete.html', {'price': price})

# ============ Buyer Offer CRUD ============

@login_required
def offer_list(request):
    """List all buyer offers"""
    # Filter by user for non-admin
    if request.user.account_type == 'buyer':
        offers = BuyerOffer.objects.filter(buyer_name=request.user.username).order_by('-date_offered')
    elif request.user.account_type == 'farmer':
        # Get crops owned by farmer
        from crops.models import Crop
        farmer_crops = Crop.objects.filter(user=request.user).values_list('crop_name', flat=True)
        offers = BuyerOffer.objects.filter(crop_name__in=farmer_crops).order_by('-date_offered')
    else:
        offers = BuyerOffer.objects.all().order_by('-date_offered')
    
    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'market_offer_list.html', {
        'offers': page_obj,
        'page_obj': page_obj,
    })

@login_required
def offer_add(request):
    """Create a new buyer offer"""
    if request.method == 'POST':
        form = BuyerOfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            # Set buyer to current user if logged in as buyer
            if request.user.account_type == 'buyer':
                offer.buyer_name = request.user.username
            offer.save()
            messages.success(request, 'Offer created successfully!')
            return redirect('market')
    else:
        form = BuyerOfferForm()
        # Pre-fill buyer name if user is a buyer
        if request.user.account_type == 'buyer':
            form.initial['buyer_name'] = request.user.username
    
    return render(request, 'market_offer_form.html', {
        'form': form,
        'action': 'Add'
    })

@login_required
def offer_edit(request, offer_id):
    """Edit a buyer offer"""
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    
    # Check permission
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
    
    return render(request, 'market_offer_form.html', {
        'form': form,
        'offer': offer,
        'action': 'Edit'
    })

@login_required
def offer_delete(request, offer_id):
    """Delete a buyer offer"""
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    
    # Check permission
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
    """Update offer status (Accept/Reject) - for farmers/admin"""
    if request.user.account_type not in ['farmer', 'admin']:
        messages.error(request, 'You do not have permission to update offer status.')
        return redirect('market')
    
    offer = get_object_or_404(BuyerOffer, id=offer_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in ['Pending', 'Accepted', 'Rejected']:
            offer.status = new_status
            offer.save()
            messages.success(request, f'Offer status updated to {new_status}!')
        else:
            messages.error(request, 'Invalid status.')
    
    return redirect('market')

# ============ Schedule Distribution CRUD ============

@login_required
def schedule_list(request):
    """List all schedules - redirects to users schedule view"""
    from users.views import schedule_view
    return schedule_view(request)

@login_required
def schedule_add(request):
    """Add a new schedule distribution"""
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
    
    return render(request, 'schedule_form.html', {
        'form': form,
        'action': 'Add'
    })

@login_required
def schedule_edit(request, schedule_id):
    """Edit an existing schedule"""
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
    
    return render(request, 'schedule_form.html', {
        'form': form,
        'schedule': schedule,
        'action': 'Edit'
    })

@login_required
def schedule_delete(request, schedule_id):
    """Delete a schedule"""
    if request.user.account_type != 'admin':
        messages.error(request, 'Only admins can delete schedules.')
        return redirect('schedule')
    
    schedule = get_object_or_404(ScheduleDistribution, id=schedule_id)
    
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted successfully!')
        return redirect('schedule')
    
    return render(request, 'schedule_confirm_delete.html', {'schedule': schedule})

