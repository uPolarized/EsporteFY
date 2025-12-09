# social/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # MUDAMOS DE <username> PARA <room_name> (que será o ID numérico da conversa)
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r"ws/feed/$", consumers.FeedConsumer.as_asgi()),
]