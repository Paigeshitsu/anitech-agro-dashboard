from django.urls import path
from . import views

app_name = 'ml_service'

urlpatterns = [
    path('predict/', views.predict_crops, name='predict_crops'),
    path('forecast-price/', views.forecast_price, name='forecast_price'),
    path('weather-history/', views.weather_history, name='weather_history'),
    path('weather-trends/', views.ml_weather_trends, name='ml_weather_trends'),
    path('crop-care/', views.crop_care_recommendations, name='crop_care'),
]
