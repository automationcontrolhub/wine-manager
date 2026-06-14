"""
ASGI config — Django Channels con routing HTTP + WebSocket.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import winery.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    # Richieste HTTP standard → gestite da Django
    "http": get_asgi_application(),

    # Connessioni WebSocket → instradati ai consumer Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            winery.routing.websocket_urlpatterns
        )
    ),
})
