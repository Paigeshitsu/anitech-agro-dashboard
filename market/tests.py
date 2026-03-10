from django.test import TestCase
from django.contrib.auth import get_user_model
from market.models import MarketPrice, BuyerOffer, ScheduleDistribution
from crops.models import Crop
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class MarketPriceModelTest(TestCase):
    def test_market_price_creation(self):
        market_price = MarketPrice.objects.create(
            crop_name='Rice',
            price=Decimal('500.00')
        )
        self.assertEqual(market_price.crop_name, 'Rice')
        self.assertEqual(market_price.price, Decimal('500.00'))

    def test_multiple_prices_for_same_crop(self):
        for price_val in [500, 600, 700]:
            MarketPrice.objects.create(
                crop_name='Rice',
                price=Decimal(str(price_val)) + Decimal('0.00')
            )
        self.assertEqual(MarketPrice.objects.filter(crop_name='Rice').count(), 3)

    def test_market_price_auto_date(self):
        market_price = MarketPrice.objects.create(
            crop_name='Wheat',
            price=Decimal('400.00')
        )
        self.assertIsNotNone(market_price.date)

class BuyerOfferModelTest(TestCase):
    def test_buyer_offer_creation(self):
        offer = BuyerOffer.objects.create(
            buyer_name='John Buyer',
            crop_name='Rice',
            offer_price=Decimal('600.00'),
            status='Pending'
        )
        self.assertEqual(offer.buyer_name, 'John Buyer')
        self.assertEqual(offer.crop_name, 'Rice')
        self.assertEqual(offer.offer_price, Decimal('600.00'))
        self.assertEqual(offer.status, 'Pending')

    def test_buyer_offer_with_contact(self):
        offer = BuyerOffer.objects.create(
            buyer_name='Jane Buyer',
            contact_number='1234567890',
            crop_name='Wheat',
            offer_price=Decimal('400.00')
        )
        self.assertEqual(offer.contact_number, '1234567890')

    def test_offer_status_transitions(self):
        offer = BuyerOffer.objects.create(
            buyer_name='John Buyer',
            crop_name='Rice',
            offer_price=Decimal('600.00'),
            status='Pending'
        )
        self.assertEqual(offer.status, 'Pending')
        offer.status = 'Accepted'
        offer.save()
        self.assertEqual(offer.status, 'Accepted')

    def test_offer_status_choices(self):
        for status in ['Pending', 'Accepted', 'Rejected']:
            offer = BuyerOffer.objects.create(
                buyer_name=f'Buyer_{status}',
                crop_name='Rice',
                offer_price=Decimal('500.00'),
                status=status
            )
            self.assertEqual(offer.status, status)

class ScheduleDistributionModelTest(TestCase):
    def test_schedule_distribution_creation(self):
        schedule = ScheduleDistribution.objects.create(
            title='Rice Distribution',
            description='Distribute rice to market',
            scheduled_date=timezone.now(),
            location='Distribution Center A'
        )
        self.assertEqual(schedule.title, 'Rice Distribution')
        self.assertEqual(schedule.location, 'Distribution Center A')

    def test_multiple_schedules(self):
        for i in range(3):
            ScheduleDistribution.objects.create(
                title=f'Distribution {i}',
                description=f'Description {i}',
                scheduled_date=timezone.now(),
                location=f'Center {i}'
            )
        self.assertEqual(ScheduleDistribution.objects.count(), 3)

    def test_schedule_created_at(self):
        schedule = ScheduleDistribution.objects.create(
            title='Test Schedule',
            description='Test distribution',
            scheduled_date=timezone.now(),
            location='Test Location'
        )
        self.assertIsNotNone(schedule.created_at)
