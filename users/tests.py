from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from users.models import User
from notifications.models import OTPToken, ActivityLog
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.account_type, 'farmer')
        self.assertTrue(user.is_verified)

    def test_user_account_types(self):
        for account_type in ['admin', 'secretary', 'farmer', 'buyer']:
            user = User.objects.create_user(
                username=f'user_{account_type}',
                email=f'{account_type}@example.com',
                password='StrongPass123!',
                account_type=account_type
            )
            self.assertEqual(user.account_type, account_type)

    def test_user_phone_and_carrier(self):
        user = User.objects.create_user(
            username='phoneuser',
            email='phone@example.com',
            password='StrongPass123!',
            account_type='farmer',
            phone='1234567890',
            carrier='Verizon'
        )
        self.assertEqual(user.phone, '1234567890')
        self.assertEqual(user.carrier, 'Verizon')

class UserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = '/auth/signup/'
        self.login_url = '/auth/login/'
        self.logout_url = '/auth/logout/'

    def test_signup_view(self):
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'account_type': 'farmer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to verify OTP
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.account_type, 'farmer')

    def test_signup_duplicate_username(self):
        # Create first user
        User.objects.create_user(
            username='existing',
            email='existing@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        # Try to create duplicate
        response = self.client.post(self.signup_url, {
            'username': 'existing',
            'name': 'Duplicate User',
            'email': 'dup@example.com',
            'account_type': 'farmer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)  # Form reloaded with error
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_signup_invalid_email(self):
        response = self.client.post(self.signup_url, {
            'username': 'testuser',
            'name': 'Test User',
            'email': 'invalid-email',
            'account_type': 'farmer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })
        self.assertEqual(response.status_code, 200)  # Form reloaded with error
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_login_view_valid_credentials(self):
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongPass123!',
            'account_type': 'farmer'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard
        self.assertEqual(response.url, '/auth/dashboard/')

    def test_login_view_invalid_password(self):
        # Create user
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword',
            'account_type': 'farmer'
        })
        self.assertEqual(response.status_code, 200)  # Form reloaded with error

    def test_login_view_wrong_account_type(self):
        # Create farmer user
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        # Try to login as admin
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongPass123!',
            'account_type': 'admin'
        })
        self.assertEqual(response.status_code, 200)  # Form reloaded with error

    def test_logout_view(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        self.client.login(username='testuser', password='StrongPass123!')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)  # Redirect to home
        self.assertEqual(response.url, '/')
        # Verify activity log was created
        self.assertTrue(ActivityLog.objects.filter(user=user, activity='Logged Out').exists())

    def test_otp_token_creation(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        otp_token = OTPToken.objects.create(
            user=user,
            otp_code='123456',
            expires_at=timezone.now() + timezone.timedelta(minutes=5)
        )
        self.assertEqual(otp_token.user, user)
        self.assertEqual(otp_token.otp_code, '123456')
        self.assertTrue(otp_token.created_at is not None)
