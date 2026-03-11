from django.urls import path
from . import views

urlpatterns = [
    path('api/', views.notifications_api, name='notifications_api'),
    path('api/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]
