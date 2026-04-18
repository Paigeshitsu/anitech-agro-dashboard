from django.apps import AppConfig
from django.conf import settings
import os
import joblib
from pathlib import Path


class MlServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_service'

    def ready(self):
        """
        ML model pre-loading disabled for instant loading with fallback predictions.
        """
        print("ML model pre-loading disabled - using fallback predictions.")
