"""
ASGI config for anitech project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anitech.settings')

django_asgi_app = get_asgi_application()

import activity_log.routing
import notifications.routing

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            activity_log.routing.websocket_urlpatterns +
            notifications.routing.websocket_urlpatterns
        )
    ),
})
