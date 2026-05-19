import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')
import django
django.setup()

from ml_service.market_price_predictor import predict_market_price
from ml_service.views import get_current_weather

# Get weather
weather = get_current_weather()
print('Weather:', weather)

# Test predictions
crops = ['Rice', 'Corn', 'Tomato']
for crop in crops:
    pred = predict_market_price(crop, 'Legazpi City', season='Dry', weather_data=weather)
    print(f'{crop}: {pred["predicted_price_php"]} PHP')