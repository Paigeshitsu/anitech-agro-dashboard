#!/usr/bin/env python
"""
Test script to check ML model predictions for different crops
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
django.setup()

from ml_service.market_price_predictor import predict_market_price
from ml_service.views import get_current_weather

def test_predictions():
    # Get current weather
    weather = get_current_weather()
    print('Weather data:', weather)
    print()

    # Test predictions for different crops
    crops = ['Rice', 'Corn', 'Tomato', 'Onion', 'Garlic', 'Cabbage']
    print('Testing ML predictions for different crops:')
    print('=' * 50)

    for crop in crops:
        try:
            pred = predict_market_price(crop, 'Legazpi City', season='Dry', weather_data=weather)
            price = pred.get('predicted_price_php', 'N/A')
            print(f'{crop:12}: {price} PHP')
        except Exception as e:
            print(f'{crop:12}: ERROR - {str(e)}')

if __name__ == '__main__':
    test_predictions()