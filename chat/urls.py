from django.urls import path
from . import views

urlpatterns = [
    path('game/<int:game_id>/chat/', views.game_chat, name='game_chat'),
]