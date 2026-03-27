"""
URL configuration for Activity Log app.
"""
from django.urls import path
from . import views

app_name = 'activity_log'

urlpatterns = [
    # Main views
    path('', views.ActivityLogListView.as_view(), name='list'),
    path('detail/<int:log_id>/', views.ActivityLogDetailView.as_view(), name='detail'),
    path('export/', views.ActivityLogExportView.as_view(), name='export'),
    path('stats/', views.ActivityLogStatsView.as_view(), name='stats'),
    path('badge/', views.activity_log_badge, name='badge'),
    path('jump/<int:year>/<int:month>/<int:day>/', views.jump_to_date, name='jump_to_date'),
    
    # API endpoints
    path('api/', views.activity_log_api, name='api'),
]
