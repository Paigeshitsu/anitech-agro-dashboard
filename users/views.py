import secrets
import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg
from django.db.models import Sum

# Forms
from .forms import SignupForm, LoginForm, ProfileForm

# Model Imports
from notifications.models import OTPToken, ActivityLog, Notification, AdminAnnouncement
from crops.models import Crop
from market.models import BuyerOffer, MarketPrice, ScheduleDistribution

# ML Service Imports
from ml_service.views import get_model
from ml_service.model import predict_top_k

# --- AUTHENTICATION VIEWS ---

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            otp = ''.join(secrets.choice('0123456789') for _ in range(6))
            OTPToken.objects.create(
                user=user, 
                otp_code=otp, 
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            send_mail(
                'Your ANITECH OTP Code',
                f'Your OTP code is {otp}. It expires in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Account created. Check your email for OTP.')
            return redirect('verify_otp', user_id=user.id)
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user and user.account_type == form.cleaned_data['account_type']:
                login(request, user)
                ActivityLog.objects.create(user=user, activity='Logged In', details='User logged in successfully', ip_address=request.META.get('REMOTE_ADDR'))
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or account type.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, activity='Logged Out', details='User logged out successfully', ip_address=request.META.get('REMOTE_ADDR'))
    logout(request)
    return redirect('home')

def verify_otp_view(request, user_id):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            token = OTPToken.objects.get(user_id=user_id, otp_code=otp, expires_at__gt=timezone.now())
            user = token.user
            user.is_verified = True
            user.save()
            token.delete()
            messages.success(request, 'Account verified. Please login.')
            return redirect('login')
        except OTPToken.DoesNotExist:
            messages.error(request, 'Invalid or expired OTP.')
    return render(request, 'verify_otp.html', {'user_id': user_id})

# --- OPTIMIZED DASHBOARD VIEW (MATCHES YOUR SCREENSHOTS) ---

@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'today': timezone.now().date(),
    }

    # 1. ML PREDICTIONS (For the Grid Cards)
    try:
        model = get_model()
        default_payload = {
            "location": "Central Luzon", 
            "season": "Dry",
            "ph": 6.5,
            "rainfall": 100,
            "temperature": 28,
            "humidity": 70
        }
        # Get 8 predictions to fill the grid in your screenshot
        context['predictions'] = predict_top_k(model, default_payload, k=8)
    except Exception as e:
        context['ml_error'] = str(e)

    # 2. MARKET PRICE TREND DATA (For the Line Chart)
    market_data = MarketPrice.objects.values('crop_name').annotate(avg_price=Avg('price')).order_by('crop_name')
    # Convert Decimal to float for JSON serialization
    market_data_list = []
    for item in market_data:
        market_data_list.append({
            'crop_name': item['crop_name'],
            'avg_price': float(item['avg_price']) if item['avg_price'] else None
        })
    context['market_trends_json'] = json.dumps(market_data_list)

    # 3. ROLE-BASED DATA FETCHING
    if user.account_type == 'farmer':
        context['my_crops'] = Crop.objects.filter(user=user).order_by('-created_at')[:5]
        context['crops'] = context['my_crops']  # Also set crops for template compatibility
        context['recent_offers'] = BuyerOffer.objects.all().order_by('-date_offered')[:5]
        
    elif user.account_type == 'admin':
        context['total_crops_count'] = Crop.objects.count()
        context['pending_offers_count'] = BuyerOffer.objects.filter(status='Pending').count()
        context['crops'] = Crop.objects.select_related('user').order_by('-created_at')[:10]
        context['offers'] = BuyerOffer.objects.all().order_by('-date_offered')[:10]
        context['schedules'] = ScheduleDistribution.objects.all().order_by('scheduled_date')[:5]
    
    # For other user types (buyer, secretary), also provide crops
    else:
        context['crops'] = Crop.objects.all().order_by('-created_at')[:10]

    # 4. WEATHER MOCK DATA
    context['weather_forecast'] = [
        {'day': 'Mon', 'temp': 28, 'condition': 'Partly Cloudy'},
        {'day': 'Tue', 'temp': 29, 'condition': 'Sunny'},
        {'day': 'Wed', 'temp': 27, 'condition': 'Rainy'},
        {'day': 'Thu', 'temp': 28, 'condition': 'Cloudy'},
        {'day': 'Fri', 'temp': 30, 'condition': 'Sunny'},
    ]

    return render(request, 'dashboard.html', context)

# --- ADDITIONAL VIEWS ---

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'profile.html', {'form': form})


@login_required
def crops_view(request):
    if request.user.account_type == 'admin':
        crops = Crop.objects.select_related('user').order_by('-created_at')
    else:
        crops = Crop.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'crops.html', {'crops': crops})


@login_required
def market_view(request):
    market_prices = MarketPrice.objects.all().order_by('-date')[:20]
    offers = BuyerOffer.objects.all().order_by('-date_offered')[:20]
    return render(request, 'market.html', {
        'market_prices': market_prices,
        'offers': offers
    })

@login_required
def admin_report_view(request):
    if request.user.account_type != 'admin':
        return redirect('dashboard')
    
    # PHP-style aggregation logic
    stats = {
        'total_revenue': SaleRecord.objects.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        'total_crops': Crop.objects.count(),
        'inventory_status': Inventory.objects.all(),
        'recent_sales': SaleRecord.objects.select_related('crop', 'buyer').order_by('-sale_date')[:10]
    }
    
    return render(request, 'admin_report.html', stats)