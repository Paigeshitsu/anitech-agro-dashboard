from django.test import TestCase
from django.contrib.auth import get_user_model
from crops.models import Crop
from django.utils import timezone
from decimal import Decimal

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
