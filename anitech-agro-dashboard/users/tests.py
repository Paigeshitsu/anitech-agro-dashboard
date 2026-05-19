from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from users.models import User
from notifications.models import OTPToken, ActivityLog
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from activity_log.models import ActivityLog as AuditLog
from unittest.mock import patch
from anitech.utils import get_crop_name

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
        self.assertFalse(user.is_verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('OTP code is', mail.outbox[0].body)

    def test_login_view_rejects_unverified_user(self):
        User.objects.create_user(
            username='pendinguser',
            email='pending@example.com',
            password='StrongPass123!',
            account_type='farmer',
            is_verified=False,
        )

        response = self.client.post(self.login_url, {
            'username': 'pendinguser',
            'password': 'StrongPass123!',
            'account_type': 'farmer'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'not verified yet')

    @patch('users.views.send_mail', side_effect=Exception('smtp failed'))
    def test_signup_redirects_to_otp_when_email_send_raises(self, _mock_send_mail):
        response = self.client.post(self.signup_url, {
            'username': 'smtpuser',
            'name': 'SMTP User',
            'email': 'smtp@example.com',
            'account_type': 'farmer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='smtpuser')
        self.assertFalse(user.is_verified)
        self.assertTrue(OTPToken.objects.filter(user=user).exists())
        self.assertContains(response, 'Account created. Email delivery could not be confirmed.')

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

    def test_signup_duplicate_username_recovers_pending_account(self):
        pending = User.objects.create_user(
            username='pendingexisting',
            email='pendingexisting@example.com',
            password='OldPass123!',
            account_type='farmer',
            is_verified=False,
        )

        response = self.client.post(self.signup_url, {
            'username': 'pendingexisting',
            'name': 'Updated Pending User',
            'email': 'pendingexisting@example.com',
            'account_type': 'buyer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/auth/verify-otp/{pending.id}/')
        pending.refresh_from_db()
        self.assertEqual(pending.first_name, 'Updated Pending User')
        self.assertEqual(pending.account_type, 'buyer')
        self.assertTrue(pending.check_password('StrongPass123!'))
        self.assertEqual(OTPToken.objects.filter(user=pending).count(), 1)

    @patch('users.views.send_mail')
    def test_resend_otp_view_replaces_old_token(self, mock_send_mail):
        user = User.objects.create_user(
            username='resenduser',
            email='resend@example.com',
            password='StrongPass123!',
            account_type='farmer',
            is_verified=False,
        )
        old_token = OTPToken.objects.create(
            user=user,
            otp_code='123456',
            expires_at=timezone.now() + timezone.timedelta(minutes=5),
        )

        response = self.client.get(f'/auth/verify-otp/{user.id}/resend/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f'/auth/verify-otp/{user.id}/')
        self.assertFalse(OTPToken.objects.filter(id=old_token.id).exists())
        self.assertEqual(OTPToken.objects.filter(user=user).count(), 1)
        mock_send_mail.assert_called_once()

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
        self.assertEqual(response.url, '/dashboard/')

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

    def test_set_language_updates_authenticated_user_preference(self):
        user = User.objects.create_user(
            username='langbuyer',
            email='langbuyer@example.com',
            password='StrongPass123!',
            account_type='buyer',
            language='English',
        )
        self.client.login(username='langbuyer', password='StrongPass123!')

        response = self.client.post(reverse('set_language'), {'language': 'tl'})

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.language, 'Tagalog')

    def test_buyer_activity_log_page_shows_only_own_logs(self):
        buyer = User.objects.create_user(
            username='buyer1',
            email='buyer1@example.com',
            password='StrongPass123!',
            account_type='buyer',
        )
        other_buyer = User.objects.create_user(
            username='buyer2',
            email='buyer2@example.com',
            password='StrongPass123!',
            account_type='buyer',
        )

        AuditLog.objects.create(user=buyer, username=buyer.username, event_type='create', action='Buyer One Action')
        AuditLog.objects.create(user=other_buyer, username=other_buyer.username, event_type='create', action='Buyer Two Action')

        self.client.login(username='buyer1', password='StrongPass123!')
        response = self.client.get(reverse('activity_log:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buyer One Action')
        self.assertNotContains(response, 'Buyer Two Action')

    def test_crop_translation_normalizes_language_and_capitalization(self):
        self.assertEqual(get_crop_name('talong', 'en'), 'Eggplant')
        self.assertEqual(get_crop_name('eggplant', 'tl'), 'Talong')
        self.assertEqual(get_crop_name('red onion', 'tl'), 'Pulang Sibuyas')
