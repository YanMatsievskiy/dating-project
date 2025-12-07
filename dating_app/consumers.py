# dating_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Match, Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        # Получаем ID другого пользователя из URL (chat/<other_user_id>/)
        self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
        try:
            self.other_user = await database_sync_to_async(User.objects.get)(id=self.other_user_id)
        except User.DoesNotExist:
            await self.close()
            return

        # Проверяем, есть ли матч между пользователями
        match_exists = await self.check_match_exists(self.user, self.other_user)
        if not match_exists:
            await self.close()
            return

        # Создаем уникальное имя группы для чата между двумя пользователями
        self.room_group_name = f"chat_{min(self.user.id, self.other_user.id)}_{max(self.user.id, self.other_user.id)}"

        # Присоединяемся к группе чата
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Покидаем группу чата
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получение сообщения от WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']

        # Сохраняем сообщение в базе данных
        message = await self.save_message(self.user, self.other_user, message_content)

        # Отправляем сообщение в группу чата
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message.content,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'timestamp': message.timestamp.isoformat(),
            }
        )

    # Получение сообщения от группы чата
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def check_match_exists(self, user1, user2):
        return Match.objects.filter(
            (models.Q(user1=user1) & models.Q(user2=user2)) |
            (models.Q(user1=user2) & models.Q(user2=user1))
        ).exists()

    @database_sync_to_async
    def save_message(self, sender, receiver, content):
        # Найдем или создадим чат между пользователями
        from .models import Chat
        chat, created = Chat.objects.get_or_create()
        chat.participants.add(sender, receiver)
        # Создаем и сохраняем сообщение
        message = Message(chat=chat, sender=sender, content=content)
        message.save()
        return message