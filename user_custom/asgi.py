"""
ASGI config for user_custom project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import sys
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import re_path
from django.core.asgi import get_asgi_application
from . import consumers
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_custom.settings')

# is only used for updating the timer
# will NOT be used for the canvas or the chat
websocket_urlpatterns = [
    re_path(r"ws/game/(?P<game_id>\d+)/$", consumers.GameConsumer.as_asgi()),
]

application =  ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
