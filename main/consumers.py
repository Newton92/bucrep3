# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from main.models import Notification

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.group_name = f'user_{self.user.id}'
            
            # Rejoindre le groupe
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.accept()
            
            # Envoyer les notifications non lues
            await self.send_unread_notifications()
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'mark_read':
            await self.mark_notification_read(data.get('notification_id'))
        elif action == 'mark_all_read':
            await self.mark_all_read()
    
    async def send_unread_notifications(self):
        notifications = await self.get_unread_notifications()
        await self.send(text_data=json.dumps({
            'type': 'unread_list',
            'notifications': notifications
        }))
    
    async def notification_message(self, event):
        """Envoyer une notification au client"""
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': event['notification']
        }))
    
    @database_sync_to_async
    def get_unread_notifications(self):
        return list(Notification.objects.filter(
            user=self.user,
            is_read=False
        ).values('id', 'type', 'message', 'created_at'))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        Notification.objects.filter(
            id=notification_id,
            user=self.user
        ).update(is_read=True)
    
    @database_sync_to_async
    def mark_all_read(self):
        Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True)