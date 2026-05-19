import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ActivityLogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_names = []

        if user.account_type == 'admin':
            self.group_names.append('activity_log_admin')
        elif user.account_type == 'secretary':
            self.group_names.append('activity_log_secretary')
        else:
            self.group_names.append(f'activity_log_user_{user.id}')

        for group_name in self.group_names:
            await self.channel_layer.group_add(group_name, self.channel_name)

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to activity log updates',
        }))

    async def disconnect(self, close_code):
        for group_name in getattr(self, 'group_names', []):
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def activity_log_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'activity_log_update',
            'log_id': event.get('log_id'),
            'action': event.get('action'),
        }))
