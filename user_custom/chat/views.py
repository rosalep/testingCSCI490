import socket
import threading
import json
from django.shortcuts import render
from django.http import JsonResponse

from .custom_server import broadcast

def chat_page(request):
    return render(request, 'chat/chat.html')

def new_message(request):
    return JsonResponse({'updates': []}) # No data is stored in the django views anymore.

def send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        if data['type'] == 'message':
            broadcast(data['message'], None) #None is used as the sender.
        elif data['type'] == 'draw':
            broadcast(json.dumps(data['data']), None) #None is used as the sender.
        return JsonResponse({'status': 'ok'})
    else:
        return JsonResponse({'status': 'error'})
