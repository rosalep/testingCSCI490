from django.contrib import admin
from .models import Team, Player, Timer, WordBank, Game
# Register your models here.
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Timer)
admin.site.register(WordBank)
admin.site.register(Game)