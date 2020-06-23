from django.contrib.auth import get_user_model
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import Message
from django.contrib.auth.models import User

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )



    def fetch_messages(self, data):
        messages=Message.objects.all()
        content={
            'messages':self.messages_to_json(messages)
        }
        self.send_message(content)

    def messages_to_json(self, messages):#serialize all messages
        result=[]
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def send_chat_message(self, message):#Send retrieved messages stored in
        # the database to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))




    def new_message(self, data):
        author=data['from']
        author_user=User.objects.filter(username=author)[0]
        message=Message.objects.create(
            author=author_user,
            content=data['message']
        )
        content={
            'command':'new_message',
            'message':self.message_to_json(message)
        }
        return self.send_chat_message(content)
        #print('new message')

    def message_to_json(self, message):
        return {
            'author':message.author.username,
            'content':message.content,
            'timestamp':str(message.timestamp)
        }

    commands={
        'fetch_messages':fetch_messages,
        'new_message':new_message
    }

    # Receive message from WebSocket
    def receive(self, text_data):
        data = json.loads(text_data)
        print(data)
        self.commands[data['command']](data)


    def send_message(self, message):
        self.send(text_data=json.dumps(message))




#This new code is for ChatConsumer is very similar to the original code,
#with the following differences:

#ChatConsumer now inherits from AsyncWebsocketConsumer rather than WebsocketConsumer.
#All methods are async def rather than just def.
#await is used to call asynchronous functions that perform I/O.
#async_to_sync is no longer needed when calling methods on the channel layer.


#When a user posts a message, a JavaScript function will
#transmit the message over WebSocket to a ChatConsumer.
#The ChatConsumer will receive that message and forward it to
#the group corresponding to the room name.
#Every ChatConsumer in the same group (and thus in the same room)
#will then receive the message from the group and forward it
#over WebSocket back to JavaScript,
# where it will be appended to the chat log.


#****self.scope['url_route']['kwargs']['room_name']
#Obtains the 'room_name' parameter from the URL route in chat/routing.py that opened
#the WebSocket connection to the consumer.
#Every consumer has a scope that contains information about its connection,
#including in particular any positional or keyword arguments
#from the URL route and the currently authenticated user if any.


#****self.room_group_name = 'chat_%s' % self.room_name
#Constructs a Channels group name directly from the user-specified room name,
#without any quoting or escaping.
#Group names may only contain letters, digits, hyphens, and periods.
#Therefore this example code will fail on room names that have other characters.


#****async_to_sync(self.channel_layer.group_add)(...)
#Joins a group. The async_to_sync(…) wrapper is required
#because ChatConsumer is a synchronous WebsocketConsumer
#but it is calling an asynchronous channel layer method.
#(All channel layer methods are asynchronous.)
#Group names are restricted to ASCII alphanumerics, hyphens, and periods only.
#Since this code constructs a group name directly
#from the room name, it will fail if the room name
#contains any characters that aren’t valid in a group name.


#****self.accept()
#Accepts the WebSocket connection.
#If you do not call accept() within the connect() method then
 #the connection will be rejected and closed.
 #You might want to reject a connection for example
 #because the requesting user is not authorized to perform the requested action.
#It is recommended that accept() be called as
#the last action in connect() if you choose to accept the connection.


#async_to_sync(self.channel_layer.group_discard)(...)
#Leaves a group.


#async_to_sync(self.channel_layer.group_send)
#Sends an event to a group.
#An event has a special 'type' key corresponding to the name of
#the method that should be invoked on consumers that receive the event.
