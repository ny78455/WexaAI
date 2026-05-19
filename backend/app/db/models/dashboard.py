import uuid
from enum import Enum as PyEnum
from sqlalchemy import String, Boolean, ForeignKey, Enum, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin
from app.db.models.user import Organization


class WidgetType(str, PyEnum):
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    KPI_CARD = "kpi_card"
    TABLE = "table"


class Dashboard(Base, TimestampMixin):
    __tablename__ = "dashboards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    refresh_interval: Mapped[int | None] = mapped_column(Integer, nullable=True)  # seconds: 30, 60, 300
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="dashboards")
    widgets: Mapped[list["Widget"]] = relationship("Widget", back_populates="dashboard", cascade="all, delete-orphan")


class Widget(Base, TimestampMixin):
    __tablename__ = "widgets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dashboard_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dashboards.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[WidgetType] = mapped_column(Enum(WidgetType), nullable=False)
    query_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    position: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)  # {x, y, w, h}
    time_range: Mapped[str] = mapped_column(String(50), default="7d")  # 1h, 24h, 7d, 30d

    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="widgets")
