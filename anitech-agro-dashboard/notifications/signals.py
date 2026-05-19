from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .services import broadcast_notification


@receiver(post_save, sender=Notification)
def broadcast_notification_on_create(sender, instance, created, **kwargs):
    if created:
        broadcast_notification(instance)
