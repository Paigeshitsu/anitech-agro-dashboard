from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('api/', views.notifications_api, name='notifications_api'),
    path('api/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]
