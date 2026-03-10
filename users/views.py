import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings

# Forms
from .forms import SignupForm, LoginForm, ProfileForm

# Model Imports (Moved to top for performance)
from notifications.models import OTPToken, ActivityLog, Notification, AdminAnnouncement
from crops.models import Crop
from market.models import BuyerOffer, MarketPrice, ScheduleDistribution

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Optimization: Secure OTP generation
            otp = ''.join(secrets.choice('0123456789') for _ in range(6))
            
            OTPToken.objects.create(
                user=user, 
                otp_code=otp, 
                expires_at=timezone.now() + timedelta(minutes=5)
            )
            
            # Send OTP email
            send_mail(
                'Your ANITECH OTP Code',
                f'Your OTP code is {otp}. It expires in 5 minutes.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, 'Account created. Please check your email for the OTP code.')
            return redirect('verify_otp', user_id=user.id)
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'], 
                password=form.cleaned_data['password']
            )
            if user and user.account_type == form.cleaned_data['account_type']:
                login(request, user)
                # Log Activity
                ActivityLog.objects.create(
                    user=user, 
                    activity='Logged In', 
                    details='User logged in successfully', 
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid credentials or account type.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user, 
            activity='Logged Out', 
            details='User logged out successfully', 
            ip_address=request.META.get('REMOTE_ADDR')
        )
    logout(request)
    return redirect('home')

def verify_otp_view(request, user_id):
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            # Query optimization: check expiration and code in one go
            token = OTPToken.objects.get(
                user_id=user_id, 
                otp_code=otp, 
                expires_at__gt=timezone.now()
            )
            user = token.user
            user.is_verified = True
            user.save()
            token.delete()
            messages.success(request, 'Account verified. Please login.')
            return redirect('login')
        except OTPToken.DoesNotExist:
            messages.error(request, 'Invalid or expired OTP.')
    return render(request, 'verify_otp.html', {'user_id': user_id})

@login_required
def dashboard_view(request):
    context = {'user': request.user}
    user_type = request.user.account_type

    # ROLE: FARMER
    if user_type == 'farmer':
        # select_related avoids separate query for the user object in templates
        context['crops'] = Crop.objects.filter(user=request.user).order_by('-created_at')

    # ROLE: BUYER
    elif user_type == 'buyer':
        context['offers'] = BuyerOffer.objects.filter(buyer=request.user).order_by('-created_at')

    # ROLE: ADMIN (Heaviest View - Needs strict optimization)
    elif user_type == 'admin':
        # Optimization: select_related('user') and order_by prevents N+1 and erratic lists
        context['crops'] = Crop.objects.select_related('user').order_by('-created_at')[:10]
        context['offers'] = BuyerOffer.objects.select_related('buyer').order_by('-created_at')[:10]
        context['market_prices'] = MarketPrice.objects.all().order_by('-date')
        context['notifications'] = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

    # ROLE: SECRETARY
    elif user_type == 'secretary':
        context['schedules'] = ScheduleDistribution.objects.all().order_by('date')
        context['announcements'] = AdminAnnouncement.objects.all().order_by('-created_at')
        context['notifications'] = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

    return render(request, 'dashboard.html', context)

@login_required
def notifications_view(request):
    # Standard ordering by latest
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def crops_view(request):
    user_type = request.user.account_type
    
    if user_type == 'farmer':
        crops = Crop.objects.filter(user=request.user).order_by('-created_at')
    elif user_type == 'admin':
        # select_related('user') is critical here to show owner names without 20 extra queries
        crops = Crop.objects.select_related('user').all().order_by('-created_at')[:50]
    else:
        crops = []
        
    return render(request, 'crops.html', {'crops': crops})

@login_required
def market_view(request):
    market_prices = MarketPrice.objects.all().order_by('-date')
    
    if request.user.account_type == 'buyer':
        offers = BuyerOffer.objects.filter(buyer=request.user).order_by('-date_offered')
    else:
        offers = []
        
    return render(request, 'market.html', {'market_prices': market_prices, 'offers': offers})

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