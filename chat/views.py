from django.shortcuts import render

def game_chat(request, game_id):
    return render(request, 'chat/game_chat.html', {'game_id': game_id})