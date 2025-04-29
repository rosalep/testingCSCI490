# from django.db import models
# from game.models import Player, Game

# class ChatMessage(models.Model):
#     game_import = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_import') 
#     player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True) 
#     message = models.TextField()
#     time_sent = models.DateTimeField(auto_now_add=True)


from django.db import models
# from users.models import CustomUser
from game.models import Player, Game
class ChatMessage(models.Model):
    game_import = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='game_import') 
    message_sender = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True) 
    message = models.TextField()
    time_sent = models.DateTimeField(auto_now_add=True)


