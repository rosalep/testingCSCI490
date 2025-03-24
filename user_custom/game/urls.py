from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_game, name='create_game'),
    path('game/<int:game_id>', views.game_detail, name='game_detail'),
    path('add_player/<int:team_id>/', views.add_player, name='add_player'),
    path('next_round/<int:game_id>/', views.next_round, name='next_round'),
    path('switch_teams/<int:game_id>/', views.switch_teams, name='switch_teams'),
    
]