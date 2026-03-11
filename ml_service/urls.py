from django.urls import path
from . import views

app_name = 'ml_service'

urlpatterns = [
    path('predict/', views.predict_crops, name='predict_crops'),
]
