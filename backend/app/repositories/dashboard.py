import uuid
import secrets
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.dashboard import Dashboard, Widget


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, dashboard_id: uuid.UUID, org_id: uuid.UUID) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(Dashboard.id == dashboard_id, Dashboard.organization_id == org_id, Dashboard.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def get_by_share_token(self, token: str) -> Dashboard | None:
        result = await self.db.execute(
            select(Dashboard)
            .options(selectinload(Dashboard.widgets))
            .where(Dashboard.share_token == token, Dashboard.is_public == True, Dashboard.is_deleted == False)
        )
        return result.scalar_one_or_none()

    async def list_org_dashboards(self, org_id: uuid.UUID) -> list[Dashboard]:
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.organization_id == org_id, Dashboard.is_deleted == False)
            .order_by(Dashboard.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, org_id: uuid.UUID, user_id: uuid.UUID, **kwargs) -> Dashboard:
        dash = Dashboard(organization_id=org_id, created_by=user_id, **kwargs)
        self.db.add(dash)
        await self.db.flush()
        await self.db.refresh(dash)
        return dash

    async def update(self, dashboard_id: uuid.UUID, **kwargs) -> None:
        await self.db.execute(update(Dashboard).where(Dashboard.id == dashboard_id).values(**kwargs))

    async def delete(self, dashboard_id: uuid.UUID) -> None:
        await self.db.execute(update(Dashboard).where(Dashboard.id == dashboard_id).values(is_deleted=True))

    async def generate_share_token(self, dashboard_id: uuid.UUID) -> str:
        token = secrets.token_urlsafe(24)
        await self.db.execute(
            update(Dashboard).where(Dashboard.id == dashboard_id).values(
                share_token=token, is_public=True
            )
        )
        return token


class WidgetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, widget_id: uuid.UUID) -> Widget | None:
        result = await self.db.execute(select(Widget).where(Widget.id == widget_id))
        return result.scalar_one_or_none()

    async def create(self, dashboard_id: uuid.UUID, **kwargs) -> Widget:
        widget = Widget(dashboard_id=dashboard_id, **kwargs)
        self.db.add(widget)
        await self.db.flush()
        await self.db.refresh(widget)
        return widget

    async def update(self, widget_id: uuid.UUID, **kwargs) -> None:
        await self.db.execute(update(Widget).where(Widget.id == widget_id).values(**kwargs))

    async def delete(self, widget_id: uuid.UUID) -> None:
        await self.db.execute(update(Widget).where(Widget.id == widget_id).values(is_deleted=True))
        # Actually delete (widgets use cascade delete)
        from sqlalchemy import delete
        await self.db.execute(delete(Widget).where(Widget.id == widget_id))
