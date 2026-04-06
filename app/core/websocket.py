from typing import Dict
from fastapi import WebSocket
import json


class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket

    def disconnect(self, user_id: str):
        self.connections.pop(user_id, None)

    async def send_to_user(self, user_id: str, data: dict):
        ws = self.connections.get(str(user_id))
        if ws:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                self.disconnect(str(user_id))

    async def broadcast(self, data: dict):
        disconnected = []
        for user_id, ws in self.connections.items():
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                disconnected.append(user_id)
        for user_id in disconnected:
            self.disconnect(user_id)


ws_manager = WebSocketManager()
