
"""
URL configuration for anitech project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.views.static import serve
from . import views
import os

def favicon_view(request):
    favicon_path = os.path.join(settings.STATICFILES_DIRS[0], 'favicon.ico')
    return serve(request, os.path.basename(favicon_path), os.path.dirname(favicon_path))

urlpatterns = [
    path('favicon.ico', favicon_view, name='favicon'),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls')),
    path('ml/', include('ml_service.urls')),
    path('crops/', include('crops.urls')),
    path('market/', include('market.urls', namespace='market')),
    path('notifications/', include('notifications.urls')),
    path('activity-log/', include('activity_log.urls')),
    path('weather/', views.weather_view, name='weather'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('profile/', views.profile_view, name='profile'),
    path('set-language/', views.set_language_view, name='set_language'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/<int:inventory_id>/edit/', views.inventory_edit, name='inventory_edit'),
    path('inventory/<int:inventory_id>/delete/', views.inventory_delete, name='inventory_delete'),
    path('', views.home_view, name='home'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

