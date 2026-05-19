from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from crops.models import Crop
from crops.views import (
    _build_recommendation_cards,
    _get_market_price_snapshot,
    _notify_admins_about_top_recommendation,
    _get_recommendation_crop_pool,
)
from django.utils import timezone
from decimal import Decimal
from market.models import MarketPrice
from notifications.models import Notification

User = get_user_model()

class CropModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='farmer1',
            email='farmer@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )

    def test_crop_creation(self):
        crop = Crop.objects.create(
            user=self.user,
            crop_name='Rice',
            price=Decimal('500.00'),
            quantity=Decimal('100.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date()
        )
        self.assertEqual(crop.crop_name, 'Rice')
        self.assertEqual(crop.quantity, Decimal('100.00'))
        self.assertEqual(crop.user, self.user)

    def test_crop_status_defaults_to_available(self):
        crop = Crop.objects.create(
            user=self.user,
            crop_name='Wheat',
            price=Decimal('400.00'),
            quantity=Decimal('50.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date()
        )
        self.assertEqual(crop.status, 'available')

    def test_multiple_crops_per_user(self):
        crop1 = Crop.objects.create(
            user=self.user,
            crop_name='Rice',
            price=Decimal('500.00'),
            quantity=Decimal('100.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date()
        )
        crop2 = Crop.objects.create(
            user=self.user,
            crop_name='Wheat',
            price=Decimal('400.00'),
            quantity=Decimal('50.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date()
        )
        self.assertEqual(self.user.crop_set.count(), 2)

    def test_crop_status_transitions(self):
        crop = Crop.objects.create(
            user=self.user,
            crop_name='Rice',
            price=Decimal('500.00'),
            quantity=Decimal('100.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date(),
            status='available'
        )
        self.assertEqual(crop.status, 'available')
        crop.status = 'reserved'
        crop.save()
        self.assertEqual(crop.status, 'reserved')

    def test_crop_with_grade_and_description(self):
        crop = Crop.objects.create(
            user=self.user,
            crop_name='Rice',
            price=Decimal('500.00'),
            quantity=Decimal('100.00'),
            harvest_date=timezone.now().date(),
            available_until=timezone.now().date(),
            grade='A1',
            description='High quality rice'
        )
        self.assertEqual(crop.grade, 'A1')
        self.assertEqual(crop.description, 'High quality rice')


class CropRecommendationCurationTest(TestCase):
    def test_recommendation_pool_prefers_market_price_crops_and_normalizes_aliases(self):
        MarketPrice.objects.create(crop_name='Sitaw', current_price=Decimal('78.00'))
        MarketPrice.objects.create(crop_name='String Bean', current_price=Decimal('81.00'))
        MarketPrice.objects.create(crop_name='Tomato', current_price=Decimal('72.00'))

        crop_pool = _get_recommendation_crop_pool()

        self.assertEqual(crop_pool, ['Beans', 'Tomato'])

    def test_recommendation_cards_remove_duplicates_and_curate_categories(self):
        MarketPrice.objects.create(
            crop_name='Sitaw',
            current_price=Decimal('78.00'),
            previous_price=Decimal('70.00'),
        )
        MarketPrice.objects.create(
            crop_name='Rice',
            current_price=Decimal('95.00'),
            previous_price=Decimal('70.00'),
        )
        MarketPrice.objects.create(
            crop_name='Tomato',
            current_price=Decimal('68.00'),
            previous_price=Decimal('62.00'),
        )

        cards = _build_recommendation_cards(
            [
                {'crop': 'String Bean', 'score': 0.82, 'category': 'seasonal', 'price': 79},
                {'crop': 'Beans', 'score': 0.76, 'category': 'high-demand', 'price': 77},
                {'crop': 'Rice', 'score': 0.48, 'category': 'high-demand', 'price': 94},
                {'crop': 'Tomato', 'score': 0.79, 'category': 'seasonal', 'price': 74},
            ],
            'Dry',
            {'temperature': 28, 'rainfall': 35, 'humidity': 70},
            _get_market_price_snapshot(),
        )

        crop_names = [card['crop'] for card in cards]
        self.assertEqual(crop_names.count('String Beans'), 1)
        self.assertIn('Tomato', crop_names)
        self.assertIn('Rice', crop_names)

        cards_by_crop = {card['crop']: card for card in cards}
        self.assertEqual(cards_by_crop['String Beans']['category'], 'seasonal')
        self.assertEqual(cards_by_crop['Tomato']['category'], 'seasonal')
        self.assertEqual(cards_by_crop['Rice']['category'], 'high-demand')

    def test_recommendation_cards_capitalize_crop_names(self):
        MarketPrice.objects.create(crop_name='rice', current_price=Decimal('95.00'))

        cards = _build_recommendation_cards(
            [{'crop': 'rice', 'score': 0.75, 'category': 'seasonal', 'price': 94}],
            'Wet',
            {'temperature': 28, 'rainfall': 120, 'humidity': 80},
            _get_market_price_snapshot(),
        )

        crop_names = [card['crop'] for card in cards]
        self.assertIn('Rice', crop_names)

    def test_top_recommendation_notification_notifies_admin_once(self):
        admin = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='StrongPass123!',
            account_type='admin'
        )

        predictions = [
            {'crop': 'Rice', 'suitability_percent': 91, 'price': 95},
            {'crop': 'Corn', 'suitability_percent': 80, 'price': 55},
        ]

        _notify_admins_about_top_recommendation(predictions, 'Wet')
        _notify_admins_about_top_recommendation(predictions, 'Wet')

        self.assertEqual(
            Notification.objects.filter(user=admin, title='Top crop recommendation updated').count(),
            1,
        )


class CropAdminNotificationTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_crop',
            email='admin_crop@example.com',
            password='StrongPass123!',
            account_type='admin'
        )
        self.farmer = User.objects.create_user(
            username='farmer_crop',
            email='farmer_crop@example.com',
            password='StrongPass123!',
            account_type='farmer'
        )
        self.buyer = User.objects.create_user(
            username='buyer_crop',
            email='buyer_crop@example.com',
            password='StrongPass123!',
            account_type='buyer'
        )

    def test_crop_add_notifies_admin(self):
        self.client.force_login(self.farmer)

        response = self.client.post(reverse('crops:crop_add'), {
            'crop_name': 'Rice',
            'price': '50.00',
            'quantity': '10.00',
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Notification.objects.filter(
                user=self.admin,
                title='New crop added',
            ).exists()
        )

    def test_crop_purchase_notifies_admin(self):
        crop = Crop.objects.create(
            user=self.farmer,
            crop_name='Rice',
            price=Decimal('50.00'),
            quantity=Decimal('10.00'),
            status='available',
        )
        self.client.force_login(self.buyer)

        response = self.client.post(reverse('crops:crop_purchase', args=[crop.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Notification.objects.filter(
                user=self.admin,
                title='Crop purchased',
            ).exists()
        )
