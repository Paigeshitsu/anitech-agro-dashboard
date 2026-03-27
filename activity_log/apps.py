"""
Activity Log App Configuration
"""
from django.apps import AppConfig


class ActivityLogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_log'
    verbose_name = 'Activity Log'
    
    def ready(self):
        # Import and connect signal handlers when app is ready
        from . import signals
        signals.connect_activity_log_signals()
