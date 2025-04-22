import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from game.models import Game  
from channels.db import database_sync_to_async
# only used to get timer 
class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']
        self.group_name = f"game_{self.game_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Start sending timer updates
        await self.send_timer_updates()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_timer_updates(self):
        while True:
            try:
                game = await self.get_game()
                if game:
                    is_running = await self.is_timer_running(game)
                    end_time = await self.get_timer_end_time(game)

                    if is_running and end_time:
                        remaining_time = end_time - timezone.now()
                        remaining_seconds = int(remaining_time.total_seconds())
                        await self.send(text_data=json.dumps({
                            'type': 'timer_update',
                            'remaining_seconds': remaining_seconds,
                        }))
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'timer_update',
                            'remaining_seconds': 0,
                        }))
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'timer_update',
                        'remaining_seconds': -1,  # Or some other indicator
                    }))
            except Exception as e:
                print(f"Error sending timer update: {e}")
                break
            await asyncio.sleep(1)  # Send update every second

    @database_sync_to_async
    def is_timer_running(self, game):
        return game.game_timer.is_running if game.game_timer else False

    @database_sync_to_async
    def get_timer_end_time(self, game):
        return game.game_timer.end_time if game.game_timer else None

    @database_sync_to_async
    def get_game(self):
        try:
            return Game.objects.get(game_id=self.game_id)
        except Game.DoesNotExist:
            return None

    # Example of receiving a message from the client (not strictly needed for just the timer)
    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')

            if message_type == 'client_action':
                # Handle a client action, e.g., sending a message to the group
                message = text_data_json.get('message')
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'game_message',
                        'text': message,
                        'sender': self.channel_name,
                    }
                )
        except json.JSONDecodeError:
            print("Invalid JSON received")

    # Example of handling a group message (if clients can send messages)
    async def game_message(self, event):
        message = event['text']
        sender = event['sender']
        # Send the message back to the client (excluding the sender if needed)
        await self.send(text_data=json.dumps({
            'type': 'game_message',
            'text': message,
            'sender': sender,
        }))