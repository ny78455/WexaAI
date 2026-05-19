import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.event import Event, APIKey


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_bulk(self, events: list[dict]) -> int:
        objs = [Event(**e) for e in events]
        self.db.add_all(objs)
        await self.db.flush()
        return len(objs)

    async def get_event_count(self, org_id: uuid.UUID, event_name: str | None, start: datetime, end: datetime) -> int:
        stmt = select(func.count(Event.id)).where(
            and_(
                Event.organization_id == org_id,
                Event.timestamp >= start,
                Event.timestamp <= end,
            )
        )
        if event_name:
            stmt = stmt.where(Event.event_name == event_name)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_recent_events(self, org_id: uuid.UUID, limit: int = 100) -> list[Event]:
        result = await self.db.execute(
            select(Event)
            .where(Event.organization_id == org_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_time_series(self, org_id: uuid.UUID, event_name: str | None, start: datetime, end: datetime, interval: str = "1 hour"):
        """Returns time-bucketed counts."""
        stmt = """
            SELECT date_trunc(:interval, timestamp) as bucket, COUNT(*) as count
            FROM events
            WHERE organization_id = :org_id
            AND timestamp BETWEEN :start AND :end
            {event_filter}
            GROUP BY bucket
            ORDER BY bucket
        """.format(event_filter="AND event_name = :event_name" if event_name else "")

        params = {"interval": interval, "org_id": str(org_id), "start": start, "end": end}
        if event_name:
            params["event_name"] = event_name

        from sqlalchemy import text
        result = await self.db.execute(text(stmt), params)
        return [{"bucket": row.bucket.isoformat(), "count": row.count} for row in result]


class APIKeyRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_hash(self, key_hash: str) -> APIKey | None:
        result = await self.db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
        return result.scalar_one_or_none()

    async def get_org_keys(self, org_id: uuid.UUID) -> list[APIKey]:
        result = await self.db.execute(
            select(APIKey).where(APIKey.organization_id == org_id).order_by(APIKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, org_id: uuid.UUID, name: str, key_hash: str, key_prefix: str) -> APIKey:
        key = APIKey(organization_id=org_id, name=name, key_hash=key_hash, key_prefix=key_prefix)
        self.db.add(key)
        await self.db.flush()
        await self.db.refresh(key)
        return key

    async def revoke(self, key_id: uuid.UUID) -> None:
        await self.db.execute(
            update(APIKey).where(APIKey.id == key_id).values(
                is_active=False, revoked_at=datetime.now(timezone.utc)
            )
        )

    async def update_last_used(self, key_id: uuid.UUID) -> None:
        await self.db.execute(
            update(APIKey).where(APIKey.id == key_id).values(last_used_at=datetime.now(timezone.utc))
        )
