import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import CurrentUser, require_min_role
from app.db.models.user import UserRole
from app.repositories.dashboard import DashboardRepository, WidgetRepository
from app.repositories.event import EventRepository
from app.schemas.dashboard import (
    DashboardCreate, DashboardUpdate, DashboardOut, DashboardListItem,
    WidgetCreate, WidgetUpdate, WidgetOut,
)
from app.core.exceptions import NotFoundError, AuthorizationError

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.post("/", response_model=DashboardOut, status_code=201)
async def create_dashboard(
    data: DashboardCreate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dash = await repo.create(current_user.organization_id, current_user.id, **data.model_dump())
    return DashboardOut.model_validate(dash)


@router.get("/", response_model=list[DashboardListItem])
async def list_dashboards(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    repo = DashboardRepository(db)
    dashes = await repo.list_org_dashboards(current_user.organization_id)
    return [DashboardListItem(
        **{k: v for k, v in DashboardOut.model_validate(d).model_dump().items() if k != "widgets"},
        widget_count=len(d.widgets) if hasattr(d, "widgets") else 0
    ) for d in dashes]


@router.get("/shared/{share_token}", response_model=DashboardOut)
async def get_shared_dashboard(share_token: str, db: AsyncSession = Depends(get_db)):
    repo = DashboardRepository(db)
    dash = await repo.get_by_share_token(share_token)
    if not dash:
        raise NotFoundError("Dashboard not found or not public")
    return DashboardOut.model_validate(dash)


@router.get("/{dashboard_id}", response_model=DashboardOut)
async def get_dashboard(dashboard_id: uuid.UUID, current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    repo = DashboardRepository(db)
    dash = await repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    return DashboardOut.model_validate(dash)


@router.patch("/{dashboard_id}", response_model=DashboardOut)
async def update_dashboard(
    dashboard_id: uuid.UUID,
    data: DashboardUpdate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dash = await repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    await repo.update(dashboard_id, **{k: v for k, v in data.model_dump().items() if v is not None})
    updated = await repo.get_by_id(dashboard_id, current_user.organization_id)
    return DashboardOut.model_validate(updated)


@router.post("/{dashboard_id}/share", response_model=dict)
async def generate_share_link(
    dashboard_id: uuid.UUID,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dash = await repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    token = await repo.generate_share_token(dashboard_id)
    return {"share_token": token, "share_url": f"/dashboards/shared/{token}"}


@router.delete("/{dashboard_id}", status_code=204)
async def delete_dashboard(
    dashboard_id: uuid.UUID,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    repo = DashboardRepository(db)
    dash = await repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    await repo.delete(dashboard_id)


# ── Widget sub-routes ─────────────────────────────────────────────────────────

@router.post("/{dashboard_id}/widgets", response_model=WidgetOut, status_code=201)
async def add_widget(
    dashboard_id: uuid.UUID,
    data: WidgetCreate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    d_repo = DashboardRepository(db)
    dash = await d_repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    w_repo = WidgetRepository(db)
    widget = await w_repo.create(
        dashboard_id=dashboard_id,
        title=data.title,
        type=data.type,
        query_config=data.query_config,
        position=data.position.model_dump(),
        time_range=data.time_range,
    )
    return WidgetOut.model_validate(widget)


@router.patch("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetOut)
async def update_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    data: WidgetUpdate,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    d_repo = DashboardRepository(db)
    dash = await d_repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    w_repo = WidgetRepository(db)
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if "position" in updates and hasattr(updates["position"], "model_dump"):
        updates["position"] = updates["position"].model_dump()
    await w_repo.update(widget_id, **updates)
    widget = await w_repo.get_by_id(widget_id)
    return WidgetOut.model_validate(widget)


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=204)
async def delete_widget(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user = Depends(require_min_role(UserRole.ANALYST)),
    db: AsyncSession = Depends(get_db),
):
    d_repo = DashboardRepository(db)
    dash = await d_repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    w_repo = WidgetRepository(db)
    await w_repo.delete(widget_id)


@router.get("/{dashboard_id}/widgets/{widget_id}/data")
async def get_widget_data(
    dashboard_id: uuid.UUID,
    widget_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Execute the widget's saved query and return chart-ready data."""
    d_repo = DashboardRepository(db)
    dash = await d_repo.get_by_id(dashboard_id, current_user.organization_id)
    if not dash:
        raise NotFoundError("Dashboard not found")
    w_repo = WidgetRepository(db)
    widget = await w_repo.get_by_id(widget_id)
    if not widget:
        raise NotFoundError("Widget not found")

    event_repo = EventRepository(db)
    from datetime import datetime, timedelta, timezone
    time_range_map = {"1h": 1/24, "24h": 1, "7d": 7, "30d": 30}
    days = time_range_map.get(widget.time_range, 7)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    qc = widget.query_config if isinstance(widget.query_config, dict) else {}
    event_name = qc.get("event_name")

    series = await event_repo.get_time_series(current_user.organization_id, event_name, start, end)
    return {"widget_id": str(widget_id), "type": widget.type, "data": series, "time_range": widget.time_range}
