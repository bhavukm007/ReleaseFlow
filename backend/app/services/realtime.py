from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self.connections: dict[UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[user_id].add(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        self.connections[user_id].discard(websocket)

    async def publish(self, user_ids: set[UUID], event: dict) -> None:
        dead: list[tuple[UUID, WebSocket]] = []
        for user_id in user_ids:
            for connection in tuple(self.connections[user_id]):
                try:
                    await connection.send_json(event)
                except Exception:
                    dead.append((user_id, connection))
        for user_id, connection in dead:
            self.disconnect(user_id, connection)


realtime = RealtimeManager()
