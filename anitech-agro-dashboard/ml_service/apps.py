from django.apps import AppConfig


class MlServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ml_service'

    def ready(self):
        """
        ML model pre-loading disabled for instant loading with fallback predictions.
        Clear any cached models that might be causing errors.
        """
        from django.core.cache import cache
        cache.clear()  # Clear cache to remove any problematic cached models
        print("ML model pre-loading disabled - cache cleared - using fallback predictions for instant loading.")
