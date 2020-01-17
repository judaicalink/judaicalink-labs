from channels.generic.websocket import WebsocketConsumer
import json
import time

class BackendConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        print('message received')
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        time.sleep(10)
        print('waiting done')

        self.send(text_data=json.dumps({
            'message': message
        }))