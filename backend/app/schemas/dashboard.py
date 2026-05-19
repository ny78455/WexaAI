import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.dashboard import WidgetType


# ── Widget ────────────────────────────────────────────────────────────────────

class WidgetPosition(BaseModel):
    x: int = 0
    y: int = 0
    w: int = 6
    h: int = 4


class WidgetCreate(BaseModel):
    title: str
    type: WidgetType
    query_config: dict
    position: WidgetPosition = WidgetPosition()
    time_range: str = "7d"


class WidgetUpdate(BaseModel):
    title: str | None = None
    query_config: dict | None = None
    position: WidgetPosition | None = None
    time_range: str | None = None


class WidgetOut(BaseModel):
    id: uuid.UUID
    dashboard_id: uuid.UUID
    title: str
    type: WidgetType
    query_config: dict
    position: dict
    time_range: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardCreate(BaseModel):
    name: str
    description: str | None = None
    refresh_interval: int | None = None  # 30, 60, 300 seconds


class DashboardUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
    refresh_interval: int | None = None


class DashboardOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_public: bool
    share_token: str | None
    refresh_interval: int | None
    created_at: datetime
    widgets: list[WidgetOut] = []

    model_config = {"from_attributes": True}


class DashboardListItem(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_public: bool
    refresh_interval: int | None
    widget_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
