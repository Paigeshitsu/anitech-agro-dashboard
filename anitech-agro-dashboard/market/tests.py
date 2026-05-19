from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from crops.models import Crop
from activity_log.models import ActivityLog
from market.models import BuyerOffer, MarketPrice, ScheduleDistribution, SellerOffer
from market.views import _filter_valid_market_predictions, generate_fallback_market_predictions
from notifications.models import Notification
from unittest.mock import patch
from pathlib import Path


User = get_user_model()


class MarketFlowRegressionTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin_user',
            password='testpass123',
            account_type='admin',
        )
        self.farmer = User.objects.create_user(
            username='farmer_user',
            password='testpass123',
            account_type='farmer',
        )
        self.other_farmer = User.objects.create_user(
            username='other_farmer',
            password='testpass123',
            account_type='farmer',
        )
        self.buyer = User.objects.create_user(
            username='buyer_user',
            password='testpass123',
            account_type='buyer',
        )
        self.secretary = User.objects.create_user(
            username='secretary_user',
            password='testpass123',
            account_type='secretary',
        )

        self.farmer_crop = Crop.objects.create(
            user=self.farmer,
            crop_name='Rice',
            price='50.00',
            wholesale_price='45.00',
            retail_price='55.00',
            quantity='100.00',
            unit='kg',
            status='available',
        )
        self.other_crop = Crop.objects.create(
            user=self.other_farmer,
            crop_name='Corn',
            price='42.00',
            wholesale_price='40.00',
            retail_price='44.00',
            quantity='80.00',
            unit='kg',
            status='available',
        )

    def test_schedule_add_redirects_for_admin(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse('market:schedule_add'), {
            'title': 'Rice Distribution',
            'description': 'Morning release',
            'quantity': '10 sacks',
            'recipient': 'Barangay 1',
            'scheduled_date': '2026-05-01T09:30',
            'location': 'Municipal Hall',
            'status': 'Pending',
        })

        self.assertRedirects(response, reverse('market:schedule_list'))
        self.assertTrue(
            ScheduleDistribution.objects.filter(title='Rice Distribution').exists()
        )

    def test_farmer_sell_offer_form_only_accepts_owned_crop(self):
        self.client.force_login(self.farmer)

        response = self.client.post(reverse('market:seller_offer_add'), {
            'crop': self.other_crop.id,
            'ask_price': '99.00',
            'quantity': '10.00',
            'expiry_date': '2026-05-10',
            'status': 'Pending',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SellerOffer.objects.filter(farmer=self.farmer, crop=self.other_crop).exists()
        )
        self.assertFormError(
            response.context['form'],
            'crop',
            'Select a valid choice. That choice is not one of the available choices.',
        )

    def test_farmer_can_create_sell_offer_for_owned_crop(self):
        self.client.force_login(self.farmer)

        response = self.client.post(reverse('market:seller_offer_add'), {
            'crop': self.farmer_crop.id,
            'ask_price': '99.00',
            'quantity': '10.00',
            'expiry_date': '2026-05-10',
            'status': 'Pending',
        })

        self.assertRedirects(response, reverse('market:seller_offer_list'))
        self.assertTrue(
            SellerOffer.objects.filter(farmer=self.farmer, crop=self.farmer_crop).exists()
        )

    def test_buyer_can_submit_offer_from_seller_offer_detail(self):
        seller_offer = SellerOffer.objects.create(
            farmer=self.farmer,
            crop=self.farmer_crop,
            ask_price='95.00',
            quantity='25.00',
            expiry_date='2026-05-12',
            status='Pending',
        )

        self.client.force_login(self.buyer)
        response = self.client.post(
            reverse('market:seller_offer_detail', args=[seller_offer.id]),
            {
                'offer_price': '90.00',
                'quantity': '12.00',
                'contact_number': '09171234567',
            },
        )

        self.assertRedirects(
            response,
            reverse('market:seller_offer_detail', args=[seller_offer.id]),
        )
        buyer_offer = BuyerOffer.objects.get(crop=self.farmer_crop, buyer_name=self.buyer.username)
        self.assertEqual(buyer_offer.crop_name, self.farmer_crop.crop_name)
        self.assertEqual(str(buyer_offer.offer_price), '90.00')
        self.assertEqual(str(buyer_offer.quantity), '12.00')
        self.assertTrue(
            ActivityLog.objects.filter(
                user=self.buyer,
                event_type='create',
                resource_id=str(buyer_offer.id),
                resource_name=self.farmer_crop.crop_name,
            ).exists()
        )

    def test_non_buyer_cannot_submit_offer_from_seller_offer_detail(self):
        seller_offer = SellerOffer.objects.create(
            farmer=self.farmer,
            crop=self.farmer_crop,
            ask_price='95.00',
            quantity='25.00',
            expiry_date='2026-05-12',
            status='Pending',
        )

        self.client.force_login(self.secretary)
        response = self.client.post(
            reverse('market:seller_offer_detail', args=[seller_offer.id]),
            {
                'offer_price': '90.00',
                'quantity': '12.00',
            },
        )

        self.assertRedirects(
            response,
            reverse('market:seller_offer_detail', args=[seller_offer.id]),
        )
        self.assertFalse(BuyerOffer.objects.filter(crop=self.farmer_crop).exists())

    def test_top_market_price_update_notifies_admin(self):
        MarketPrice.objects.create(crop_name='Rice', current_price='50.00')
        MarketPrice.objects.create(crop_name='Onion', current_price='120.00')

        self.assertTrue(
            Notification.objects.filter(
                user=self.admin,
                title='Top market price updated',
            ).exists()
        )

    def test_fallback_market_predictions_skip_invalid_database_prices(self):
        MarketPrice.objects.create(crop_name='Rice', current_price='50.00')
        MarketPrice.objects.create(crop_name='Corn', current_price='0.00')

        predictions = generate_fallback_market_predictions(['Rice', 'Corn'])

        self.assertEqual([item['crop'] for item in predictions], ['Rice'])

    def test_market_prediction_filter_drops_na_cards(self):
        filtered = _filter_valid_market_predictions([
            {
                'crop': 'Rice',
                'current_price': 50,
                'predictions': [
                    {'period': '1_week', 'predicted_price': 51},
                    {'period': '1_month', 'predicted_price': 55},
                    {'period': '3_months', 'predicted_price': 60},
                ],
            },
            {
                'crop': 'Corn',
                'current_price': 40,
                'predictions': [
                    {'period': '1_week', 'predicted_price': 41},
                    {'period': '1_month', 'predicted_price': None},
                    {'period': '3_months', 'predicted_price': 50},
                ],
            },
        ])

        self.assertEqual([item['crop'] for item in filtered], ['Rice'])

    @patch('market.views.trigger_bantay_presyo_sync_async')
    @patch('market.views.generate_ml_market_predictions')
    @patch('market.views._get_market_weather_data')
    @patch('market.views.ensure_market_price_data_available')
    def test_market_prices_view_triggers_background_sync_when_opened(
        self,
        mock_ensure_market_data,
        mock_weather,
        mock_generate_predictions,
        mock_trigger_sync,
    ):
        MarketPrice.objects.create(crop_name='Rice', current_price='50.00')
        mock_weather.return_value = {
            'temperature': 28,
            'humidity': 65,
            'precipitation': 0,
            'rainfall': 0,
        }
        mock_generate_predictions.return_value = [
            {
                'crop': 'Rice',
                'current_price': 50,
                'predictions': [
                    {'period': '1_week', 'predicted_price': 51},
                    {'period': '1_month', 'predicted_price': 55},
                    {'period': '3_months', 'predicted_price': 60},
                ],
            }
        ]

        response = self.client.get(reverse('market:prices'))

        self.assertEqual(response.status_code, 200)
        mock_ensure_market_data.assert_called_once_with()
        mock_trigger_sync.assert_called_once_with(only_if_stale=True)

    @patch('market.views.trigger_bantay_presyo_sync_async')
    def test_refresh_market_prices_endpoint_starts_async_sync(self, mock_trigger_sync):
        mock_trigger_sync.return_value = True

        response = self.client.post(reverse('market:refresh_market_prices'))

        self.assertEqual(response.status_code, 202)
        self.assertJSONEqual(
            response.content,
            {
                'started': True,
                'async': True,
                'status': {
                    'is_syncing': False,
                    'last_success_at': None,
                    'last_attempt_at': None,
                    'last_error': None,
                    'last_source_date': None,
                },
            },
        )


class MarketAutoRecoveryTest(TestCase):
    @patch('market.services.bantay_presyo.sync_bantay_presyo_market_prices')
    def test_ensure_market_price_data_available_syncs_when_market_table_is_empty(self, mock_sync):
        from market.services.bantay_presyo import ensure_market_price_data_available

        mock_sync.return_value = {'status': 'success'}

        result = ensure_market_price_data_available()

        self.assertTrue(result['recovered'])
        self.assertEqual(result['reason'], 'missing_db_rows_or_csv')
        mock_sync.assert_called_once_with(force=True)

    @patch('market.services.bantay_presyo.sync_bantay_presyo_market_prices')
    def test_ensure_market_price_data_available_syncs_when_csv_is_missing(self, mock_sync):
        from market.services import bantay_presyo as service

        MarketPrice.objects.create(crop_name='Rice', current_price='50.00')
        mock_sync.return_value = {'status': 'success'}

        with patch.object(service, 'FILTERED_CSV_PATH', Path('missing-filtered.csv')):
            with patch.object(service, 'ML_CSV_PATH', Path('missing-ml.csv')):
                result = service.ensure_market_price_data_available()

        self.assertTrue(result['recovered'])
        mock_sync.assert_called_once_with(force=True)
