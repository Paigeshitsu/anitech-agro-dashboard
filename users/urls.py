from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/<int:user_id>/', views.verify_otp_view, name='verify_otp'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/read-all/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('notifications/<int:notification_id>/delete/', views.notification_delete, name='notification_delete'),
    path('notifications/filter/<str:filter_type>/', views.notifications_filter, name='notifications_filter'),
    path('crops/', views.crops_view, name='crops'),
    path('market/', views.market_view, name='market'),
    path('weather/', views.weather_view, name='weather'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('profile/', views.profile_view, name='profile'),
]
