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

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_timer_updates()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_timer_updates(self):
        while True:
            try:
                game = await self.get_game()
                # check that game exists
                if game:
                    # retrieve info from db
                    is_running = await self.is_timer_running(game)
                    end_time = await self.get_timer_end_time(game)
                    rounds = await self.get_rounds(game)
                    current_artist = await self.get_artist(game)
                    guessers = await self.get_guessers(game)
                    team1_points = await self.get_team1_points(game)
                    team2_points = await self.get_team2_points(game)
                    word_to_guess = await self.get_word(game)
                    # there is time left in the timer
                    if is_running and end_time:
                        remaining_time = end_time - timezone.now()
                        remaining_seconds = int(remaining_time.total_seconds())
                        await self.send(text_data=json.dumps({
                            'type': 'timer_update',
                            'remaining_seconds': remaining_seconds,
                            'rounds':rounds,
                            'current_artist':current_artist,
                            'guessers':guessers,
                            'team1_points':team1_points,
                            'team2_points':team2_points,
                            'word_to_guess': word_to_guess,
                        }))
                    # time has run out
                    else:
                        await self.send(text_data=json.dumps({
                            'type': 'timer_update',
                            'remaining_seconds': 0,
                            'rounds':rounds,
                            'current_artist':current_artist,
                            'guessers':guessers,
                            'team1_points':team1_points,
                            'team2_points':team2_points,
                            'word_to_guess': word_to_guess,
                        }))
                # there is no game
                else:
                    await self.send(text_data=json.dumps({
                        'type': 'timer_update',
                        'remaining_seconds': -1, 
                    }))
            except Exception as e:
                print(f"Error sending timer update: {e}")
                break
            # update every second 
            await asyncio.sleep(1)  

    # helper functions to get data from the db
    @database_sync_to_async
    def get_word(self, game):
        return game.word_to_guess
    
    @database_sync_to_async
    def get_artist(self, game):
        return game.current_artist.player_import.username
    
    @database_sync_to_async
    def get_rounds(self, game):
        return game.rounds
    
    @database_sync_to_async
    def get_guessers(self, game):
        return game.guessers.name
    
    @database_sync_to_async
    def get_team1_points(self, game):
        return game.team1.score
    
    @database_sync_to_async
    def get_team2_points(self, game):
        return game.team2.score
    
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
