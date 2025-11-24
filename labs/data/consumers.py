import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from . import models


class BackendConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = 'taskmessages'

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()
        running = models.ThreadTask.objects.filter(is_done=False)
        for task in running:
            send_message('task{}'.format(task.id), 'info', task.name + ':', '')

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Receive message from room group
    def task_message(self, event):
        # Send message to WebSocket
        self.send(text_data=json.dumps(event))


def send_message(id, level, message, submessage):
    async_to_sync(get_channel_layer().group_send)(
        'taskmessages',
        {
            'action': 'create',
            'type': 'task_message',
            'message': message,
            'id': id,
            'submessage': submessage,
            'level': 'info',
        }
    )


def send_sub_message(id, level='info', submessage=''):
    print('sending sub message: {}'.format(submessage))
    async_to_sync(get_channel_layer().group_send)(
        'taskmessages',
        {
            'action': 'update',
            'type': 'task_message',
            'id': id,
            'submessage': submessage,
            'level': level,
        }
    )
