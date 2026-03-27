"""
WebSocket routing for activity log.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/activity-log/$', consumers.ActivityLogConsumer.as_asgi()),
]
