import secrets
import json
import random
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg, Sum
from django.db import transaction
from django.core.cache import cache

# Forms
from .forms import SignupForm, LoginForm, ProfileForm

# Model Imports
from notifications.models import OTPToken, ActivityLog, Notification, AdminAnnouncement
from crops.models import Crop
from market.models import BuyerOffer, MarketPrice, ScheduleDistribution
from .models import User

# ML Service Imports
from ml_service.views import get_model
# from ml_service.model import predict_top_k  (lazy loaded)

# --- AUTHENTICATION ---

logger = logging.getLogger(__name__)


def issue_signup_otp(user):
    otp = ''.join(secrets.choice('0123456789') for _ in range(6))
    OTPToken.objects.filter(user=user).delete()
    OTPToken.objects.create(
        user=user,
        otp_code=otp,
        expires_at=timezone.now() + timedelta(minutes=5),
    )
    send_mail(
        'Your ANITECH OTP Code',
        f'Your OTP code is {otp}. It expires in 5 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

def signup_view(request):
    if request.method == 'POST':
        existing_user = User.objects.filter(username=request.POST.get('username', '').strip()).first()
        submitted_email = request.POST.get('email', '').strip()

        if existing_user and not existing_user.is_verified and submitted_email and existing_user.email == submitted_email:
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            if password1 and password1 == password2:
                existing_user.first_name = request.POST.get('name', '').strip()
                existing_user.phone = request.POST.get('phone', '').strip()
                existing_user.account_type = request.POST.get('account_type', existing_user.account_type)
                existing_user.email = submitted_email
                existing_user.set_password(password1)
                existing_user.save()

                try:
                    issue_signup_otp(existing_user)
                    messages.success(request, 'Your pending account already exists. We sent a new OTP to your email.')
                except Exception:
                    logger.exception('OTP resend failed for user_id=%s email=%s during signup recovery', existing_user.id, existing_user.email)
                    messages.warning(
                        request,
                        'Your pending account already exists. Email delivery could not be confirmed. If you already received the OTP, enter it below.'
                    )
                return redirect('verify_otp', user_id=existing_user.id)

        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.is_verified = False
                    user.save()
            except Exception:
                messages.error(request, 'We could not create your account right now. Please try again.')
                return render(request, 'users/signup.html', {'form': form})

            try:
                issue_signup_otp(user)
                messages.success(request, 'Account created. Check email for OTP.')
            except Exception:
                logger.exception('OTP email send failed for user_id=%s email=%s', user.id, user.email)
                messages.warning(
                    request,
                    'Account created. Email delivery could not be confirmed. If you already received the OTP, enter it below.'
                )
                return redirect('verify_otp', user_id=user.id)

            return redirect('verify_otp', user_id=user.id)
        # Form has errors, render with the invalid form
        return render(request, 'users/signup.html', {'form': form})
    form = SignupForm()
    return render(request, 'users/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user and user.account_type == form.cleaned_data['account_type']:
                if not user.is_verified:
                    messages.error(request, 'Your account is not verified yet. Enter the OTP sent to your email first.')
                    return render(request, 'users/login.html', {'form': form})
                login(request, user)
                ActivityLog.objects.create(user=user, activity='Logged In', details='Success', ip_address=request.META.get('REMOTE_ADDR'))
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or account type mismatch.')
        # Form has errors, render with the invalid form
        return render(request, 'users/login.html', {'form': form})
    return render(request, 'users/login.html', {'form': LoginForm()})

def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(user=request.user, activity='Logged Out', details='Success')
    logout(request)
    return redirect('home')

def verify_otp_view(request, user_id):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        token = OTPToken.objects.filter(user_id=user_id, otp_code=otp, expires_at__gt=timezone.now()).first()
        if token:
            token.user.is_verified = True
            token.user.save()
            token.delete()
            messages.success(request, 'Verified! Please login.')
            return redirect('login')
        messages.error(request, 'Invalid/Expired OTP.')
    return render(request, 'users/verify_otp.html', {'user_id': user_id})


def resend_otp_view(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user.is_verified:
        messages.info(request, 'This account is already verified. Please log in.')
        return redirect('login')

    try:
        issue_signup_otp(user)
        messages.success(request, 'A new OTP has been sent to your email.')
    except Exception:
        logger.exception('OTP resend failed for user_id=%s email=%s', user.id, user.email)
        messages.error(request, 'We could not resend the OTP right now. Please try again.')

    return redirect('verify_otp', user_id=user.id)

# --- UNIVERSAL DASHBOARD VIEW ---

@login_required
def dashboard_view(request):
    user = request.user
    context = {
        'user': user,
        'today': timezone.now().date(),
        'stat_cards': [], # To be filled by role logic
    }

    # 1. ML PREDICTIONS (Shared across all dashboards)
    try:
        model = get_model()
        payload = {"location": "Central Luzon", "season": "Dry", "ph": 6.5, "rainfall": 100, "temperature": 28, "humidity": 70}
        from ml_service.model import predict_top_k
        context['predictions'] = predict_top_k(model, payload, k=8)
    except:
        context['predictions'] = []

    # 2. NOTIFICATIONS COUNT (Shared across all dashboards)
    context['notifications_count'] = Notification.objects.filter(user=user, is_read=False).count()

    # 2. MARKET TRENDS (Shared for Charts)
    market_qs = MarketPrice.objects.values('crop_name').annotate(avg_price=Avg('current_price')).order_by('crop_name')
    context['market_trends_json'] = json.dumps([{'crop': i['crop_name'], 'price': float(i['avg_price'])} for i in market_qs])

    # 3. ROLE-SPECIFIC STATS & TABLES
    if user.account_type == 'admin':
        accepted_revenue = BuyerOffer.objects.filter(status='Accepted').aggregate(Sum('offer_price'))['offer_price__sum'] or 0
        context['stat_cards'] = [
            {'title': 'Total Crops', 'value': Crop.objects.count(), 'icon': 'fa-seedling', 'color': 'green'},
            {'title': 'Pending Offers', 'value': BuyerOffer.objects.filter(status='Pending').count(), 'icon': 'fa-tags', 'color': 'orange'},
            {'title': 'Total Revenue', 'value': f"₱{accepted_revenue}", 'icon': 'fa-wallet', 'color': 'blue'},
        ]
        context['crops'] = Crop.objects.select_related('user').all()[:5]
        context['offers'] = BuyerOffer.objects.all().order_by('-date_offered')[:5]
        context['schedules'] = ScheduleDistribution.objects.all()[:5]

    elif user.account_type == 'farmer':
        my_crops_count = Crop.objects.filter(user=user).count()
        # Filter offers by farmer directly (not by crop name which could match other farmers' crops)
        context['stat_cards'] = [
            {'title': 'My Crops', 'value': my_crops_count, 'icon': 'fa-leaf', 'color': 'green'},
            {'title': 'Active Offers', 'value': BuyerOffer.objects.filter(farmer=user).count(), 'icon': 'fa-shopping-cart', 'color': 'blue'},
            {'title': 'Notifications', 'value': Notification.objects.filter(user=user, is_read=False).count(), 'icon': 'fa-bell', 'color': 'orange'},
        ]
        context['crops'] = Crop.objects.filter(user=user)[:5]
        context['offers'] = BuyerOffer.objects.filter(farmer=user)[:5]

    elif user.account_type == 'buyer':
        context['stat_cards'] = [
            {'title': 'My Offers', 'value': BuyerOffer.objects.filter(buyer_name=user.username).count(), 'icon': 'fa-hand-holding-usd', 'color': 'green'},
            {'title': 'Market Prices', 'value': MarketPrice.objects.count(), 'icon': 'fa-chart-line', 'color': 'blue'},
        ]
        context['market_prices'] = MarketPrice.objects.all()[:10]
        # Get available crops for buyers to make offers (cached for faster loading)
        from crops.models import Crop
        try:
            available_crops = cache.get('buyer_available_crops')
            if not available_crops:
                available_crops = Crop.objects.filter(status='available')[:10]
                cache.set('buyer_available_crops', available_crops, 300)  # Cache for 5 min
            context['available_crops'] = available_crops
        except:
            context['available_crops'] = Crop.objects.filter(status='available')[:10]

    # 4. WEATHER (Shared)
    context['weather_forecast'] = [
        {'day': 'Mon', 'temp': 28, 'condition': 'Sunny'},
        {'day': 'Tue', 'temp': 29, 'condition': 'Partly Cloudy'},
        {'day': 'Wed', 'temp': 27, 'condition': 'Rainy'},
    ]

    # Ensure available_crops is always defined
    if 'available_crops' not in context:
        context['available_crops'] = []

    return render(request, 'dashboard.html', context)

# --- OTHER VIEWS ---

@login_required
def crops_view(request):
    if request.user.account_type == 'admin':
        crops = Crop.objects.select_related('user').all()
    else:
        crops = Crop.objects.filter(user=request.user)
    return render(request, 'crops.html', {'crops': crops})

@login_required
def admin_report_view(request):
    if request.user.account_type != 'admin':
        return redirect('dashboard')
    stats = {
        'total_revenue': BuyerOffer.objects.filter(status='Accepted').aggregate(Sum('offer_price'))['offer_price__sum'] or 0,
        'total_crops': Crop.objects.count(),
        'recent_offers': BuyerOffer.objects.all().order_by('-date_offered')[:10]
    }
    return render(request, 'admin_report.html', stats)

# --- ADDITIONAL VIEWS ---

@login_required
def notifications_view(request):
    filter_type = request.GET.get('filter', 'all')
    
    if filter_type == 'unread':
        user_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    elif filter_type == 'read':
        user_notifications = Notification.objects.filter(user=request.user, is_read=True).order_by('-created_at')
    else:
        user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate counts
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    read_count = Notification.objects.filter(user=request.user, is_read=True).count()
    
    return render(request, 'users/notifications.html', {
        'notifications': user_notifications,
        'filter_type': filter_type,
        'unread_count': unread_count,
        'read_count': read_count,
    })

@login_required
def notifications_filter(request, filter_type):
    """Filter notifications by type (all, unread, read)"""
    if filter_type == 'unread':
        user_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    elif filter_type == 'read':
        user_notifications = Notification.objects.filter(user=request.user, is_read=True).order_by('-created_at')
    else:
        user_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate counts
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    read_count = Notification.objects.filter(user=request.user, is_read=True).count()
    
    return render(request, 'users/notifications.html', {
        'notifications': user_notifications,
        'filter_type': filter_type,
        'unread_count': unread_count,
        'read_count': read_count,
    })

@login_required
def notification_mark_read(request, notification_id):
    """Mark a single notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, 'Notification marked as read.')
    return redirect('notifications')

@login_required
def notifications_mark_all_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications')

@login_required
def notification_delete(request, notification_id):
    """Delete a notification"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    messages.success(request, 'Notification deleted.')
    return redirect('notifications')

@login_required
def market_view(request):
    market_prices = MarketPrice.objects.all().order_by('-date')[:20]
    offers = BuyerOffer.objects.all().order_by('-date_offered')[:20]
    return render(request, 'market.html', {
        'market_prices': market_prices,
        'offers': offers
    })

@login_required
def profile_view(request):
    user = request.user
    
    # Calculate stats
    from crops.models import Crop
    from market.models import BuyerOffer
    
    if user.account_type == 'admin':
        crops_count = Crop.objects.count()
        offers_count = BuyerOffer.objects.count()
    elif user.account_type == 'farmer':
        crops_count = Crop.objects.filter(user=user).count()
        my_crop_names = list(Crop.objects.filter(user=user).values_list('crop_name', flat=True))
        offers_count = BuyerOffer.objects.filter(crop_name__in=my_crop_names).count()
    elif user.account_type == 'buyer':
        crops_count = 0
        offers_count = BuyerOffer.objects.filter(buyer_name=user.username).count()
    else:
        crops_count = 0
        offers_count = 0
    
    # Handle profile form submission
    if request.method == 'POST':
        # Check which form was submitted
        if 'old_password' in request.POST:
            # Password change form
            from django.contrib.auth import update_session_auth_hash
            from django.contrib.auth.forms import PasswordChangeForm
            
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Password updated successfully!')
            else:
                for field, errors in password_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        else:
            # Profile update form
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profile updated successfully!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{error}')
        
        return redirect('profile')
    else:
        form = ProfileForm(instance=user)
    
    return render(request, 'profile.html', {
        'form': form,
        'crops_count': crops_count,
        'offers_count': offers_count,
    })

@login_required
def weather_view(request):
    """Weather forecast view"""
    from datetime import datetime
    
    # Set location to Legazpi City, Albay, Bicol Region
    user_location = "Legazpi City, Albay, Bicol Region"
    
    # Get current date and time
    now = datetime.now()
    current_date = now.strftime("%B %d, %Y")
    current_time = now.strftime("%I:%M %p")
    
    # Mock weather data (in production, this would call the ML service)
    current_weather = {
        'temperature': 28,
        'condition': 'Partly Cloudy',
        'location': user_location,
        'humidity': 75,
        'wind': 12,
        'feels_like': 30,
        'precipitation': 10,
        'date': current_date,
        'time': current_time,
    }
    
    forecast = [
        {'day': 'Today', 'temp': 28, 'condition': 'Partly Cloudy', 'icon': 'cloud-sun'},
        {'day': 'Mon', 'temp': 30, 'condition': 'Sunny', 'icon': 'sun'},
        {'day': 'Tue', 'temp': 29, 'condition': 'Partly Cloudy', 'icon': 'cloud-sun'},
        {'day': 'Wed', 'temp': 26, 'condition': 'Rainy', 'icon': 'cloud-rain'},
        {'day': 'Thu', 'temp': 27, 'condition': 'Cloudy', 'icon': 'cloud'},
        {'day': 'Fri', 'temp': 31, 'condition': 'Sunny', 'icon': 'sun'},
        {'day': 'Sat', 'temp': 29, 'condition': 'Partly Cloudy', 'icon': 'cloud-sun'},
    ]
    
    recommendations = [
        {'type': 'success', 'icon': 'check-circle', 'title': 'Good day for planting', 'message': 'The weather conditions are ideal for planting rice and vegetables.'},
        {'type': 'warning', 'icon': 'exclamation-triangle', 'title': 'Expect rain on Wednesday', 'message': 'Consider harvesting crops before the expected rainfall.'},
        {'type': 'info', 'icon': 'info-circle', 'title': 'Moderate humidity', 'message': 'Monitor crops for fungal diseases due to high humidity levels.'},
    ]
    
    return render(request, 'weather.html', {
        'current_weather': current_weather,
        'forecast': forecast,
        'recommendations': recommendations,
    })

@login_required
def schedule_view(request):
    """Schedule view for distribution and events"""
    from market.models import ScheduleDistribution
    
    # Get schedules based on user role
    if request.user.account_type == 'admin':
        # Admin sees all schedules
        schedules = ScheduleDistribution.objects.all().order_by('scheduled_date')
    else:
        # Non-admin users see all schedules (model doesn't have recipient field)
        schedules = ScheduleDistribution.objects.all().order_by('scheduled_date')
    
    return render(request, 'schedule.html', {
        'schedules': schedules,
    })
