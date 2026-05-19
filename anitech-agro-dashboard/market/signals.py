from django.db.models.signals import post_save
from django.dispatch import receiver

from activity_log.utils import log_activity
from notifications.services import notify_admins_once, notify_all_users

from .models import MarketPrice


@receiver(post_save, sender=MarketPrice)
def notify_market_price_change(sender, instance, created, **kwargs):
    previous_price = instance.previous_price
    current_price = instance.current_price

    if not created and previous_price == current_price:
        return

    if previous_price is None and created:
        action = f'Added market price: {instance.crop_name} is now {current_price}'
        title = f'{instance.crop_name} market price posted'
    else:
        action = f'Updated market price: {instance.crop_name} is now {current_price}'
        title = f'{instance.crop_name} price updated'

    message = f'{instance.crop_name} is now {current_price} {instance.unit}'.strip()

    log_activity(
        user=None,
        event_type='update' if not created else 'create',
        severity='info',
        status='success',
        action=action,
        description=message,
        resource_type='market',
        resource_id=str(instance.id),
        resource_name=instance.crop_name,
    )

    notify_all_users(title, message, notif_type='market')

    top_market_price = MarketPrice.objects.order_by('-current_price', 'crop_name').first()
    if top_market_price:
        top_snapshot = {
            'crop': top_market_price.crop_name,
            'price': str(top_market_price.current_price),
            'unit': top_market_price.unit,
        }
        notify_admins_once(
            'admin_notification_top_market_price',
            top_snapshot,
            'Top market price updated',
            (
                f"{top_market_price.crop_name} is now the top market price at "
                f"PHP {top_market_price.current_price} {top_market_price.unit}."
            ),
            notif_type='market',
            timeout=3600,
        )
