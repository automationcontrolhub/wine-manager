from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/winery/$", consumers.WineryConsumer.as_asgi()),
]
