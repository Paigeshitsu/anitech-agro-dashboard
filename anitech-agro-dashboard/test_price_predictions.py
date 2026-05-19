#!/usr/bin/env python
"""
Test script to verify the price_predictions view integration with Open-Meteo weather data and ML model.
"""
import os
import sys
import django
import json
from django.test import RequestFactory
from django.http import JsonResponse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from market.views import price_predictions

def test_price_predictions():
    """Test the price_predictions view with weather integration."""
    factory = RequestFactory()

    # Test data
    test_data = {
        'crops': ['Rice', 'Corn'],
        'period': '1_week'
    }

    # Create POST request
    request = factory.post(
        '/market/price-predictions/',
        data=json.dumps(test_data),
        content_type='application/json'
    )

    try:
        # Call the view
        response = price_predictions(request)

        if isinstance(response, JsonResponse):
            data = json.loads(response.content.decode('utf-8'))

            # Check if predicted_prices dictionary is returned
            if 'predicted_prices' in data:
                print("✅ SUCCESS: predicted_prices dictionary found")
                print(f"Predicted prices: {data['predicted_prices']}")

                # Check if weather data is included
                if 'weather_data' in data:
                    print("✅ SUCCESS: Weather data included")
                    print(f"Weather data: {data['weather_data']}")
                else:
                    print("❌ WARNING: No weather data in response")

                # Check if season is determined
                if 'season' in data:
                    print(f"✅ SUCCESS: Season determined: {data['season']}")
                else:
                    print("❌ WARNING: No season in response")

                return True
            else:
                print("❌ ERROR: predicted_prices dictionary not found in response")
                print(f"Response data: {data}")
                return False
        else:
            print("❌ ERROR: Response is not JsonResponse")
            return False

    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing price_predictions view with weather integration...")
    success = test_price_predictions()
    sys.exit(0 if success else 1)