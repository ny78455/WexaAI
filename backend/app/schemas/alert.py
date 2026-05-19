import uuid
from datetime import datetime
from pydantic import BaseModel
from app.db.models.alert import AlertStatus, AlertSeverity


class AlertCondition(BaseModel):
    metric: str           # e.g. "error_rate", "event_count"
    operator: str         # ">", "<", ">=", "<="
    threshold: float
    window_minutes: int   # evaluation window


class NotificationChannel(BaseModel):
    type: str             # "email", "webhook", "in_app"
    config: dict          # {"email": "..."} or {"url": "..."}


class AlertRuleCreate(BaseModel):
    name: str
    description: str | None = None
    condition: AlertCondition
    notification_channels: list[NotificationChannel] = []
    severity: AlertSeverity = AlertSeverity.MEDIUM


class AlertRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    condition: AlertCondition | None = None
    notification_channels: list[NotificationChannel] | None = None
    severity: AlertSeverity | None = None
    status: AlertStatus | None = None
    muted_until: datetime | None = None


class AlertRuleOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    condition: dict
    notification_channels: list
    status: AlertStatus
    severity: AlertSeverity
    muted_until: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertHistoryOut(BaseModel):
    id: uuid.UUID
    rule_id: uuid.UUID
    triggered_at: datetime
    resolved_at: datetime | None
    triggered_value: float | None
    message: str | None
    notification_sent: bool

    model_config = {"from_attributes": True}
