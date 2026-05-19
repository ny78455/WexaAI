from fastapi import APIRouter
from app.api.v1 import auth, events, dashboards, alerts, ws

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(events.router)
api_router.include_router(events.api_keys_router)
api_router.include_router(dashboards.router)
api_router.include_router(alerts.router)
api_router.include_router(ws.router)
