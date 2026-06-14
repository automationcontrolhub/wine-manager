"""
WebSocket consumer — aggiornamenti real-time magazzino/ordini.
Il client può iscriversi a gruppi specifici (es. magazzino, ordini)
e ricevere notifiche push quando i dati cambiano lato backend.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WineryConsumer(AsyncWebsocketConsumer):
    """Consumer generico per il canale notifiche winery."""

    async def connect(self):
        self.group_name = "winery_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send(text_data=json.dumps({"type": "connected", "message": "WebSocket connesso"}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Ping/pong di keepalive dal client."""
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except (json.JSONDecodeError, KeyError):
            pass

    # ── Handler messaggi di gruppo (inviati da views/signals Django) ──────

    async def magazzino_update(self, event):
        """Notifica aggiornamento magazzino."""
        await self.send(text_data=json.dumps({
            "type": "magazzino_update",
            "payload": event.get("payload", {}),
        }))

    async def ordine_update(self, event):
        """Notifica aggiornamento ordine."""
        await self.send(text_data=json.dumps({
            "type": "ordine_update",
            "payload": event.get("payload", {}),
        }))
