"""WebSocket router for real-time event streaming and alert push."""
import json
import asyncio
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.core.security import decode_token

router = APIRouter(tags=["WebSocket"])

# Simple in-memory connection manager
class ConnectionManager:
    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}  # org_id -> set of sockets

    async def connect(self, websocket: WebSocket, org_id: str):
        await websocket.accept()
        self.connections.setdefault(org_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, org_id: str):
        if org_id in self.connections:
            self.connections[org_id].discard(websocket)

    async def broadcast_to_org(self, org_id: str, message: dict):
        sockets = self.connections.get(org_id, set()).copy()
        dead = set()
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.connections[org_id].discard(ws)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_live_events(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Live event stream — authenticated via query param token."""
    try:
        payload = decode_token(token)
        org_id = payload.get("org_id")
        if not org_id:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, org_id)
    try:
        while True:
            # Keep alive ping
            data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
            await websocket.send_json({"type": "pong"})
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        manager.disconnect(websocket, org_id)


@router.websocket("/ws/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Real-time alert notifications."""
    try:
        payload = decode_token(token)
        org_id = payload.get("org_id")
        if not org_id:
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, f"alerts:{org_id}")
    try:
        while True:
            await asyncio.wait_for(websocket.receive_text(), timeout=30)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        manager.disconnect(websocket, f"alerts:{org_id}")
