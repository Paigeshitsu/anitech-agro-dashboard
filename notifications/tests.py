from django.test import TestCase
from django.contrib.auth import get_user_model
from notifications.models import Notification, ActivityLog, AdminAnnouncement, OTPToken, TranslationCache
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )

    def test_notification_creation(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='This is a test notification',
            type='info'
        )
        self.assertEqual(notification.title, 'Test Notification')
        self.assertEqual(notification.message, 'This is a test notification')
        self.assertEqual(notification.type, 'info')
        self.assertFalse(notification.is_read)

    def test_notification_types(self):
        types = ['info', 'warning', 'error', 'success']
        for notif_type in types:
            notification = Notification.objects.create(
                user=self.user,
                title=f'Test {notif_type}',
                message=f'{notif_type} notification',
                type=notif_type
            )
            self.assertEqual(notification.type, notif_type)

    def test_notification_mark_as_read(self):
        notification = Notification.objects.create(
            user=self.user,
            title='Test',
            message='Message',
            type='info',
            is_read=False
        )
        notification.is_read = True
        notification.save()
        self.assertTrue(notification.is_read)

class ActivityLogModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )

    def test_activity_log_creation(self):
        activity_log = ActivityLog.objects.create(
            user=self.user,
            activity='Logged In',
            details='User logged in via web interface',
            ip_address='192.168.1.1'
        )
        self.assertEqual(activity_log.activity, 'Logged In')
        self.assertEqual(activity_log.details, 'User logged in via web interface')
        self.assertEqual(activity_log.ip_address, '192.168.1.1')

    def test_activity_log_without_ip(self):
        activity_log = ActivityLog.objects.create(
            user=self.user,
            activity='Logged Out',
            details='User logged out'
        )
        self.assertIsNone(activity_log.ip_address)

    def test_multiple_activities_per_user(self):
        ActivityLog.objects.create(
            user=self.user,
            activity='Logged In',
            ip_address='192.168.1.1'
        )
        ActivityLog.objects.create(
            user=self.user,
            activity='Viewed Profile',
            ip_address='192.168.1.1'
        )
        ActivityLog.objects.create(
            user=self.user,
            activity='Logged Out',
            ip_address='192.168.1.1'
        )
        self.assertEqual(self.user.activitylog_set.count(), 3)

class AdminAnnouncementModelTest(TestCase):
    def test_announcement_creation(self):
        announcement = AdminAnnouncement.objects.create(
            title='System Maintenance',
            message='The system will be down for maintenance on Sunday.',
            expiry_date=timezone.now().date() + timedelta(days=7)
        )
        self.assertEqual(announcement.title, 'System Maintenance')
        self.assertEqual(announcement.message, 'The system will be down for maintenance on Sunday.')
        self.assertIsNotNone(announcement.created_at)

    def test_announcement_without_expiry(self):
        announcement = AdminAnnouncement.objects.create(
            title='Important Notice',
            message='Please update your profile information.'
        )
        self.assertIsNone(announcement.expiry_date)

    def test_multiple_announcements(self):
        for i in range(3):
            AdminAnnouncement.objects.create(
                title=f'Announcement {i}',
                message=f'Message {i}'
            )
        self.assertEqual(AdminAnnouncement.objects.count(), 3)

class OTPTokenModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )

    def test_otp_token_creation(self):
        otp_token = OTPToken.objects.create(
            user=self.user,
            otp_code='123456',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertEqual(otp_token.user, self.user)
        self.assertEqual(otp_token.otp_code, '123456')
        self.assertIsNotNone(otp_token.created_at)

    def test_otp_token_expiration(self):
        otp_token = OTPToken.objects.create(
            user=self.user,
            otp_code='654321',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertGreater(otp_token.expires_at, timezone.now())

    def test_otp_token_expired(self):
        otp_token = OTPToken.objects.create(
            user=self.user,
            otp_code='111111',
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        self.assertLess(otp_token.expires_at, timezone.now())

    def test_multiple_otp_tokens_per_user(self):
        OTPToken.objects.create(
            user=self.user,
            otp_code='111111',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        OTPToken.objects.create(
            user=self.user,
            otp_code='222222',
            expires_at=timezone.now() + timedelta(minutes=5)
        )
        self.assertEqual(self.user.otptoken_set.count(), 2)

class TranslationCacheModelTest(TestCase):
    def test_translation_cache_creation(self):
        cache = TranslationCache.objects.create(
            source_text='Hello World',
            source_lang='en',
            target_lang='es',
            translated_text='Hola Mundo'
        )
        self.assertEqual(cache.source_text, 'Hello World')
        self.assertEqual(cache.source_lang, 'en')
        self.assertEqual(cache.target_lang, 'es')
        self.assertEqual(cache.translated_text, 'Hola Mundo')

    def test_translation_cache_uniqueness(self):
        TranslationCache.objects.create(
            source_text='Hello World',
            source_lang='en',
            target_lang='es',
            translated_text='Hola Mundo'
        )
        # Attempt to create duplicate
        with self.assertRaises(Exception):
            TranslationCache.objects.create(
                source_text='Hello World',
                source_lang='en',
                target_lang='es',
                translated_text='Hola Mundo'
            )

    def test_multiple_translations_same_source(self):
        TranslationCache.objects.create(
            source_text='Hello World',
            source_lang='en',
            target_lang='es',
            translated_text='Hola Mundo'
        )
        TranslationCache.objects.create(
            source_text='Hello World',
            source_lang='en',
            target_lang='fr',
            translated_text='Bonjour le monde'
        )
        self.assertEqual(
            TranslationCache.objects.filter(source_text='Hello World').count(), 
            2
        )
