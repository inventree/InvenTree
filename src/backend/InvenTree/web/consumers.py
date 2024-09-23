"""Websocket consumers for web app."""

import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer


class InvenTreeConsumer(JsonWebsocketConsumer):
    """This consumer is used to enable page attendance widgets."""

    def __init__(self, *args, **kwargs):
        """Set up context."""
        super().__init__(args, kwargs)
        self.user = None

    def connect(self):
        """Join a user to a page."""
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            self.close()
            return
        self.user = user
        self.accept()

        from django.contrib.auth.models import User

        from InvenTree.serializers import UserSerializer

        self.room_name = self.scope['url_route']['kwargs']['url_name']
        self.room_group_name = f'chat_{self.room_name}'
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        # Announce all users
        instances = User.objects.all()
        self.send_json({
            'type': 'users',
            'users': UserSerializer(instances, many=True).data,
        })

    def disconnect(self, code):
        """Remove user from a page."""
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )
        return super().disconnect(code)

    def receive_json(self, content, **kwargs):
        """Handler for processing incoming messages."""
        message_type = content.get('type', None)
        message = content.get('message', None)

        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.get_username(),
            },
        )

        if message_type == '#TODO':
            # TODO: implement this
            ...
        return super().receive_json(content, **kwargs)

    # Receive message from room group
    def chat_message(self, event):
        """Send message to WebSocket."""
        message = event['message']

        # Send message to WebSocket
        self.send(
            text_data=json.dumps({
                'type': 'chat_message',
                'message': message,
                'user': event['user'],
            })
        )
