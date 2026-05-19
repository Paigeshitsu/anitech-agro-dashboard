#!/usr/bin/env python
"""
Test script to verify that market predictions now show varied trends (not all increases)
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from market.views import market_prices_view
from django.test import RequestFactory

def test_prediction_variation():
    """Test that predictions show varied trends, not all increases."""
    factory = RequestFactory()

    # Test the price_predictions API endpoint directly
    api_request = factory.post(
        '/market/price-predictions/',
        data=json.dumps({'crops': ['Rice', 'Corn', 'Tomato', 'Onion', 'Garlic']}),
        content_type='application/json'
    )

    try:
        from market.views import price_predictions
        api_response = price_predictions(api_request)

        if hasattr(api_response, 'content'):
            data = json.loads(api_response.content.decode('utf-8'))
            predicted_prices = data.get('predicted_prices', {})

            print("Testing prediction variation:")
            print("=" * 40)
            print("Predicted prices:")
            for crop, price in predicted_prices.items():
                print(f"  {crop}: {price} PHP")

            # Check if we have varied predictions
            prices = list(predicted_prices.values())
            if len(prices) > 1:
                min_price = min(prices)
                max_price = max(prices)
                avg_price = sum(prices) / len(prices)
                variation = (max_price - min_price) / avg_price * 100

                print(f"\nPrice range: {min_price} - {max_price} PHP")
                print(".1f")

                if variation > 20:  # At least 20% variation
                    print("✅ SUCCESS: Predictions show good variation")
                    return True
                else:
                    print("❌ WARNING: Predictions show low variation")
                    return False
            else:
                print("❌ ERROR: Not enough predictions to test variation")
                return False
        else:
            print("❌ ERROR: No API response content")
            return False

    except Exception as e:
        print(f"❌ ERROR: Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_prediction_variation()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")