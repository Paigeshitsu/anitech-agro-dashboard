from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache

from users.models import User

from .models import Notification


def create_notification(user, notif_type, title, message):
    return Notification.objects.create(
        user=user,
        type=notif_type,
        title=title,
        message=message,
    )


def notify_users(users, notif_type, title, message):
    notifications = []
    for user in users:
        notifications.append(create_notification(user, notif_type, title, message))
    return notifications


def get_admin_users():
    return User.objects.filter(account_type='admin')


def notify_admins(title, message, notif_type='info'):
    return notify_users(get_admin_users(), notif_type, title, message)


def notify_admins_once(cache_key, snapshot, title, message, notif_type='info', timeout=3600):
    previous_snapshot = cache.get(cache_key)
    if previous_snapshot == snapshot:
        return []

    cache.set(cache_key, snapshot, timeout)
    return notify_admins(title, message, notif_type=notif_type)


def notify_all_users(title, message, notif_type='info'):
    return notify_users(User.objects.all(), notif_type, title, message)


def broadcast_notification(notification):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f'notifications_user_{notification.user_id}',
        {
            'type': 'notification_update',
            'notification_id': notification.id,
            'title': notification.title,
            'message': notification.message,
        }
    )
