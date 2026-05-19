import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_name = f'notifications_user_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notifications',
        }))

    async def disconnect(self, close_code):
        group_name = getattr(self, 'group_name', None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def notification_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification_update',
            'notification_id': event.get('notification_id'),
            'title': event.get('title'),
            'message': event.get('message'),
        }))
