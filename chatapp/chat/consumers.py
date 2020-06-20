import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name=self.scope['url_route']['kwargs']['room_name']
        self.room_group_name='chat_%s' % self.room_name

        #join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )


    def disconnect(self, close_code):
        #leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    #receive message from websocket
    def receive(self, text_data):
        text_data_json=json.loads(text_data)
        message=text_data_json['message']

        #send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'chat_message',
                'message':message
            }
        )

    #Receive message from room group
    def chat_message(self, event):
        message=event['message']

        #send message to WebSocket
        self.send(text_data=json.dumps({
            'message':message
        }))

#When a user posts a message, a JavaScript function will
#transmit the message over WebSocket to a ChatConsumer.
#The ChatConsumer will receive that message and forward it to
#the group corresponding to the room name.
#Every ChatConsumer in the same group (and thus in the same room)
#will then receive the message from the group and forward it
#over WebSocket back to JavaScript,
# where it will be appended to the chat log.
