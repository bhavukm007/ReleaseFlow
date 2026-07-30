from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.services.realtime import realtime

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_updates(websocket: WebSocket, token: str) -> None:
    try:
        user_id = decode_token(token, "access")
    except Exception:
        await websocket.close(code=4401)
        return
    await realtime.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime.disconnect(user_id, websocket)
