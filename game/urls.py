from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_game, name='create_game'),
    path('game/<int:game_id>', views.game_detail, name='game_detail'),
    path('add_player/<int:team_id>/', views.add_player, name='add_player'),
    path('create_team/', views.create_team, name='create_team'), # make a new team, doesn't automatically add player to it
    path('open_teams/', views.open_teams, name='open_teams'), # shows a list of open teams; click button to join
    path('leave_team/<int:team_id>/', views.leave_team, name='leave_team'), # remove player from team; no HTML
    path('game/<int:game_id>/chat/', views.game_chat, name='game_chat'),

    path('next_round/<int:game_id>/', views.next_round, name='next_round'),
    
]