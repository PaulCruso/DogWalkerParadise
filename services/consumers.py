import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
from django.contrib.auth.models import User
from .models import Appointment, ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):

        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'chat_{self.appointment_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Accept the connection
        await self.accept()

        # Send chat history
        await self.send_chat_history()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        
        # Save the message
        await self.save_message(message)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': self.scope["user"].username,
                'timestamp': datetime.now().isoformat()
            }
        )

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, message):
        user = self.scope["user"]
        appointment = Appointment.objects.get(id=self.appointment_id)
        ChatMessage.objects.create(
            appointment=appointment,
            sender=user,
            content=message
        )

    @database_sync_to_async
    def get_chat_history(self):
        appointment = Appointment.objects.get(id=self.appointment_id)
        return list(ChatMessage.objects.filter(appointment=appointment).order_by('timestamp').values(
            'content',
            'sender__username',
            'timestamp'
        ))

    async def send_chat_history(self):
        history = await self.get_chat_history()
        if history:
            await self.send(text_data=json.dumps({
                'type': 'history',
                'messages': [
                    {
                        'message': msg['content'],
                        'username': msg['sender__username'],
                        'timestamp': msg['timestamp'].isoformat()
                    }
                    for msg in history
                ]
            }))
            
            
class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = f"user_{self.scope['user'].id}"

        # Add user to their notification group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_notification(self, event):
        # Send notification data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message'],
            'appointment_id': event['appointment_id'],
            'timestamp': event['timestamp']
        }))