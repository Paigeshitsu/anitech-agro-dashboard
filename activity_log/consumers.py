"""
WebSocket consumers for real-time activity log updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async


class ActivityLogConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time activity log notifications.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.group_name = 'activity_log_updates'
        
        # Join the activity log group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to activity log updates'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the activity log group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            
            if data.get('type') == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
            elif data.get('type') == 'subscribe':
                # Handle subscription requests
                await self.send(text_data=json.dumps({
                    'type': 'subscribed',
                    'filters': data.get('filters', {})
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def new_log_entry(self, event):
        """Handle new log entry notifications."""
        await self.send(text_data=json.dumps({
            'type': 'new_log_entry',
            'log_id': event.get('log_id'),
            'count': event.get('count', 1),
            'timestamp': event.get('timestamp')
        }))
    
    async def log_update(self, event):
        """Handle log update notifications."""
        await self.send(text_data=json.dumps({
            'type': 'log_update',
            'log_id': event.get('log_id'),
            'action': event.get('action'),
            'timestamp': event.get('timestamp')
        }))
    
    async def stats_update(self, event):
        """Handle statistics update notifications."""
        await self.send(text_data=json.dumps({
            'type': 'stats_update',
            'stats': event.get('stats', {})
        }))


class ActivityLogNotifier:
    """
    Utility class to broadcast activity log events to WebSocket clients.
    """
    
    @staticmethod
    async def notify_new_entry(log_id, channel_layer):
        """Notify all connected clients about a new log entry."""
        from django.utils import timezone
        
        await channel_layer.group_send(
            'activity_log_updates',
            {
                'type': 'new_log_entry',
                'log_id': log_id,
                'count': 1,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    @staticmethod
    async def notify_stats_update(stats, channel_layer):
        """Notify all connected clients about statistics updates."""
        await channel_layer.group_send(
            'activity_log_updates',
            {
                'type': 'stats_update',
                'stats': stats
            }
        )
