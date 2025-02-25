from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # WebSocket route for chat functionality
    re_path(r'ws/chat/(?P<appointment_id>\d+)/$', consumers.ChatConsumer.as_asgi()),

    # WebSocket route for notifications
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
]