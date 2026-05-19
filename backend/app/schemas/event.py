import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_validator


# ── Event ─────────────────────────────────────────────────────────────────────

class EventIn(BaseModel):
    event_name: str
    user_id: str | None = None
    session_id: str | None = None
    properties: dict[str, Any] = {}
    timestamp: datetime | None = None

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("event_name must be between 1 and 255 characters")
        return v.strip()


class EventBatchIn(BaseModel):
    events: list[EventIn]

    @field_validator("events")
    @classmethod
    def validate_batch(cls, v: list[EventIn]) -> list[EventIn]:
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 events")
        if len(v) == 0:
            raise ValueError("Batch must contain at least one event")
        return v


class EventOut(BaseModel):
    id: uuid.UUID
    event_name: str
    user_id: str | None
    properties: dict
    timestamp: datetime
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── API Key ───────────────────────────────────────────────────────────────────

class APIKeyCreate(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or len(v) > 255:
            raise ValueError("API key name must be between 1 and 255 characters")
        return v.strip()


class APIKeyOut(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyOut):
    """Returned only at creation time — includes the raw key."""
    raw_key: str


# ── Ingestion Response ────────────────────────────────────────────────────────

class IngestionResponse(BaseModel):
    accepted: int
    message: str
